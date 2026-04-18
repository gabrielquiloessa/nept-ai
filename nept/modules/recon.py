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

    def _score_target(self, target):
        score = 0

        high = ["admin", "login", "panel", "api", "dev", "test", "staging"]
        medium = ["mail", "app", "dashboard"]

        for w in high:
            if w in target:
                score += 50

        for w in medium:
            if w in target:
                score += 20

        if target.startswith("www"):
            score += 10

        return score

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
            threads=10 if self.mobile else self.kwargs.get("threads", 50),
            timeout=5
        )
        sub.targets = dns_targets
        sub.run()

        all_targets = list(set([r["target"] for r in sub.results] + dns_targets))

        scored = sorted(all_targets, key=lambda x: self._score_target(x), reverse=True)

        if self.mobile:
            selected_targets = scored[:3]
        else:
            selected_targets = scored[:8]

        if not json_output:
            print(f"[+] Total targets: {len(all_targets)} | Using: {len(selected_targets)}")

        # ===== FAST MODE =====
        if self.fast:
            self.results = dns.results + sub.results
            if not json_output:
                print("\n[+] Recon completed (fast mode)")
            return

        # ===== PORTSCAN =====
        port = Portscan(
            target=None,
            json=json_output,
            output=output,
            threads=20 if self.mobile else self.kwargs.get("threads", 100),
            timeout=2 if self.mobile else 1
        )
        port.targets = selected_targets
        port.run()

        # ===== HTTP =====
        http = Httpinfo(
            target=None,
            json=json_output,
            output=output
        )
        http.targets = selected_targets
        http.run()

        alive = []
        for r in http.results:
            if r.get("url") or r.get("status") is not None:
                alive.append(r["target"])

        # fallback caso http falhe
        if not alive:
            alive = selected_targets

        if self.mobile:
            alive = alive[:2]

        # ===== DIR =====
        dir_results = []
        targets_to_scan = alive[:2] if self.mobile else alive[:5]

        for host in targets_to_scan:
            dirscan = Dir(
                target=host,
                json=json_output,
                output=output
            )
            dirscan.run()
            dir_results.extend(dirscan.results)

        self.results = dns.results + sub.results + port.results + http.results + dir_results

        if json_output:
            import json
            print(json.dumps(self.results, indent=4))
        else:
            print("\n[+] Recon completed")
