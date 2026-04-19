#!/usr/bin/env python3

import argparse
from .engine import Engine


class CLI:

    def __init__(self):
        self.engine = Engine()

    def run(self):
        self.engine.load_modules()

        parser = argparse.ArgumentParser(
            description="Nept Recon Framework"
        )

        parser.add_argument("module", nargs="?", help="Module")

        parser.add_argument("-t", "--target")
        parser.add_argument("-l", "--list")
        parser.add_argument("-w", "--wordlist")

        parser.add_argument("--mobile", action="store_true")

        parser.add_argument("--fast", action="store_true")
        parser.add_argument("--threads", type=int, default=None)

        parser.add_argument(
            "-f", "--format",
            choices=["json", "txt", "csv"],
            default="txt"
        )

        parser.add_argument("-o", "--output")

        parser.add_argument("--ai", choices=["add", "list"])

        parser.add_argument("--console", action="store_true")

        args = parser.parse_args()

        # ===== CONSOLE =====
        if args.console:
            self.engine.console()
            return

        # ===== AI MODE =====
        if args.ai:
            if args.ai == "list":
                self.engine.ai.list_rules()
            elif args.ai == "add":
                self.engine.ai.add_rule()
            return

        # ===== HELP MODULE =====
        if not args.module:
            print("[!] Use module or --console\n")
            print("""
Modules

dir             Directory brute force
dnsinfo         DNS Information
subdomain       Subdomain brute force
portscan        Ports scanner
httpinfo        HTTP information
recon           Run all modules
            """)
            return

        self.engine.use_module(args.module)

        # ===== FORMAT =====
        self.engine.set_option("format", args.format)

        # FORMAT -> JSON FLAG GLOBAL
        if args.format == "json": 
            self.engine.set_option("json", True)
        
        # ===== MOBILE =====
        if args.mobile:
            self.engine.set_option("mobile", True)

        # ===== FAST MODE =====
        if args.fast:
            self.engine.set_option("fast", True)

            if args.threads is None:
                self.engine.set_option("threads", 100)

            self.engine.set_option("timeout", 2)

        # ===== THREADS MANUAL =====
        if args.threads is not None:
            self.engine.set_option("threads", args.threads)

        # ===== OTHERS PARAMS =====
        for k, v in vars(args).items():
            if v is not None and k not in [
                "module", "console", "fast", "ai", "format", "threads"
            ]:
                self.engine.set_option(k, v)

        self.engine.run_module()
