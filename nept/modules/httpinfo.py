#!/usr/bin/env python3

import requests
import threading
from queue import Queue, Empty
from pathlib import Path
from urllib.parse import urlparse
import json

MAX_THREADS = 50
TIMEOUT = 4

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Andorid 10) Chrome/120 Safari/537.36"
}


class Httpinfo:
    def __init__(self, target=None, list=None, output=None, json=False, **kwargs):
        self.target = target.strip() if target else None
        self.list = list
        self.output = output
        self.json_output = json

        self.targets = self._load_targets()

        self.queue = Queue()
        self.lock = threading.Lock()
        self.results = []

    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None, "description": "Single target"},
            "LIST": {"required": False, "value": None, "description": "File with targets"},
            "OUTPUT": {"required": False, "value": None, "description": "Save output to file"},
            "JSON": {"required": False, "value": False, "description": "Return JSON output"},
        }

    def _load_targets(self):
        targets = set()

        if self.list:
            path = Path(self.list)
            if not path.exists():
                print("[!] List file not found")
                return []

            with path.open() as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        targets.add(line)

        elif self.target:
            targets.add(self.target)

        else:
            print("[!] Target or list required")
            return []

        return list(targets)

    def _generate_urls(self, target):
        parsed = urlparse(target)
        ports = [80, 443, 8080, 8443]

        if parsed.scheme:
            return [target]

        urls = []
        for port in ports:
            if port == 443:
                urls.append(f"https://{target}")
            elif port == 80:
                urls.append(f"http://{target}")
            else:
                urls.append(f"http://{target}:{port}")
                urls.append(f"https://{target}:{port}")
        return urls

    def _fingerprint(self, r):
        tech = []
        headers = r.headers
        body = r.text.lower()

        server = headers.get("Server", "")
        powered = headers.get("X-Powered-By", "")

        if "apache" in server.lower():
            tech.append("Apache")
        if "nginx" in server.lower():
            tech.append("Nginx")
        if "iis" in server.lower():
            tech.append("IIS")

        if "php" in powered.lower():
            tech.append("PHP")
        if "express" in powered.lower():
            tech.append("Node.js")

        if "wp-content" in body:
            tech.append("WordPress")
        if "laravel" in body:
            tech.append("Laravel")
        if "django" in body:
            tech.append("Django")
        if "react" in body:
            tech.append("React")
        if "vue" in body:
            tech.append("Vue")

        return list(set(tech)) if tech else []

    def _worker(self):
        session = requests.Session()

        while True:
            try:
                target = self.queue.get(timeout=1)
            except Empty:
                break

            if not target or ".." in target or target.startswith("#"):
                self.queue.task_done()
                continue

            result = {
                "target": target,
                "status": "down",
                "url": None,
                "status_code": None,
                "server": None,
                "content_type": None,
                "technologies": []
            }

            urls = self._generate_urls(target)

            for url in urls:
                try:
                    r = session.get(
                        url,
                        headers=HEADERS,
                        timeout=TIMEOUT,
                        allow_redirects=True
                    )

                    result.update({
                        "type": "http",
                        "target": target,
                        "status": "up",
                        "url": url,
                        "port": urlparse(url).port or (443 if url.startswith("https") else 80),
                        "status": r.status_code,
                        "server": r.headers.get("Server"),
                        "content_type": r.headers.get("Content-Type"),
                        "technologies": self._fingerprint(r)
                    })
                    break

                except requests.exceptions.RequestException:
                    continue

            with self.lock:
                self.results.append(result)

            self.queue.task_done()

    def _print_human(self):
        for r in self.results:
            print(f"\n[+] {r['target']}")
            print(f" URL: {r['url']}")
            print(f" Status: {r['status_code']}")
            print(f" Server: {r['server']}")
            print(f" Content-Type: {r['content_type']}")
            print(f" Tech: {', '.join(r['technologies']) if r['technologies'] else 'Unknown'}")

    def run(self):
        if not self.targets:
            print("[!] No valid targets")
            return

        if not self.json_output:
            print(f"[+] Targets: {len(self.targets)}")
            print(f"[+] Threads: {MAX_THREADS}\n")

        for t in self.targets:
            self.queue.put(t)

        threads = []
        for _ in range(min(MAX_THREADS, len(self.targets))):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            threads.append(t)

        self.queue.join()

        if self.output:
            with open(self.output, "w") as f:
                json.dump(self.results, f, indent=4)
            if not self.json_output:
                print(f"[+] Saved to: {self.output}")

        elif self.json_output:
            print(json.dumps(self.results, indent=4))

        else:
            print("[+] Scan finished\n")
            self._print_human()
