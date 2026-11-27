#!/usr/bin/env python3
"""Build an audited, portable source ZIP outside the public checkout."""
import argparse
import hashlib
from pathlib import Path
import sys
import zipfile

from check_public import ALLOWED, ROOT, audit


def package(destination):
    path = Path(destination).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("Release output must be outside the checkout.")
    files = {}
    for name in sorted(ALLOWED):
        file = ROOT / name
        if file.is_symlink() or not file.is_file():
            raise ValueError("Missing or unsafe public release file: " + name)
        data = file.read_bytes()
        errors = audit(name, data)
        if errors:
            raise ValueError("Public audit failed: " + name)
        files[name] = data
    created = False
    try:
        with path.open("xb") as output:
            created = True
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
                for name, data in files.items():
                    entry = zipfile.ZipInfo("AgentSpace/" + name, date_time=(2020, 1, 1, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    entry.external_attr = 0o100644 << 16
                    archive.writestr(entry, data)
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    args = parser.parse_args()
    try:
        print("SHA-256:", package(args.destination))
    except (OSError, ValueError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
