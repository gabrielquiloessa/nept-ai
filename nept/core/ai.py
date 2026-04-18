#!/usr/bin/env python3

import json
from pathlib import Path
from collections import defaultdict
import colorama
from colorama import Fore

colorama.init()


class NeptAI:

    def __init__(self):
        self.rules = []
        self.rules_path = Path(__file__).resolve().parent / "rules.json"
        self._load_rules()

    def _load_rules(self):
        try:
            if not self.rules_path.exists():
                self.rules_path.write_text("[]")

            with open(self.rules_path) as f:
                self.rules = json.load(f)

        except Exception as e:
            print(f"{Fore.RED}[Nept Assistent] Failed loading rules: {e}")

    def _save_rules(self):
        try:
            with open(self.rules_path, "w") as f:
                json.dump(self.rules, f, indent=4)
        except Exception as e:
            print(f"{Fore.RED}[Nept Assistent] Failed saving rules: {e}")

    def list_rules(self):
        if not self.rules:
            print(f"{Fore.YELLOW}[Nept Assistent] No rules loaded\n")
            return

        print(f"\n{Fore.CYAN}[Nept Assistent] Loaded Rules:\n")

        for i, r in enumerate(self.rules, 1):
            print(f"{i}. {r.get('name')}")
            print(f"   severity: {r.get('severity')} | priority: {r.get('priority')}")
            print(f"   match: {r.get('match')}")
            print(f"   actions: {r.get('actions')}\n")

    def add_rule(self):
        try:
            print(f"\n{Fore.CYAN}[Nept Assistent] Add New Rule\n")

            name = input("Name: ").strip()
            severity = int(input("Severity (1-10): "))
            priority = int(input("Priority (1-10): "))

            print("\nMatch types:")
            print(" - port_equals")
            print(" - status_equals")
            print(" - url_contains")
            print(" - server_contains")
            print(" - tech_contains")

            m_type = input("Match type: ").strip()
            m_value = input("Match value (comma separated): ").strip().split(",")

            actions = input("Actions (comma separated): ").strip().split(",")

            rule = {
                "name": name,
                "severity": severity,
                "priority": priority,
                "match": {
                    "type": m_type,
                    "value": [v.strip() if not v.strip().isdigit() else int(v.strip()) for v in m_value]
                },
                "actions": [a.strip() for a in actions if a.strip()]
            }

            self.rules.append(rule)
            self._save_rules()

            print(f"\n{Fore.GREEN}[Nept Assistent] Rule added successfully!\n")

        except Exception as e:
            print(f"{Fore.RED}[Nept Assistent] Failed adding rule: {e}")
            
    def normalize(self, results):
        normalized = []

        for r in results:
            if not isinstance(r, dict):
                continue

            # CORREÇÃO AQUI: O módulo dnsinfo usa "tech", o normalizador procurava "technologies"
            tech_data = r.get("tech") or r.get("technologies") or []

            entry = {
                "type": r.get("type"),
                "target": r.get("target") or r.get("host"),
                "host": r.get("host"),
   
                "A": r.get("A", []),
                "AAAA": r.get("AAAA", []),
                "MX": r.get("MX", []),
                "NS": r.get("NS", []),
                "TXT": r.get("TXT", []),
                "CNAME": r.get("CNAME", []),
                "SOA": r.get("SOA", []),               
   
                "port": r.get("port"),
                "url": r.get("url"),
                "status": r.get("status") or r.get("status_code"),
                "server": r.get("server"),
                "tech": tech_data,
                "extra": r
            }

            normalized.append(entry)

        return normalized

    def match(self, rule, r):
        m = rule.get("match", {})
        t = m.get("type")
        v = m.get("value", [])

        try:
            if t == "port_equals":
                # Garante que estamos comparando inteiros com inteiros
                r_port = r.get("port")
                if r_port is None:
                    return False
                return int(r_port) in [int(x) for x in v]

            if t == "status_equals":
                return str(r.get("status")) in [str(x) for x in v]

            if t == "url_contains":
                return any(str(x).lower() in str(r.get("url", "")).lower() for x in v)

            if t == "server_contains":
                return any(str(x).lower() in str(r.get("server", "")).lower() for x in v)

            if t == "tech_contains":
                r_tech = [str(t_item).lower() for t_item in r.get("tech", [])]
                return any(str(x).lower() in r_tech for x in v)

            if t == "ns_contains":
                return any(any(str(x).lower() in str(ns).lower() for ns in r.get("NS", [])) for x in v)

            if t == "mx_contains":
                return any(any(str(x).lower() in str(mx).lower() for mx in r.get("MX", [])) for x in v)

            if t == "txt_contains":
                return any(any(str(x).lower() in str(txt).lower() for txt in r.get("TXT", [])) for x in v)
        except Exception:
            return False

        return False

    def correlate(self, data):
        findings = []
        score = 0

        for r in data:
            for rule in self.rules:
                if self.match(rule, r):
                    risk = rule["severity"] * rule["priority"]

                    findings.append({
                        "name": rule["name"],
                        "target": r.get("target"),
                        "extra": r,
                        "risk": risk,
                        "actions": rule.get("actions", [])
                    })

                    score += risk

        findings = sorted(findings, key=lambda x: x["risk"], reverse=True)

        return findings, score

    def build_attack_plan(self, findings):
        actions = set()

        for f in findings:
            for a in f["actions"]:
                actions.add(a)

        if not actions:
            return [
                "Expand recon",
                "Try fuzzing",
                "Check misconfigurations"
            ]

        return list(actions)

    def run(self, raw_results):
        data = self.normalize(raw_results)

        findings, score = self.correlate(data)

        if not findings:
            print(f"\n{Fore.YELLOW}[Nept Assistent] No findings, fallback mode\n")

            for a in self.build_attack_plan([]):
                print(f" - {a}")
            return

        print(f"\n{Fore.GREEN}[Nept Assistent] INTELLIGENCE REPORT\n")
        print(f"Risk Score: {score}\n")

        grouped = defaultdict(list)

        for f in findings:
            grouped[f["name"]].append(f)

        for name, items in grouped.items():
            print(f"[+] {name} ({len(items)})")
            for i in items[:3]:
                r = i.get("extra", {})

                display = i.get("target")

                if isinstance(r, dict):
                    if r.get("host"):
                        display = r["host"]
                    elif r.get("url"):
                        display = r["url"]

                print(f"   -> {display} (risk={i['risk']})")
            print()

        print(f"\n{Fore.GREEN}[Nept Assistent] ATTACK PLAN:\n")

        plan = self.build_attack_plan(findings)

        for i, step in enumerate(plan, 1):
            print(f"{i}. {step}")
