import json
import csv
from pathlib import Path

class OutputHandler:

    def save(self, results, kwargs):
        output = kwargs.get("output")
        fmt = kwargs.get("format", "txt")

        if not output or not results:
            return

        path = Path(output)

        if fmt == "json":
            with open(path, "w") as f:
                json.dump(results, f, indent=4)

        elif fmt == "csv":
            with open(path, "w") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

        else:
            with open(path, "w") as f:
                for r in results:
                    f.write(str(r) + "\n")

        print(f"[+] Saved: {path}")
