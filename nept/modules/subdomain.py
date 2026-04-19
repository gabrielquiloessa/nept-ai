#!/usr/bin/env python3

from pathlib import Path
import requests
import threading
from queue import Queue, Empty
import json
import socket
import time

BASE_DIR = Path(__file__).resolve().parent.parent
MAX_THREADS = 30


class Subdomain:
    def __init__(self, target=None, list=None, wordlist=None, status=None, **kwargs):
        try:
            self.target = target.strip() if target else None
            self.list = list

            self.output = kwargs.get("output") or kwargs.get("o")
            self.json_output = kwargs.get("json", False)
            self.threads = int(kwargs.get("threads", MAX_THREADS))
            self.timeout = int(kwargs.get("timeout", 5))
            self.mobile = kwargs.get("mobile", False)

            # MOBILE FIX REAL
            if self.mobile:
                self.threads = min(self.threads, 15)
                self.timeout = max(self.timeout, 7)
                self.delay = 0.05  # anti-freeze
            else:
                self.delay = 0

            self.results = []
            self.seen = set()

            default_wordlist = BASE_DIR / "wordlists" / "sub.txt"
            self.wordlist = Path(wordlist) if wordlist else default_wordlist

            self.queue = Queue()
            self.lock = threading.Lock()

            self.targets = self._load_targets()

        except Exception:
            self.wordlist = None

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

    def _log(self, msg):
        if not self.json_output:
            print(msg)

    def _load_targets(self):
        targets = set()

        if self.list:
            path = Path(self.list)
            if path.exists():
                with path.open() as f:
                    for line in f:
                        if line.strip():
                            targets.add(line.strip())

        elif self.target:
            targets.add(self.target)

        return list(targets)

    # -------------------------
    # PASSIVE ENUM (CRT.SH)
    # -------------------------
    def _crt(self, domain):
        subs = set()
        try:
            url = f"https://crt.sh/?q=%25.{domain}&output=json"
            r = requests.get(url, timeout=10)

            if r.status_code != 200:
                return subs

            data = r.json()

            for entry in data:
                for s in entry.get("name_value", "").split("\n"):
                    s = s.strip().lower().replace("*.", "")
                    if domain in s:
                        subs.add(s)

        except Exception:
            pass

        return subs

    def _resolve(self, host):
        try:
            socket.gethostbyname(host)
            return True
        except:
            return False

    def _worker(self):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) Chrome/120 Safari/537.36"
        })

        while True:
            try:
                target, sub = self.queue.get_nowait()
            except Empty:
                break

            try:
                host = f"{sub}.{target}" if not sub.endswith(target) else sub

                if host in self.seen:
                    self.queue.task_done()
                    continue

                self.seen.add(host)

                resolved = self._resolve(host)
                found = False

                for scheme in ["https", "http"]:
                    try:
                        r = session.get(
                            f"{scheme}://{host}",
                            timeout=self.timeout,
                            allow_redirects=False
                        )

                        if r.status_code in [200, 301, 302, 403, 401]:
                            result = {
                                "type": "subdomain",
                                "target": host,
                                "url": f"{scheme}://{host}",
                                "status": r.status_code
                            }

                            with self.lock:
                                if not self.json_output:
                                    print(f"[{r.status_code}] {host}")
                                self.results.append(result)

                            found = True
                            break

                    except:
                        continue

                if not found and resolved:
                    with self.lock:
                        if not self.json_output:
                            print(f"[DNS] {host}")
                        self.results.append({
                            "type": "subdomain",
                            "target": host,
                            "status": "resolved"
                        })

                if self.delay:
                    time.sleep(self.delay)

            except:
                pass

            self.queue.task_done()

    def run(self):
        if not self.targets:
            self._log("[!] No targets")
            return

        subs = set()

        # PASSIVE
        for t in self.targets:
            self._log(f"[i] crt.sh: {t}")
            subs.update(self._crt(t))

        # WORDLIST
        if self.wordlist and self.wordlist.exists():
            with open(self.wordlist, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        subs.add(s)

        self._log(f"[+] Total candidates: {len(subs)}")

        for target in self.targets:
            self.queue = Queue()

            for s in subs:
                self.queue.put((target, s))

            threads = []
            for _ in range(min(self.threads, self.queue.qsize())):
                t = threading.Thread(target=self._worker, daemon=True)
                t.start()
                threads.append(t)

            self.queue.join()

        self._log(f"\n[+] Found: {len(self.results)}")
