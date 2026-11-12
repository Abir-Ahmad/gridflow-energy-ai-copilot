"""Download a checksum-pinned NESO snapshot and ingest using unchanged GridFlow."""

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

URL = "https://api.neso.energy/dataset/8f2fe0af-871c-488d-8bad-960426f24601/resource/f6d02c0f-957b-48cb-82ee-09003f2ba759/download/demanddata_2024.csv"
SHA = "fa7895b6e9ab5eb1b450949d969cb18ffeb6005359fc71c79c87e1c47e59cac6"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, help="Use an existing official snapshot")
    args = parser.parse_args()
    directory = Path("data")
    directory.mkdir(exist_ok=True)
    source = args.csv or directory / "demanddata_2024.csv"
    if args.csv is None and not source.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            content = response.read(10_000_001)
        if len(content) > 10_000_000:
            raise ValueError("Unexpected download size")
        if hashlib.sha256(content).hexdigest() != SHA:
            raise ValueError("NESO snapshot changed; review the revision before updating the checksum")
        source.write_bytes(content)
    if hashlib.sha256(source.read_bytes()).hexdigest() != SHA:
        raise ValueError("Unexpected source checksum; refusing unreviewed data")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "gridflow",
            str(source),
            "--database-url",
            "sqlite:///data/energy.db",
            "--artifacts",
            "artifacts/gridflow",
        ],
        check=True,
    )
    print(json.dumps({"source_url": URL, "source_sha256": SHA, "database": "data/energy.db"}))


if __name__ == "__main__":
    main()
