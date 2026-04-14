#!/usr/bin/env python3

import re

class Validator:
    try:
        @staticmethod
        def is_valid_ip(ip):
            pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
            return re.match(pattern, ip) is not None

        @staticmethod
        def is_valid_domain(domain):
            pattern = r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
            return re.match(pattern, domain) is not None
    except Exception as e:
        print(f"Error: {e}")
