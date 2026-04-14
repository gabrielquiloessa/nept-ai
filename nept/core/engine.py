#!/usr/bin/env python3

import importlib
import pkgutil
import json
from .ai import NeptAI
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

# =============================
# READLINE FIX (MOBILE SAFE)
# =============================
try:
    import readline

    try:
        readline.parse_and_bind("tab: complete")
    except:
        pass

except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None


class Engine:

    def __init__(self):
        self.modules = {}
        self.current_module = None
        self.options = {}
        self.ai = NeptAI()

    def load_modules(self):
        import nept.modules as pkg

        for _, name, ispkg in pkgutil.iter_modules(pkg.__path__):
            if ispkg or name.startswith("_"):
                continue

            try:
                module = importlib.import_module(f"nept.modules.{name}")
                self.modules[name] = module
            except Exception as e:
                print(f"[!] Failed loading module {name}: {e}")

    def _get_class(self, module):
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and obj.__module__ == module.__name__:
                return obj

    def use_module(self, name):
        if name not in self.modules:
            print(f"{Fore.RED}[!] Module not found{Style.RESET_ALL}")
            return

        self.current_module = name
        cls = self._get_class(self.modules[name])
        self.options = cls.options() if hasattr(cls, "options") else {}

        print(f"{Fore.GREEN}[+] Using: {name}{Style.RESET_ALL}")

    def set_option(self, k, v):
        k = k.upper()
        if k in self.options:
            self.options[k]["value"] = v

    def run_module(self):
        if not self.current_module:
            print(f"{Fore.RED}[!] No module selected{Style.RESET_ALL}")
            return

        cls = self._get_class(self.modules[self.current_module])

        kwargs = {
            k.lower(): v["value"]
            for k, v in self.options.items()
            if v.get("value") is not None
        }

        instance = cls(**kwargs)
        instance.run()

        results = getattr(instance, "results", [])

        # JSON OUTPUT GLOBAL
        if kwargs.get("json"):
            print(json.dumps(results, indent=4))
            return

        # AI
        self.ai.run(results)

    # =============================
    # CONSOLE IMPLEMENTATION
    # =============================
    def console(self):
        print(f"\n{Fore.CYAN}Nept Interactive Console{Style.RESET_ALL}\n")

        while True:
            try:
                if self.current_module:
                    prompt = f"{Fore.BLUE}({self.current_module}) nept> {Style.RESET_ALL}"
                else:
                    prompt = f"{Fore.BLUE}nept> {Style.RESET_ALL}"

                cmd = input(prompt).strip()

                if not cmd:
                    continue

                if cmd in ["exit", "quit"]:
                    print(f"{Fore.YELLOW}[i] Exiting...{Style.RESET_ALL}")
                    break

                parts = cmd.split()
                command = parts[0]

                # ===== USE MODULE =====
                if command == "use":
                    if len(parts) < 2:
                        print(f"{Fore.RED}[!] Usage: use <module>{Style.RESET_ALL}")
                        continue
                    self.use_module(parts[1])
                    continue

                # ===== CLEAR =====
                if command == "clear":
                    import os
                    os.system("clear")
                    continue

                # ===== SET OPTION =====
                if command == "set":
                    if len(parts) < 3:
                        print(f"{Fore.RED}[!] Usage: set <option> <value>{Style.RESET_ALL}")
                        continue
                    self.set_option(parts[1], parts[2])
                    print(f"{Fore.GREEN}[+] {parts[1].upper()} => {parts[2]}{Style.RESET_ALL}")
                    continue

                # ===== SHOW OPTIONS =====
                if command == "options":
                    if not self.options:
                        print(f"{Fore.RED}[!] No module selected{Style.RESET_ALL}")
                        continue

                    print(f"\n{Fore.CYAN}Options:{Style.RESET_ALL}\n")
                    for k, v in self.options.items():
                        print(f"{Fore.YELLOW}{k:15}{Style.RESET_ALL} : {v.get('value')} ({v.get('desc', '')})")
                    print()
                    continue

                # ===== RUN =====
                if command == "run":
                    self.run_module()
                    continue

                # ===== LIST MODULES =====
                if command == "modules":
                    print(f"\n{Fore.CYAN}Available modules:{Style.RESET_ALL}\n")
                    for m in self.modules:
                        print(f"{Fore.GREEN} - {m}{Style.RESET_ALL}")
                    print()
                    continue

                # ===== AI =====
                if command == "ai":
                    if len(parts) < 2:
                        print(f"{Fore.RED}[!] Usage: ai <list|add>{Style.RESET_ALL}")
                        continue

                    if parts[1] == "list":
                        self.ai.list_rules()
                    elif parts[1] == "add":
                        self.ai.add_rule()
                    else:
                        print(f"{Fore.RED}[!] Unknown AI command{Style.RESET_ALL}")
                    continue

                # ===== HELP =====
                if command in ["help", "?"]:
                    print(f"""
{Fore.CYAN}Commands:{Style.RESET_ALL}

    modules              List modules
    use <module>         Select module
    options              Show options
    set <k> <v>          Set option
    run                  Execute module
    ai list              List AI rules
    ai add               Add AI rule
    clear                Clear screen
    exit / quit          Exit console
""")
                    continue

                print(f"{Fore.RED}[!] Unknown command (type 'help'){Style.RESET_ALL}")

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[i] Use 'exit' to quit{Style.RESET_ALL}")
