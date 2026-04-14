#!/usr/bin/env python3

from nept.modules.dnsinfo import Dnsinfo
from nept.modules.subdomain import Subdomain
from nept.modules.portscan import Portscan
from nept.modules.httpinfo import Httpinfo
from nept.modules.dir import Dir


class Recon:

    def __init__(self, target=None, list=None, fast=False, mobile=False, **kwargs):
        self.target = target
        self.list = list
        self.fast = fast
        self.mobile = mobile
        self.kwargs = kwargs
        self.results = []

    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None},
            "LIST": {"required": False, "value": None},   
            "FAST": {"required": False, "value": False},
            "MOBILE": {"required": False, "value": False},
            "JSON": {"required": False, "value": False},
        }

    def _load_targets(self):
        targets = []

        if self.target:
            targets.append(self.target)

        if self.list:
            try:
                with open(self.list, "r") as f:
                    targets += [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"[!] Failed loading list: {e}")

        return list(set(targets))

    def run(self):
        json_output = self.kwargs.get("json", False)
        output = self.kwargs.get("output")

        if not json_output:
            print("[i] Starting recon...\n")

        targets = self._load_targets()

        if not targets:
            print("[!] Target or list required")
            print("[!] No valid targets")
            return

        # ===== DNS =====
        dns = Dnsinfo(
            target=None,
            json=json_output,
            output=output
        )
        dns.targets = targets
        dns.run()

        dns_targets = [r["target"] for r in dns.results if r.get("A")]

        # ===== SUBDOMAIN =====
        sub = Subdomain(
            target=None,
            json=json_output,
            output=output,
            threads=self.kwargs.get("threads", 50),
            timeout=self.kwargs.get("timeout", 5)
        )
        sub.targets = dns_targets
        sub.run()

        all_targets = list(set([r["target"] for r in sub.results] + dns_targets))

        # ===== PORTSCAN =====
        port = Portscan(
            target=None,
            json=json_output,
            output=output,
            threads=self.kwargs.get("threads", 100),
            timeout=self.kwargs.get("timeout", 1)
        )
        port.targets = all_targets
        port.run()

        if not self.fast:
            # ===== HTTP =====
            http = Httpinfo(
                target=None,
                json=json_output,
                output=output
            )
            http.targets = all_targets
            http.run()

            alive = [r["target"] for r in http.results if r.get("status")]

            if self.mobile:
                alive = alive[:3]

            # ===== DIR =====
            dirscan = Dir(
                targets=alive,
                json=json_output,
                output=output
            )
            dirscan.run()

            self.results = dns.results + sub.results + port.results + http.results + dirscan.results

        else:
            self.results = dns.results + sub.results + port.results

        if json_output:
            import json
            print(json.dumps(self.results, indent=4))
        else:
            print("\n[+] Recon completed")
