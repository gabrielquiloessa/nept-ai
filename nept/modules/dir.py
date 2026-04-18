#!/usr/bin/env python3

import requests
import threading
import json
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

    def __init__(self, target=None, list=None, wordlist=None, threads=50, output=None, json_format=False, **kwargs):
        self.target = target
        self.list = list
        self.threads = int(threads)
        self.results = []
        self.lock = threading.Lock()
        self.output = output

        # Ensure JSON flag is correctly set
        self.json = (
            json_format
            or kwargs.get("JSON", False)
            or (output is not None and output.endswith(".json"))
        )

        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=self.threads, pool_maxsize=self.threads)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        self.wordlist = Path(wordlist) if wordlist else BASE_DIR / "wordlists" / "dom.txt"

    def _prepare_targets(self):
        raw_list = [self.target] if self.target else []
        if self.list and Path(self.list).exists():
            with open(self.list, "r") as f:
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
                    if not self.json:
                        print(f" [{r.status_code}] {url}")
                    self.results.append({"url": url, "status": r.status_code})
        except:
            pass

    def _save_output(self):
        if not self.output:
            return

        try:
            with open(self.output, "w", encoding="utf-8") as f:
                if self.json:
                    json.dump(self.results, f, indent=4)
                else:
                    for item in self.results:
                        f.write(f"[{item['status']}] {item['url']}\n")
            print(f"\n[+] Results saved in: {self.output}")
        except Exception as e:
            print(f"\n[!] Error on file save: {e}")

    def run(self):
        targets = self._prepare_targets()
        wordlist = self._load_wordlist()

        if not self.json:
            print(f"[+] Starting scan in {len(targets)} targets...")

        for base_url in targets:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                for path in wordlist:
                    executor.submit(self._scan, base_url, path)

        if self.json:
            print(json.dumps(self.results, indent=4))
        
        self._save_output()
