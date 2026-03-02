#!/usr/bin/env python3
"""依存パッケージのライセンスポリシーチェックスクリプト(共有)

使い方:
  python check_licenses.py --mode allowlist [--licenses-file /tmp/licenses.json]
  python check_licenses.py --mode denylist  [--licenses-file /tmp/licenses.json]

--mode allowlist: 全パッケージのライセンスが許可リストに含まれることを確認
--mode denylist:  全パッケージのライセンスが拒否リストに含まれないことを確認
"""

import argparse
import json
import sys
from pathlib import Path

# 許可ライセンスリスト (quality-check で使用)
ALLOWED_LICENSES = {
    "MIT",
    "MIT License",
    "Apache-2.0",
    "Apache Software License",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSD License",
    "ISC",
    "ISC License (ISCL)",
    "GPL-3.0",
    "GNU General Public License v3 (GPLv3)",
    "Unlicense",
    "Python Software Foundation License",
    "Public Domain",
}

# 拒否ライセンスリスト (security-check で使用)
DENIED_LICENSES = {
    "GPL-1.0",
    "GPL-1.0+",
    "GPL-1.0-only",
    "GPL-1.0-or-later",
    "GPL-2.0",
    "GPL-2.0+",
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "LGPL-2.0",
    "LGPL-2.0+",
    "LGPL-2.0-only",
    "LGPL-2.0-or-later",
    "LGPL-2.1",
    "LGPL-2.1+",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "GNU General Public License v2",
    "GNU General Public License v2 (GPLv2)",
    "GNU Lesser General Public License v2",
    "GNU Lesser General Public License v2 (LGPLv2)",
    "GNU Lesser General Public License v2.1",
}


def parse_license_parts(license_name: str) -> set[str]:
    """ライセンス文字列を個別のライセンス名に分割する。"""
    raw_parts = license_name.replace(" OR ", ",").replace(";", ",").split(",")
    return {p.strip() for p in raw_parts if p.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(description="ライセンスポリシーチェック")
    parser.add_argument(
        "--mode",
        choices=["allowlist", "denylist"],
        required=True,
        help="チェックモード: allowlist(許可リスト) または denylist(拒否リスト)",
    )
    parser.add_argument(
        "--licenses-file",
        default="/tmp/licenses.json",  # noqa: S108  # nosec B108
        help="pip-licenses --format=json の出力ファイルパス",
    )
    args = parser.parse_args()

    with Path(args.licenses_file).open() as f:
        packages = json.load(f)

    violations: list[str] = []

    for pkg in packages:
        # ライセンス不明の場合:
        #   denylist モード: 拒否リストに合致しないため通過 (benefit-of-the-doubt)
        #   allowlist モード: 許可リストに合致しないため違反として検出 (明示的承認が必要)
        license_name = (pkg.get("License") or "UNKNOWN").strip()
        parts = parse_license_parts(license_name)

        if args.mode == "denylist":
            for part in parts:
                if part in DENIED_LICENSES:
                    violations.append(f"{pkg['Name']} ({part})")
        else:  # allowlist
            for part in parts:
                if part not in ALLOWED_LICENSES:
                    violations.append(f"{pkg['Name']} ({part})")

    if violations:
        label = "Denied" if args.mode == "denylist" else "Disallowed"
        sys.stderr.write(f"{label} licenses detected:\n  " + "\n  ".join(violations) + "\n")
        sys.exit(1)

    if args.mode == "denylist":
        sys.stdout.write("No denied licenses found in dependencies.\n")
    else:
        sys.stdout.write("All dependency licenses are within the allowlist.\n")


if __name__ == "__main__":
    main()
