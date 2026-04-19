# Nept Recon Framework

**Nept** is a lightweight, fast, and user-friendly reconnaissance framework for mobile pentesting, featuring an AI assistant to automate and assist with security tasks.

---

## Features
- Fast reconnaissance pipeline for domains, subdomains, directories, and ports
- AI-powered assistant for pentesting guidance
- Modular structure for easy extension
- Supports JSON output for automation and integration
- Multi-threaded for faster scanning

---

## Installation

Clone the repository and run the installer:

```bash
# Termux (Recommended)

pkg update && pkg upgrade -y
pkg install git python -y

git clone https://github.com/gabrielquiloessa/nept-ai.git
cd nept-ai

chmod +x install.sh
./install.sh

# Run (console mode / Interative mode)
nept --console

# Run (cli mode)
nept portscan -t example.com
nept subdomain -t example.com
nept dir -t example.com
nept dnsinfo -t example.com
nept httpinfo -t example.com
nept recon -t example.com

```


Modules

```
dir            Directory brute force
dnsinfo        Dns Information
subdomain      Subdomain brute force
protscan       Ports scaner
httpinfo       HTTP information
recon          Test all modules
```

CLI Usage

```
nept recon -t example.com
nept dir -t example.com -w path/to/wordlist.txt
```

Interactive Console

```
nept --console

# Commands
modules
use <module>
set <key> <value>
run

ai list
ai add
```

AI Commands

```
# List all rules
nept --ai list

# Add new rule
nept --ai add

Name: Sensitive File Exposure
Severity (1-10): 9
Priority (1-10): 10
Match type: url_contains
Match value (comma separated): .env,.git,backup,db.sql,config.php
Actions (comma separated): Download file,Extract secrets,Check for credentials,Search API keys,Try reuse credentials

# Note: The rule already exists.
If was add return message

[Nept Assistent] Rule added successfully!

# Example Output

[Nept Assistent] INTELLIGENCE REPORT

Risk Score: 42

[+] Open Port (3)
   -> example.com (risk=12)

ATTACK PLAN:

1. Try default credentials
2. Fuzz directories
3. Check misconfigurations
```

Architecture

```
core/
 ├── engine.py 
 ├── ai.py 
 ├── rules.json


modules/
 ├── dnsinfo.py 
 ├── subdomain.py
 ├── portscan.py
 ├── httpinfo.py
 ├── dir.py 
 ├── recon.py
``` 
 
Disclaimer
```
This tool is for educational and authorized security testing only.
You are responsible for your actions.
```
Author
```
Gabriel Canga Quiloessa

Cybersecurity | Pentester | Red Team
Focused on offensive security and automation
```
Support
```
If you like this project:

 Star the repository
 Fork it
 Contribute ideas
```
Roadmap
```
   Plugin system
   AI auto-learning
   Web dashboard
   Distributed scanning
   Bug bounty mode
```
