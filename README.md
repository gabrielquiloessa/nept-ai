# Nept Recon Framework 🚀

[![License: MIT](https://shields.io)](https://opensource.org)
[![Python](https://shields.io)](https://python.org)
[![Platform](https://shields.io)](https://github.com)

Nept is a lightweight, AI-powered reconnaissance framework designed for modern penetration testing with a mobile-first philosophy. It enables fast, modular, and automated intelligence gathering across domains, networks, and web applications, powered by an intelligent risk-analysis engine.

---

## ⚡ Key Features

* **Mobile-First Design:** Optimized natively for Termux (Android) and standard Linux environments.
* **AI-Powered Assistant:** Intelligent rule matching and dynamic attack-plan generation based on scan results.
* **Fast Execution:** Multi-threaded architecture for high-speed directory, subdomain, and port discovery.
* **Modular Pipeline:** Highly extensible structure allowing effortless addition of custom security modules.
* **Automation Ready:** Native support for structured JSON outputs to pipe data into other Red Team tools.

---

## 🛠️ Installation & Setup

### Termux (Recommended)
Ensure your environment is updated, clone the repository, and execute the automated installer:

```bash
pkg update && pkg upgrade -y
pkg install git python -y
git clone https://github.com/gabrielquiloessa/nept-ai.git
cd nept-ai
chmod +x install.sh
./install.sh
```

---

## 🎯 Usage Guide

Once installed via `install.sh`, the framework can be invoked globally using the `nept` command.

### 1. CLI Mode (Direct Scans)
```bash
nept recon -t example.com      # Run all available modules
nept portscan -t example.com   # Scan for open ports
nept subdomain -t example.com  # Brute-force subdomains
nept dir -t example.com        # Directory brute-force
nept dnsinfo -t example.com    # Gather DNS configurations
nept httpinfo -t example.com   # Analyze HTTP headers
```

### 2. Interactive Console Mode
Launch the custom interactive shell to chain modules and manage the AI engine dynamically:
```bash
nept --console
```
**Console Commands:**
* `modules` - List all active scanning modules.
* `use <module>` - Select a specific module for configuration.
* `set <key> <value>` - Define target variables dynamically.
* `run` - Execute the active payload.
* `ai list` / `ai add` - Interfere directly with the intelligent rule set.

---

## 🧠 AI Engine & Threat Intel

Nept features an integrated engine that maps vulnerabilities using custom severity scoring. You can inject live rules directly into the AI database:

```bash
nept --ai add
```
*Input Example:*
```text
Name: Sensitive File Exposure
Severity (1-10): 9
Priority (1-10): 10
Match type: url_contains
Match value: .env, .git, backup.tar, db.sql, config.php
Actions: Download file, Extract secrets, Check for credentials, Search API keys
```

### Intelligence Report Sample Output:
```text
[Nept Assistant] INTELLIGENCE REPORT
------------------------------------
Risk Score: 42
[+] Open Port (3) -> example.com (risk=12)

ATTACK PLAN:
1. Try default credentials on discovered interfaces.
2. Fuzz directories for hidden backups or configuration files.
3. Check for SSL/TLS misconfigurations.
```

---

## 🏗️ Architecture Blueprint

```text
core/
 ├── engine.py       # Core execution and threading orchestrator
 ├── ai.py           # Intelligent analysis and decision engine
 └── rules.json      # Dynamic threat signature database

modules/
 ├── dnsinfo.py      # DNS Enumeration module
 ├── subdomain.py    # Subdomain Discovery module
 ├── portscan.py     # Port Scanner module
 ├── httpinfo.py     # HTTP Header Analyzer module
 ├── dir.py          # Directory Fuzzer module
 └── recon.py        # Full Suite Orchestrator
```

---

## 🗺️ Development Roadmap

- [ ] Web-based Dashboard Integration
- [ ] AI Automated Reinforcement Learning
- [ ] Distributed Remote Scanning Infrastructure
- [ ] Specialized Bug Bounty Passive Mode
- [ ] Dynamic Plugin Engine for Third-Party Scripts

---

## ⚠️ Disclaimer

This tool is strictly developed for educational purposes and authorized penetration testing. The author assumes no liability for misuse, unauthorized infrastructure damage, or illegal actions performed with this software.

---

## 👤 Author

* **Gabriel Canga Quiloessa** 
* Cyber Security Researcher | Pentester | Red Team Operator
* *Focus: Offensive Security Automation & Intelligent Exploitation*

---

## 🤝 Support & Contributions

If you find this project useful, consider supporting its development:
1. ⭐ **Star** the repository to increase visibility.
2. 🍴 **Fork** the project to experiment with custom features.
3. 💡 Open an **Issue** or **Pull Request** to contribute to the code.

---

## 🔄 Dynamic OTA Updates (Over-The-Air)

Nept features an integrated update engine allowing users to dynamically pull the latest threat intelligence signatures (rules) or module enhancements directly from the upstream repository without cloning the framework again or breaking custom settings.

### 1. Update AI Risk Signatures
Fetch the latest community threat intelligence and risk matching patterns into your local signature database:
```bash
nept --update rules
```

### 2. Update Core Penetration Testing Modules
If a script gets corrupted, deleted by accident, or a new version is pushed to GitHub, repair/update all module scripts simultaneously with a single command:
```bash
nept --update modules
```
_This handles the seamless downloading, wiping, and upgrading of: `dir`, `dnsinfo`, `httpinfo`, `portscan`, `recon`, and `subdomain` binaries._

