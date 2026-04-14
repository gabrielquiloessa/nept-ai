#!/usr/bin/env python3

import dns.resolver
import threading
from queue import Queue, Empty
from pathlib import Path
from urllib.parse import urlparse
import json
import colorama
from colorama import Fore

colorama.init()

MAX_THREADS = 50

class Dnsinfo:
    def __init__(self, target=None, list=None, output=None, json=False, **kwargs):
        self.target = target.strip() if target else None
        self.list = list
        self.output = output
        self.json_output = json

        self.queue = Queue()
        self.lock = threading.Lock()

        self.targets = self._load_targets()
        self.results = []

    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None, "description": "Single target"},
            "LIST": {"required": False, "value": None, "description": "File with targets"},
            "OUTPUT": {"required": False, "value": None, "description": "Save output"},
            "JSON": {"required": False, "value": False, "description": "JSON output"},
        }

    def _normalize_target(self, target):
        parsed = urlparse(target)
        if parsed.netloc:
            return parsed.netloc.split(':')[0]
        return target.split(':')[0]

    def _load_targets(self):
        targets = set()
        if self.list:
            path = Path(self.list)
            if not path.exists():
                print(f"[!] List file not found: {self.list}")
                return []
            with path.open() as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        targets.add(self._normalize_target(line))
        elif self.target:
            targets.add(self._normalize_target(self.target))
        else:
            print("[!] Target or list required")
            return []
        return list(targets)

    def _resolve_raw(self, resolver, target, record_type):
        try:
            answers = resolver.resolve(target, record_type)
            return answers
        except dns.resolver.NXDOMAIN:
            return None
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers, Exception):
            return []

    def _parse_record(self, record_type, data):
        if not data:
            return []
        results = []
        for r in data:
            try:
                if record_type in ["A", "AAAA"]:
                    results.append(str(r))
                elif record_type == "MX":
                    host = str(r.exchange).rstrip('.')
                    results.append(f"{r.preference} {host}")
                elif record_type in ["NS", "CNAME"]:
                    results.append(str(r.target).rstrip('.'))
                elif record_type == "TXT":
                    txt_content = b"".join(r.strings).decode('utf-8', errors='ignore')
                    if txt_content:
                        results.append(txt_content)
                elif record_type == "SOA":
                    mname = str(r.mname).rstrip('.')
                    rname = str(r.rname).rstrip('.')
                    results.append(f"{mname} {rname} {r.serial} {r.refresh} {r.retry} {r.expire} {r.minimum}")
                else:
                    results.append(str(r))
            except Exception:
                continue
        return results

    def _worker(self):
        # Correção para o ambiente Termux (Android)
        try:
            resolver = dns.resolver.Resolver()
        except dns.resolver.NoResolverConfiguration:
            # Se não encontrar /etc/resolv.conf, usa DNS público manualmente
            resolver = dns.resolver.Resolver(configure=False)
            resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
        
        resolver.timeout = 4
        resolver.lifetime = 5

        while True:
            try:
                target = self.queue.get(timeout=1)
            except Empty:
                break

            if not target or ".." in target or target.startswith("#"):
                self.queue.task_done()
                continue

            result = {
                "type": "dns",
                "target": target,
                "host": target,
                "status": "unknown",
                "port": None, 
                "url": f"http://{target}",
                "server": None,
                "A": [],
                "AAAA": [],
                "MX": [],
                "NS": [],
                "TXT": [],
                "CNAME": [],
                "SOA": [],
                "tech": []
            }

            try:
                raw_a = self._resolve_raw(resolver, target, "A")
                if raw_a is None:
                    result["status"] = "NXDOMAIN"
                else:
                    result["status"] = "resolved"
                    result["A"] = self._parse_record("A", raw_a)
                    result["AAAA"] = self._parse_record("AAAA", self._resolve_raw(resolver, target, "AAAA"))
                    result["MX"] = self._parse_record("MX", self._resolve_raw(resolver, target, "MX"))
                    result["NS"] = self._parse_record("NS", self._resolve_raw(resolver, target, "NS"))
                    result["TXT"] = self._parse_record("TXT", self._resolve_raw(resolver, target, "TXT"))
                    result["CNAME"] = self._parse_record("CNAME", self._resolve_raw(resolver, target, "CNAME"))
                    result["SOA"] = self._parse_record("SOA", self._resolve_raw(resolver, target, "SOA"))

                    # Lógica de detecção de tecnologias
                    if result["NS"] or result["SOA"] or result["MX"]:
                        result["tech"].append("DNS")
                    if result["A"]:
                        result["tech"].append("IP")
                    if result["NS"]:
                        result["tech"].append("NS")
                        result["server"] = result["NS"][0]
                    if result["MX"]:
                        result["tech"].append("MX")
                        mx_str = " ".join(result["MX"]).lower()
                        if "google" in mx_str or "gmail" in mx_str:
                            result["tech"].append("Google Workspace")
                        elif "outlook" in mx_str or "office365" in mx_str:
                            result["tech"].append("Office 365")
                    if result["TXT"]:
                        txt_combined = " ".join(result["TXT"]).lower()
                        if "v=spf1" in txt_combined:
                            result["tech"].append("SPF")
                        if "dmarc" in txt_combined:
                            result["tech"].append("DMARC")
                        if "google-site-verification" in txt_combined:
                            result["tech"].append("Google Verified")

            except Exception:
                result["status"] = "error"

            with self.lock:
                self.results.append(result)

            self.queue.task_done()

    def _print_human(self):
        for r in self.results:
            print(f"\n{r['target']}")
            if r["status"] == "NXDOMAIN":
                print(f"  {Fore.RED}[!] Domain does not exist{Fore.RESET}")
                continue
            if r["status"] == "error":
                print(f"  {Fore.YELLOW}[!] Resolution error{Fore.RESET}")
                continue

            fields = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
            for key in fields:
                if r[key]:
                    print(f"  [{key}]")
                    for item in r[key]:
                        print(f"    - {item}")

            if r["tech"]:
                print(f"  {Fore.CYAN}[Tech]{Fore.RESET} {', '.join(r['tech'])}")

    def run(self):
        if not self.targets:
            print("[!] No valid targets")
            return

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
            print(f"[+] Saved to {self.output}")
        elif self.json_output:
            print(json.dumps(self.results, indent=4))
        else:
            print("[+] DNS scan finished")
            self._print_human()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        scanner = Dnsinfo(target=sys.argv[1])
        scanner.run()
