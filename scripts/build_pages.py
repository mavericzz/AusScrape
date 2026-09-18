"""Build the GitHub Pages static desk into dist/."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    parser.add_argument("--base", default="/")
    args = parser.parse_args()
    from src.pages import build_static_site

    dest = build_static_site(ROOT, ROOT / args.out, base_href=args.base)
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
