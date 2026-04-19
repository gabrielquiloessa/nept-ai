#!/usr/bin/env python3
import socket
import threading
from queue import Queue
from pathlib import Path
import json

COMMON_PORTS = [20, 21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 2121, 3306, 3389, 8080, 8443, 5900, 6379, 27017, 9000, 9001]
MAX_THREADS = 80

class Portscan:
    def __init__(self, target=None, list=None, **kwargs):
        self.target = target
        self.list = list
        self.results = []
        self.queue = Queue()
        self.lock = threading.Lock()
        
        self.output = kwargs.get("output") or kwargs.get("o")
        self.json_output = kwargs.get("json", False)
        self.threads = int(kwargs.get("threads", MAX_THREADS))
        self.timeout = float(kwargs.get("timeout", 1))
        
        port = kwargs.get("port")
        ports = kwargs.get("ports")
        self.ports = self._parse_ports(ports or port) if (ports or port) else COMMON_PORTS
        
        self.targets = self._load_targets()

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

    def _parse_ports(self, value):
        ports = set()
        value = str(value).lower().strip()
        if value == "all": return list(range(1, 65536))
        for part in value.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    s, e = map(int, part.split("-"))
                    for p in range(min(s, e), max(s, e) + 1):
                        if 1 <= p <= 65535: ports.add(p)
                except: continue
            else:
                try:
                    p = int(part)
                    if 1 <= p <= 65535: ports.add(p)
                except: continue
        return sorted(ports)

    def _worker(self):
        while not self.queue.empty():
            target, ip, port = self.queue.get()
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.timeout)
                    if s.connect_ex((ip, port)) == 0:
                        try: service = socket.getservbyport(port)
                        except: service = "unknown"
                        result = {"type": "port", "target": f"{target}:{port}", "ip": ip, "port": port, "service": service}
                        with self.lock:
                            if not self.json_output: print(f"[OPEN] {target}:{port} ({service})")
                            self.results.append(result)
            except: pass
            self.queue.task_done()

    def run(self):
        if not self.targets or not self.ports:
            print("[!] Target or Port missing")
            return
            
        for target in self.targets:
            try:
                ip = socket.gethostbyname(target)
                for port in self.ports: self.queue.put((target, ip, port))
            except: continue
        
        threads = []
        for _ in range(min(self.threads, self.queue.qsize())):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            threads.append(t)
        for t in threads: t.join()
        
        print(f"\n[+] Scan finished. Open ports: {len(self.results)}")
