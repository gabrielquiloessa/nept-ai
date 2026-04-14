#!/usr/bin/env python3        

import requests
import threading              
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning       

BASE_DIR = Path(__file__).resolve().parent.parent

class Dir:
    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None},
            "LIST": {"required": False, "value": None},
            "WORDLIST": {"required": False, "value": None},
            "THREADS": {"required": False, "value": 50},
        }

    def __init__(self, target=None, list=None, wordlist=None, targets=None, threads=50, **kwargs):
        self.target = target
        self.list = list
        self.targets_raw = targets or []
        self.threads = int(threads)
        self.results = []
        self.lock = threading.Lock()

        # Otimização: Uso de Session para Keep-Alive
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=self.threads, pool_maxsize=self.threads)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        if wordlist:
            self.wordlist = Path(wordlist)
        else:
            self.wordlist = BASE_DIR / "wordlists" / "dom.txt"
            # Removido print excessivo para não poluir o Termux

    def _prepare_targets(self):
        raw_list = []
        if self.target: raw_list.append(self.target)
        if self.list and Path(self.list).exists():
            with open(self.list, "r") as f:
                raw_list += [line.strip() for line in f if line.strip()]
        raw_list += self.targets_raw

        clean_targets = []
        for t in set(raw_list):
            # Detecta o melhor protocolo uma vez só para ganhar tempo
            t_clean = t.replace("http://", "").replace("https://", "").strip("/")
            try:
                # Tenta HTTPS primeiro (mais comum em 2026)
                test = requests.get(f"https://{t_clean}", timeout=3, verify=False)
                clean_targets.append(f"https://{t_clean}")
            except:
                clean_targets.append(f"http://{t_clean}")
        return clean_targets

    def _load_wordlist(self):
        if not self.wordlist.exists(): return []
        with open(self.wordlist, "r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip() and " " not in line]

    def _scan(self, base_url, path):
        url = f"{base_url}/{path}"
        try:
            # Usando a sessão persistente
            r = self.session.get(url, timeout=3, allow_redirects=False, verify=False)

            # Filtro básico de falsos positivos (comum em servidores que dão 200 para tudo)
            if r.status_code in [200, 204, 301, 302, 307, 401, 403, 405]:
                with self.lock:
                    print(f" [{r.status_code}] {url}")
                    self.results.append({"url": url, "status": r.status_code})
        except:
            pass

    def run(self):
        targets = self._prepare_targets()
        words = self._load_wordlist()

        if not targets or not words:
            print("[!] Alvo ou wordlist inválidos.")
            return

        print(f"[+] Nept Dir-Fuzzer | Threads: {self.threads} | Palavras: {len(words)}")

        for target in targets:
            print(f"\n[i] Escaneando: {target}")

            # ThreadPoolExecutor é mais rápido que criar threads manualmente aqui
            try:
                with ThreadPoolExecutor(max_workers=self.threads) as executor:
                    # Envia todas as tarefas para o pool
                    executor.map(lambda w: self._scan(target, w), words)
            except KeyboardInterrupt:
                print("\n[!] Abortando scan atual...")
                break

        print(f"\n[+] Scan de diretórios finalizado. {len(self.results)} encontrados.")
