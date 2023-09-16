#!/usr/bin/env python3

import json
import re


def main():
    with open("package.json") as package:
        version = json.load(package)["version"]

    _update(file_name="web/package.json", version=version)
    _update(file_name="rest/version.go", version=version)
    _update(file_name="service/config/version.py", version=version)


def _update(file_name: str, version: str):
    print(f"updating version in {file_name}")

    with open(file_name) as web_package:
        lines = web_package.readlines()

    for idx, line in enumerate(lines):
        if any(v in line for v in ['"version": ', "__version__ = ", "const Version = "]):
            lines[idx] = re.sub(r"\d+\.\d+\.\d+", version, line)
            break

    with open(file_name, "w") as file:
        file.writelines(lines)


if __name__ == "__main__":
    main()
