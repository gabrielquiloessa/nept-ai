#!/usr/bin/env python3

from pathlib import Path
import requests
import threading
from queue import Queue, Empty
import json

BASE_DIR = Path(__file__).resolve().parent.parent
MAX_THREADS = 30


class Subdomain:
    def __init__(self, target=None, list=None, wordlist=None, status=None, **kwargs):
        try:
            self.target = target.strip() if target else None
            self.list = list
            self.targets = []

            # -------------------------
            # EXTRA PARAMS
            # -------------------------
            self.output = kwargs.get("output") or kwargs.get("o")
            self.json_output = kwargs.get("json", False)
            self.threads = int(kwargs.get("threads", MAX_THREADS))
            self.timeout = int(kwargs.get("timeout", 5))

            self.results = []

            # -------------------------
            # WORDLIST
            # -------------------------
            default_wordlist = BASE_DIR / "wordlists" / "sub.txt"

            if wordlist:
                self.wordlist = Path(wordlist)
            else:
                self.wordlist = default_wordlist
                print(f"[i] Using default wordlist: {self.wordlist}")

            if not self.wordlist.exists():
                print(f"[!] Wordlist not found: {self.wordlist}")
                self.wordlist = None

            # -------------------------
            # STATUS FILTER
            # -------------------------
            if status is not None:
                try:
                    self.status = int(status)
                except:
                    print("[!] Invalid status")
                    self.status = None
            else:
                self.status = None

            self.queue = Queue()
            self.lock = threading.Lock()

            self.targets = self._load_targets()

        except Exception as e:
            print(f"[!] Error in __init__: {e}")
            self.wordlist = None
            self.status = None

    # -------------------------
    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None},
            "LIST": {"required": False, "value": None},
            "WORDLIST": {"required": False, "value": None},
            "STATUS": {"required": False, "value": None},
            "THREADS": {"required": False, "value": 30},
            "TIMEOUT": {"required": False, "value": 5},
            "OUTPUT": {"required": False, "value": None},
            "JSON": {"required": False, "value": False},
        }

    # -------------------------
    def _load_targets(self):
        targets = set()

        if self.list:
            try:
                path = Path(self.list)

                if not path.exists():
                    print("[!] List file not found")
                    return []

                with path.open() as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            targets.add(line)

            except Exception as e:
                print(f"[!] Error reading list: {e}")
                return []

        elif self.target:
            targets.add(self.target)

        else:
            print("[!] Target or list required")
            return []

        return list(targets)

    # -------------------------
    def _worker(self):
        session = requests.Session()

        while True:
            try:
                target, sub = self.queue.get_nowait()
            except Empty:
                break

            host = f"{sub}.{target}"
            url = f"http://{host}"

            if ".." in host or host.startswith("#"):
                self.queue.task_done()
                continue

            try:
                r = session.get(url, timeout=self.timeout, allow_redirects=False)

                if self.status is not None:
                    valid = r.status_code == self.status
                else:
                    valid = r.status_code in [200, 301, 302, 403, 500]

                if valid:
                    result = {
                        "type": "subdomain",
                        "target": host,
                        "host": host,
                        "url": url,
                        "port": 80,
                        "status": r.status_code
                    }

                    with self.lock:
                        if not self.json_output:
                            print(f"[{r.status_code}] {host}")
                        self.results.append(result)

            except requests.exceptions.RequestException:
                pass

            self.queue.task_done()

    # -------------------------
    def _save_output(self):
        if not self.output:
            return

        try:
            path = Path(self.output)

            if self.json_output:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.results, f, indent=4)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for r in self.results:
                        f.write(f"{r['host']} -> {r['status']}\n")

            print(f"\n[+] Saved output: {path}")

        except Exception as e:
            print(f"[!] Error saving output: {e}")

    # -------------------------
    def run(self):
        try:
            if not self.targets:
                print("[!] No valid targets")
                return

            if not self.wordlist:
                print("[!] No valid wordlist")
                return

            print(f"[+] Targets: {len(self.targets)}")
            print(f"[+] Threads: {self.threads}")

            subs = []
            with open(self.wordlist, 'rt', encoding="utf-8", errors="ignore") as f:
                for line in f:
                    sub = line.strip()
                    if sub and " " not in sub:
                        subs.append(sub)

            print(f"[+] Subdomains loaded: {len(subs)}\n")

            all_results = []

            for target in self.targets:
                print("\n" + "=" * 50)
                print(f"[i] Testing: {target}")
                print("=" * 50)

                self.results = []
                self.queue = Queue()

                for sub in subs:
                    self.queue.put((target, sub))

                threads = []
                total_threads = min(self.threads, self.queue.qsize())

                for _ in range(total_threads):
                    t = threading.Thread(target=self._worker, daemon=True)
                    t.start()
                    threads.append(t)
                
                try:
                    self.queue.join()
                except KeyboardInterrupt:
                    print("\n[!] Interrupted bu user")

                print(f"[+] Found on {target}: {len(self.results)}")
                all_results.extend(self.results)

            self.results = all_results

            print(f"\n[+] Enumeration finished")
            print(f"[+] Total Found: {len(self.results)}")

            self._save_output()

        except Exception as e:
            print(f"[!] Error in run(): {e}")
