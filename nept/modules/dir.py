#!/usr/bin/env python3

import requests
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent.parent


class Dir:
    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None},
            "LIST": {"required": False, "value": None},
            "WORDLIST": {"required": False, "value": None},
            "THREADS": {"required": False, "value": 50},
            "OUTPUT": {"required": False, "value": None},
            "JSON": {"required": False, "value": False},
        }

    def __init__(self, target=None, list=None, wordlist=None, threads=50, output=None, json=False, **kwargs):
        self.target = target
        self.list = list
        self.threads = int(threads)
        self.results = []
        self.lock = threading.Lock()
        self.output = output
        self.json_output = json

        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.threads,
            pool_maxsize=self.threads
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        self.wordlist = Path(wordlist) if wordlist else BASE_DIR / "wordlists" / "dom.txt"

    def _log(self, msg):
        if not self.json_output:
            print(msg, file=sys.stderr)

    def _prepare_targets(self):
        raw_list = [self.target] if self.target else []

        if self.list and Path(self.list).exists():
            with open(self.list, "r", encoding="utf-8", errors="ignore") as f:
                raw_list += [line.strip() for line in f if line.strip()]

        clean_targets = []
        for t in set(raw_list):
            t_clean = t.replace("http://", "").replace("https://", "").strip("/")
            clean_targets.append(f"https://{t_clean}")

        return clean_targets

    def _load_wordlist(self):
        if not self.wordlist.exists():
            return []

        with open(self.wordlist, "r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip() and " " not in line]

    def _scan(self, base_url, path):
        url = f"{base_url}/{path}"

        try:
            r = self.session.get(url, timeout=3, allow_redirects=False, verify=False)

            if r.status_code in [200, 204, 301, 302, 307, 401, 403, 405]:
                with self.lock:
                    self.results.append({"url": url, "status": r.status_code})

                    if not self.json_output:
                        print(f"[{r.status_code}] {url}")

        except:
            pass

    def run(self):
        targets = self._prepare_targets()

        if not targets:
            self._log("[!] Target required")
            return

        words = self._load_wordlist()

        self._log(f"[+] Targets: {len(targets)}")
        self._log(f"[+] Threads: {self.threads}")
        self._log(f"[+] Words: {len(words)}")

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for target in targets:
                self._log(f"[i] Scanning: {target}")
                for word in words:
                    executor.submit(self._scan, target, word)
