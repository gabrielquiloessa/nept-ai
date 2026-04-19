#!/usr/bin/env python3

import requests
import threading
from queue import Queue, Empty
from pathlib import Path
import json
import colorama
from colorama import Fore

colorama.init()

class Httpinfo:
    def __init__(self, target=None, list=None, output=None, json=False, **kwargs):
        self.target = target.strip() if target else None
        self.list = list
        self.output = output
        self.json_output = json
        self.threads_count = int(kwargs.get("threads", 20))
        self.timeout = float(kwargs.get("timeout", 3))
        self.targets = self._load_targets()
        self.queue = Queue()
        self.lock = threading.Lock()
        self.results = []

    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None},
            "LIST": {"required": False, "value": None},
            "OUTPUT": {"required": False, "value": None},
            "JSON": {"required": False, "value": False},
            "THREADS": {"required": False, "value": 20},
            "TIMEOUT": {"required": False, "value": 3},
        }

    def _load_targets(self):
        targets = set()
        if self.list:
            path = Path(self.list)
            if path.exists():
                with path.open() as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            targets.add(line)
        elif self.target:
            targets.add(self.target)
        return list(targets)

    def _worker(self):
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Android 10; Linux; Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        
        while True:
            try:
                target = self.queue.get(timeout=1)
            except Empty:
                break

            found = False
            for proto in ["https://", "http://"]:
                url = target if "://" in target else f"{proto}{target}"
                try:
                    r = session.get(url, timeout=self.timeout, allow_redirects=True)
                    headers = r.headers
                    server = headers.get("Server", "Unknown")
                    powered_by = headers.get("X-Powered-By", "None")
                    cookies = headers.get("Set-Cookie", "")

                    result = {
                        "target": target,
                        "status": "up",
                        "status_code": r.status_code,
                        "server": server,
                        "x_powered_by": powered_by,
                        "cookie_flags": {
                            "HttpOnly": "HttpOnly" in cookies,
                            "Secure": "Secure" in cookies
                        },
                        "url": r.url,
                        "tech": ["Web", server]
                    }
                    if powered_by != "None": result["tech"].append(powered_by)
                    
                    with self.lock:
                        self.results.append(result)
                    found = True
                    break 
                except requests.exceptions.RequestException:
                    continue
            
            if not found:
                with self.lock:
                    self.results.append({"target": target, "status": "down"})
            self.queue.task_done()

    def _print_human(self):
        for r in self.results:
            print(f"\n{r['target']}")
            if r.get("status") == "down":
                print(f"  {Fore.RED}[!] Status: DOWN{Fore.RESET}")
                continue
            
            print(f"  [Status]: {r['status_code']}")
            print(f"  [Server]: {r['server']}")
            print(f"  [URL]: {r['url']}")
            print(f"  [Cookies]: HttpOnly={r['cookie_flags']['HttpOnly']}, Secure={r['cookie_flags']['Secure']}")
            if r['tech']:
                print(f"  {Fore.CYAN}[Tech]{Fore.RESET} {', '.join(r['tech'])}")

    def run(self):
        if not self.targets: return
        for t in self.targets: self.queue.put(t)
        threads = [threading.Thread(target=self._worker, daemon=True) for _ in range(min(self.threads_count, len(self.targets)))]
        for t in threads: t.start()
        for t in threads: t.join()

        if not self.json_output:
            self._print_human()

        if self.output:
            with open(self.output, "w") as f:
                json.dump(self.results, f, indent=4)
