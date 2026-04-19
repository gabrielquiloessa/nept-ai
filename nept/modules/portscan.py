#!/usr/bin/env python3

import socket
import threading
from queue import Queue
from pathlib import Path
import json
from datetime import datetime

COMMON_PORTS = [
    20,21,22,23,25,53,80,110,139,143,443,
    445,2121,3306,3389,8080,8443,5900,6379,
    27017,9000,9001
]

MAX_THREADS = 80


class Portscan:

    def __init__(self, target=None, list=None, **kwargs):
        self.target = target
        self.list = list
        self.targets = []

        self.ports = []
        self.queue = Queue()
        self.lock = threading.Lock()
        self.results = []

        self.current_target = None  # CONTEXT VISUAL

        self.output = kwargs.get("output") or kwargs.get("o")
        self.json_output = kwargs.get("json", False)
        self.threads = int(kwargs.get("threads", MAX_THREADS))
        self.timeout = float(kwargs.get("timeout", 1))

        port = kwargs.get("port")
        ports = kwargs.get("ports")

        try:
            if ports:
                self.ports = self._parse_ports(ports)
            elif port:
                self.ports = self._parse_ports(port)
            else:
                print("[*] No port specified, using common ports...")
                self.ports = COMMON_PORTS

        except Exception as e:
            print(f"[!] Error parsing ports: {e}")
            self.ports = []

        self.targets = self._load_targets()

    # -------------------------
    # OPTIONS
    # -------------------------
    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None},
            "LIST": {"required": False, "value": None},
            "PORT": {"required": False, "value": None},
            "PORTS": {"required": False, "value": None},
            "THREADS": {"required": False, "value": 80},
            "TIMEOUT": {"required": False, "value": 1},
            "OUTPUT": {"required": False, "value": None},
            "JSON": {"required": False, "value": False},
        }

    # -------------------------
    # LOAD TARGETS
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

                        if not line or line.startswith("#"):
                            continue

                        if line in ["0", ".", "null"]:
                            continue

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
    # PARSE PORTS
    # -------------------------
    def _parse_ports(self, value):
        ports = set()
        value = str(value).lower().strip()

        if value == "all":
            return list(range(1, 65536))

        for part in value.split(","):
            part = part.strip()

            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    for p in range(min(start, end), max(start, end)+1):
                        if 1 <= p <= 65535:
                            ports.add(p)
                except:
                    continue
            else:
                try:
                    p = int(part)
                    if 1 <= p <= 65535:
                        ports.add(p)
                except:
                    continue

        return sorted(ports)

    # -------------------------
    # WORKER
    # -------------------------
    def _worker(self):
        while not self.queue.empty():
            target, ip, port = self.queue.get()

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.timeout)
                    code = s.connect_ex((ip, port))

                    if code == 0:
                        try:
                            service = socket.getservbyport(port)
                        except:
                            service = "unknown"

                        banner = self._grab_banner(ip, port)

                        result = {
                            "type": "port",
                            "target": f"{target}:{port}",
                            "ip": ip,
                            "port": port,
                            "service": service,
                            "banner": banner.strip()
                        }

                        with self.lock:
                            if not self.json_output:
                                print(f"[OPEN] {target}:{port} ({service}) {banner}")
                            self.results.append(result)

            except:
                pass

            self.queue.task_done()

    # -------------------------
    # BANNER GRAB
    # -------------------------
    def _grab_banner(self, ip, port):
        try:
            with socket.socket() as s:
                s.settimeout(self.timeout)
                s.connect((ip, port))
                banner = s.recv(1024).decode(errors="ignore").strip()

                if banner:
                    return f"| {banner[:50]}"
        except:
            pass
        return ""

    # -------------------------
    # SAVE OUTPUT
    # -------------------------
    def _save_output(self):
        if not self.output:
            return  #  sem auto-save

        try:
            path = Path(self.output)

            if self.json_output:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.results, f, indent=4)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for r in self.results:
                        f.write(
                            f"{r['target']}:{r['port']} ({r['service']}) {r['banner']}\n"
                        )

            print(f"\n[+] Saved output: {path}")

        except Exception as e:
            print(f"[!] Error saving output: {e}")
            
    # -------------------------
    # RUN
    # -------------------------
    def run(self):
        try:
            if not self.targets:
                print("[!] No valid targets")
                return

            if not self.ports:
                print("[!] No valid ports")
                return

            if not self.json_output:
                print(f"[+] Targets loaded: {len(self.targets)}")
                print(f"[+] Ports: {len(self.ports)}")
            print(f"[+] Threads: {self.threads}\n")

            for target in self.targets:
            
                self.queue = Queue()

                print("\n" + "=" * 50)
                print(f"[i] Testing: {target}")
                print("=" * 50)

                try:
                    ip = socket.gethostbyname(target)
                except:
                    print(f"[!] Failed to resolve: {target}")
                    continue

                print(f"[+] {target} -> {ip}")

                for port in self.ports:
                    self.queue.put((target, ip, port))

                threads = []
                total_threads = min(self.threads, self.queue.qsize())

                for _ in range(total_threads):
                    t = threading.Thread(target=self._worker, daemon=True)
                    t.start()
                    threads.append(t)

                self.queue.join()

            print(f"\n[+] Scan finished")
            print(f"[+] Open ports: {len(self.results)}")

            self._save_output()

        except Exception as e:
            print(f"[!] Error: {e}")
