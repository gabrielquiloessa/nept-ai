import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import time


BASE_DIR = Path(__file__).resolve().parent.parent


class Dir:

    @staticmethod
    def options():
        return {
            "TARGET": {"required": False, "value": None},
            "LIST": {"required": False, "value": None},
            "WORDLIST": {"required": False, "value": None},
            "THREADS": {"required": False, "value": 15},  
        }

    def __init__(self, target=None, list=None, wordlist=None, targets=None, threads=15, **kwargs):
        self.target = target
        self.list = list
        self.targets = targets or []
        self.threads = int(threads)
        self.results = []

        self.lock = threading.Lock() 

        # default wordlist
        if wordlist:
            self.wordlist = Path(wordlist)
        else:
            self.wordlist = BASE_DIR / "wordlists" / "dom.txt"
            print(f"[i] Using default wordlist: {self.wordlist}")

    # =============================
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

        if self.targets:
            targets += self.targets

        clean = []
        for t in targets:
            t = t.replace("http://", "").replace("https://", "")
            clean.append(t)

        return list(set(clean))

    # =============================
    def _load_wordlist(self):
        if not self.wordlist.exists():
            print(f"[!] Wordlist not found: {self.wordlist}")
            return []

        words = []
        with open(self.wordlist, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                w = line.strip()
                if w and " " not in w:
                    words.append(w)

        return words

    # =============================
    def _scan(self, target, path):
        for proto in ["http", "https"]:
            url = f"{proto}://{target}/{path}"

            try:
                r = requests.get(url, timeout=3, allow_redirects=False)
              
                if r.status_code in [200, 403]:
                    
                    with self.lock:
                        print(f"[{r.status_code}] {url}")
                    
                    self.results.append({
                        "url": url,
                        "status": r.status_code
                    })
                    return

                if r.status_code in [301, 302] and "redirect" in r.headers.get("Location", "").lower():
                    return

            except:
                pass
      
            time.sleep(0.01)

    # =============================
    def run(self):
        targets = self._load_targets()

        if not targets:
            print("[!] Target or list required")
            return

        words = self._load_wordlist()

        if not words:
            print("[!] No valid wordlist")
            return

        print(f"[+] Targets: {len(targets)}")
        print(f"[+] Words: {len(words)}")
        print(f"[+] Threads: {self.threads}\n")

        for target in targets:
            print(f"\n[i] Testing: {target}\n")

            with ThreadPoolExecutor(max_workers=self.threads) as exe:
                for word in words:
                    exe.submit(self._scan, target, word)
