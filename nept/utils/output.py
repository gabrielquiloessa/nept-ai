#!/usr/bin/env python3

class Output:
    try: 
        @staticmethod
        def print_info(msg):
            print(f"[INFO] {msg}")

        @staticmethod
        def print_warning(msg):
            print(f"[WARNING] {msg}")

        @staticmethod
        def print_error(msg):
            print(f"[ERROR] {msg}")

        @staticmethod
        def save_to_file(filename, data):
            with open(filename, "w") as f:
                f.write(data)
            print(f"[+] Data save in {filename}")
    except Exception as e:
        print(f"Error: {e}")
