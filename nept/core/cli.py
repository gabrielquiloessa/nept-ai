#!/usr/bin/env python3

import argparse
from .engine import Engine
from .update import Update 

class CLI:

    def __init__(self):
        self.engine = Engine()

    def run(self):
        self.engine.load_modules()

        parser = argparse.ArgumentParser(
            description="Nept Recon Framework: An AI-powered offensive reconnaissance and automation tool."
        )

        # ===== Core Arguments =====
        parser.add_argument(
            "module", 
            nargs="?", 
            help="The scanning module to execute (e.g., portscan, dir, subdomain, recon)."
        )

        parser.add_argument(
            "-t", "--target", 
            help="Target specification. Accepts a domain name, full URL, or IP address."
        )
        
        parser.add_argument(
            "-l", "--list", 
            help="Path to a file containing a list of multiple targets for batch scanning."
        )
        
        parser.add_argument(
            "-w", "--wordlist", 
            help="Path to a custom wordlist file for directory or subdomain brute-forcing."
        )

        # ===== Performance & Optimization Flags =====
        parser.add_argument(
            "--mobile", 
            action="store_true", 
            help="Optimize scanning logic and memory usage specifically for Termux/mobile environments."
        )

        parser.add_argument(
            "--fast", 
            action="store_true", 
            help="Enable high-speed mode (automatically sets threads to 100 and timeout to 2s)."
        )
        
        parser.add_argument(
            "--threads", 
            type=int, 
            default=None, 
            help="Manually specify the number of concurrent threads to spawn (overrides dynamic limits)."
        )

        # ===== Output Formatting =====
        parser.add_argument(
            "-f", "--format",
            choices=["json", "txt", "csv"],
            default="txt",
            help="Set the output report format type. Default is 'txt'."
        )

        parser.add_argument(
            "-o", "--output", 
            help="Path to save the scan report output file."
        )

        # ===== Specialized Execution Modes =====
        parser.add_argument(
            "--ai", 
            choices=["add", "list"], 
            help="Interact with the Threat Intel AI engine: 'list' active intelligence rules, or 'add' a custom signature."
        )

        parser.add_argument(
            "--update", 
            choices=["rules", "modules"], 
            help="Perform an Over-The-Air (OTA) update: 'rules' updates threat signatures; 'modules' upgrades all attack scripts."
        )
                
        parser.add_argument(
            "--console", 
            action="store_true", 
            help="Launch Neptune's custom interactive console shell environment."
        )

        args = parser.parse_args()

        # ===== CONSOLE =====
        if args.console:
            self.engine.console()
            return

        # ======UPDATES========
        if args.update:
            updater = Update()
            if args.update == "rules":
                updater.update_rules()
            elif args.update == "modules":
                updater.update_dir()
                updater.update_dnsinfo()
                updater.update_httpinfo()
                updater.update_portscan()
                updater.update_recon()
                updater.update_subdomain()
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
