#!/usr/bin/env python3

import requests
import os

class Update:
    def __init__(self, **kwargs):
        self.upgrade = kwargs.get("upgrade")

        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _safe_download(self, url, file_path, description):
        try:
            # Remove the old file if exixts and create a new
            if os.path.exists(file_path):
                os.remove(file_path)
            
            response = requests.get(url)
            response.raise_for_status()

            # Save the file in path specify
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"{description} updated successfully!")
        except Exception as e:
            print(f"Error updating {description}: {e}")

    def update_rules(self):
        url = "https://raw.githubusercontent.com/gabrielquiloessa/nept-ai/refs/heads/main/nept/core/rules.json"
        # Save on rules.json
        path = os.path.join(self.BASE_DIR, "core", "rules.json")
        self._safe_download(url, path, "rules")

    def update_module(self, module_name):
        url = f"https://raw.githubusercontent.com/gabrielquiloessa/nept-ai/refs/heads/main/nept/modules/{module_name}.py"
        # Salva on nept/modules/{module_name}.py
        path = os.path.join(self.BASE_DIR, "modules", f"{module_name}.py")
        self._safe_download(url, path, f"module '{module_name}'")

    # All modules
    def update_dir(self): self.update_module("dir")
    def update_dnsinfo(self): self.update_module("dnsinfo")
    def update_httpinfo(self): self.update_module("httpinfo")
    def update_portscan(self): self.update_module("portscan")
    def update_recon(self): self.update_module("recon")
    def update_subdomain(self): self.update_module("subdomain")
