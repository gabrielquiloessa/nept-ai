#!/usr/bin/env python3
import importlib
import pkgutil
import json
import sys
from .ai import NeptAI
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

class Engine:
    def __init__(self):
        self.modules = {}
        self.current_module = None
        self.options = {}
        self.ai = NeptAI()
        self.json_mode = False

    def _log(self, msg):
        if not self.json_mode:
            print(msg, file=sys.stderr)

    def load_modules(self):
        import nept.modules as pkg
        for _, name, ispkg in pkgutil.iter_modules(pkg.__path__):
            if ispkg or name.startswith("_"):
                continue
            try:
                module = importlib.import_module(f"nept.modules.{name}")
                self.modules[name] = module
            except Exception as e:
                self._log(f"[!] Failed loading module {name}: {e}")

    def _get_class(self, module):
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and obj.__module__ == module.__name__:
                return obj

    def use_module(self, name):
        if name not in self.modules:
            self._log(f"{Fore.RED}[!] Module not found{Style.RESET_ALL}")
            return
        self.current_module = name
        cls = self._get_class(self.modules[name])
        self.options = cls.options() if hasattr(cls, "options") else {}
        self._log(f"{Fore.GREEN}[+] Using: {name}{Style.RESET_ALL}")

    def set_option(self, k, v):
        k = k.upper()
        if k in self.options:
            self.options[k]["value"] = v

    def run_module(self):
        if not self.current_module:
            self._log(f"{Fore.RED}[!] No module selected{Style.RESET_ALL}")
            return
        cls = self._get_class(self.modules[self.current_module])
        kwargs = {
            k.lower(): v["value"] for k, v in self.options.items() if v.get("value") is not None
        }
        self.json_mode = kwargs.get("json", False)
        instance = cls(**kwargs)
        instance.run()
        results = getattr(instance, "results", [])
        
        self.ai.run(results)
        
    def console(self):
        print("Nept Interactive Console")
        print("""
███╗░░██╗███████╗██████╗░████████╗
████╗░██║██╔════╝██╔══██╗╚══██╔══╝
██╔██╗██║█████╗░░██████╔╝░░░██║░░░
██║╚████║██╔══╝░░██╔═══╝░░░░██║░░░
██║░╚███║███████╗██║░░░░░░░░██║░░░
╚═╝░░╚══╝╚══════╝╚═╝░░░░░░░░╚═╝░░░
""")

        print("Type 'help' for commands.\n")

        while True:
            try:
                if not self.modules:
                    cmd = input(f"{Fore.BLUE}nept>{Style.RESET_ALL} ").strip()

                if self.modules:
                    cmd = input(f"{Fore.GREEN}({self.current_module}){Style.RESET_ALL} {Fore.BLUE}nept>{Style.RESET_ALL} ").strip()
                if not cmd:
                    continue

                if cmd in ("exit", "quit"):
                    break
                    
                if cmd == "clear":
                    import os
                    os.system("clear")
                    
                if cmd == "ai list":
                    self.ai.list_rules()
                    
                if cmd == "ai add":
                    self.ai.add_rule()

                if cmd in ("help", "?"):
                    print("""
Commands

help
modules
use <module>
set <option> <value>
run
show options
clear
exit
""")
                    continue

                if cmd == "modules":
                    for m in self.modules:
                        print("-", m)
                    continue

                if cmd.startswith("use "):
                    module = cmd.split(maxsplit=1)[1]
                    self.use_module(module)
                    continue

                if cmd in ("show options", "options"):
                    for k, v in self.options.items():
                        print(f"{k} = {v.get('value')}")
                    continue

                if cmd.startswith("set "):
                    parts = cmd.split(maxsplit=2)

                    if len(parts) < 3:
                        print("Usage: set OPTION VALUE")
                        continue

                    self.set_option(parts[1], parts[2])
                    continue

                if cmd == "run":
                    self.run_module()
                    continue

                print("Unknown command")

            except KeyboardInterrupt:
                print()
                break

            except EOFError:
                break
                
