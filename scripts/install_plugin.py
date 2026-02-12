#!/usr/bin/env python3
"""TachoGraphWizard プラグインを対話式でインストールするスクリプト。"""

from __future__ import annotations

import argparse
import base64
import os
import platform
import shutil
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

PLUGIN_DIR_NAME: Final[str] = "tachograph_wizard"


class InstallMode(StrEnum):
    """インストール方式。"""

    COPY = "copy"
    SYMLINK = "symlink"


@dataclass(frozen=True)
class CliOptions:
    """コマンドライン引数。"""

    mode: InstallMode | None
    plugin_base: Path | None
    target: Path | None
    source: Path | None
    non_interactive: bool
    yes: bool


def _write_stdout(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def _write_stderr(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_source_dir() -> Path:
    return _repo_root() / "src" / PLUGIN_DIR_NAME


def _default_plugin_base() -> Path:
    system_name = platform.system()
    home = Path.home()

    if system_name == "Windows":
        # Prefer APPDATA, then fall back to LOCALAPPDATA, then to the home directory.
        # Empty strings are treated as unset (falsy in boolean context)
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        base_dir = Path(appdata) if appdata else home
        return base_dir / "GIMP" / "3.0" / "plug-ins"
    if system_name == "Darwin":
        return home / "Library" / "Application Support" / "GIMP" / "3.0" / "plug-ins"
    # Linux: respect XDG_CONFIG_HOME, otherwise use ~/.config
    # Empty strings are treated as unset per XDG Base Directory specification
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(xdg_config) if xdg_config else home / ".config"
    return base_dir / "GIMP" / "3.0" / "plug-ins"


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _remove_existing(path: Path) -> None:
    if not _path_exists(path):
        return

    if path.is_symlink() or path.is_file():
        path.unlink()
        return

    shutil.rmtree(path)


def _prompt_text(prompt: str, default: str) -> str:
    question = f"{prompt} [{default}]: "
    try:
        value = input(question).strip()
    except EOFError:
        return default
    return value if value else default


def _prompt_yes_no(prompt: str, default: bool) -> bool:
    default_label = "Y/n" if default else "y/N"
    try:
        value = input(f"{prompt} ({default_label}): ").strip().lower()
    except EOFError:
        return default

    if not value:
        return default
    return value in {"y", "yes"}


def _select_mode(default_mode: InstallMode) -> InstallMode:
    _write_stdout("インストール方式を選択してください:")
    _write_stdout("  1. copy (Windowsは xcopy / Linuxは copytree)")
    _write_stdout("  2. symlink (開発向け: 変更が即反映)")

    while True:
        choice = _prompt_text("番号を入力", "1" if default_mode is InstallMode.COPY else "2")
        if choice == "1":
            return InstallMode.COPY
        if choice == "2":
            return InstallMode.SYMLINK
        _write_stderr("1 または 2 を入力してください。")


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _create_symlink_with_elevated_powershell(source: Path, target: Path) -> bool:
    powershell = shutil.which("powershell")
    if powershell is None:
        _write_stderr("PowerShell が見つかりません。管理者権限で手動実行してください。")
        return False

    source_literal = _powershell_quote(str(source))
    target_literal = _powershell_quote(str(target))
    inner_script = "\n".join(
        [
            "$ErrorActionPreference = 'Stop'",
            f"$source = {source_literal}",
            f"$target = {target_literal}",
            "$parent = Split-Path -Path $target -Parent",
            "if (-not (Test-Path -LiteralPath $parent)) {",
            "    New-Item -ItemType Directory -Path $parent -Force | Out-Null",
            "}",
            "if (Test-Path -LiteralPath $target) {",
            "    Remove-Item -LiteralPath $target -Recurse -Force",
            "}",
            "New-Item -ItemType SymbolicLink -Path $target -Target $source | Out-Null",
        ]
    )
    encoded_inner = base64.b64encode(inner_script.encode("utf-16le")).decode("ascii")

    outer_script = (
        "Start-Process -FilePath "
        f"{_powershell_quote(powershell)} "
        "-Verb RunAs -Wait "
        f"-ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand','{encoded_inner}')"
    )

    result = subprocess.run(  # noqa: S603  # nosec B603
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", outer_script],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _write_stderr("昇格PowerShell実行に失敗しました。")
        if result.stderr:
            _write_stderr(result.stderr.strip())
        return False

    return _path_exists(target)


def _install_copy(source: Path, target: Path) -> bool:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        _write_stderr(f"ターゲットディレクトリの作成に失敗しました: {target.parent}")
        _write_stderr(f"エラー: {error}")
        return False

    if platform.system() == "Windows":
        cmd_path = shutil.which("cmd")
        if cmd_path is None:
            _write_stderr("cmd.exe が見つかりません。")
            return False

        result = subprocess.run(  # noqa: S603  # nosec B603
            [cmd_path, "/c", "xcopy", str(source), str(target), "/E", "/I", "/Y", "/Q", "/H"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            _write_stderr(f"xcopy 失敗 (exit code={result.returncode})")
            if result.stdout:
                _write_stderr(result.stdout.strip())
            if result.stderr:
                _write_stderr(result.stderr.strip())
            return False
        return True

    try:
        shutil.copytree(source, target, copy_function=shutil.copy2)
    except OSError as error:
        _write_stderr(f"ディレクトリのコピーに失敗しました: {error}")
        return False
    return True


def _install_symlink(source: Path, target: Path, interactive: bool, assume_yes: bool) -> bool:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        _write_stderr(f"ターゲットディレクトリの作成に失敗しました: {target.parent}")
        _write_stderr(f"エラー: {error}")
        return False

    try:
        target.symlink_to(source, target_is_directory=True)
        return True
    except OSError as error:
        if platform.system() != "Windows":
            _write_stderr(f"シンボリックリンク作成に失敗しました: {error}")
            return False

        needs_admin = isinstance(error, PermissionError) or getattr(error, "winerror", None) == 1314
        if not needs_admin:
            _write_stderr(f"シンボリックリンク作成に失敗しました: {error}")
            return False

        _write_stderr("権限不足のため、通常権限ではシンボリックリンクを作成できませんでした。")
        if not assume_yes and interactive and not _prompt_yes_no("管理者PowerShellで再実行しますか?", True):
            return False
        if not interactive and not assume_yes:
            _write_stderr("`--yes` なしの非対話モードでは昇格実行できません。")
            return False

        return _create_symlink_with_elevated_powershell(source=source, target=target)


def _parse_args(argv: list[str]) -> CliOptions:
    parser = argparse.ArgumentParser(
        description="TachoGraphWizard を GIMP 3 の plug-ins ディレクトリへインストールします。"
    )
    parser.add_argument(
        "--mode",
        choices=[InstallMode.COPY.value, InstallMode.SYMLINK.value],
        help="copy または symlink を指定します。",
    )
    parser.add_argument("--plugin-base", help="GIMP plug-ins ディレクトリを指定します。")
    parser.add_argument("--target", help="最終的な配置先ディレクトリ (例: .../plug-ins/tachograph_wizard)。")
    parser.add_argument("--source", help="ソースディレクトリ (既定: ./src/tachograph_wizard)。")
    parser.add_argument("--non-interactive", action="store_true", help="質問を出さずに実行します。")
    parser.add_argument("--yes", action="store_true", help="確認質問に自動で Yes を選びます。")

    namespace = parser.parse_args(argv)

    mode = InstallMode(namespace.mode) if namespace.mode else None
    # Apply expandvars then expanduser to support both environment variables and ~
    plugin_base = Path(os.path.expandvars(namespace.plugin_base)).expanduser() if namespace.plugin_base else None
    target = Path(os.path.expandvars(namespace.target)).expanduser() if namespace.target else None
    source = Path(os.path.expandvars(namespace.source)).expanduser() if namespace.source else None

    return CliOptions(
        mode=mode,
        plugin_base=plugin_base,
        target=target,
        source=source,
        non_interactive=namespace.non_interactive,
        yes=namespace.yes,
    )


def _resolve_target(plugin_base: Path | None, explicit_target: Path | None) -> Path:
    if explicit_target is not None:
        return explicit_target
    if plugin_base is None:
        message = "インストール先が決定できません。`--plugin-base` または `--target` を指定してください。"
        raise RuntimeError(message)
    return plugin_base / PLUGIN_DIR_NAME


def run(options: CliOptions) -> int:
    try:
        default_plugin_base = _default_plugin_base()
    except RuntimeError as error:
        _write_stderr(str(error))
        return 1

    # Resolve all paths to absolute form for display and validation
    source = (options.source or _default_source_dir()).expanduser().resolve()
    plugin_base = (options.plugin_base or default_plugin_base).expanduser().resolve()
    target = _resolve_target(plugin_base=plugin_base, explicit_target=options.target).expanduser().resolve()
    mode = options.mode or InstallMode.COPY

    if not source.exists() or not source.is_dir():
        _write_stderr(f"ソースディレクトリが見つかりません: {source}")
        return 1

    interactive = not options.non_interactive

    if interactive and options.target is None:
        _write_stdout(f"ソース: {source}")
        input_value = _prompt_text("GIMP plug-ins ディレクトリ", str(plugin_base))
        # Expand environment variables and user home directory
        selected_base = Path(os.path.expandvars(input_value)).expanduser()
        # Resolve to absolute path to show user the actual location
        try:
            selected_base = selected_base.resolve()
        except (OSError, RuntimeError) as error:
            # Path resolution failed - likely invalid path syntax
            _write_stderr(f"パスの解決に失敗しました: {selected_base}")
            _write_stderr(f"エラー: {error}")
            return 1
        plugin_base = selected_base
        target = plugin_base / PLUGIN_DIR_NAME

    if interactive and options.mode is None:
        mode = _select_mode(default_mode=mode)

    _write_stdout("")
    _write_stdout("インストール設定:")
    _write_stdout(f"  source: {source}")
    _write_stdout(f"  target: {target}")
    _write_stdout(f"  mode:   {mode.value}")

    if interactive and not options.yes and not _prompt_yes_no("この内容で実行しますか?", True):
        _write_stdout("キャンセルしました。")
        return 0

    if _path_exists(target):
        if not options.yes:
            if not interactive:
                _write_stderr(f"既存のインストール先が存在します: {target}")
                _write_stderr("`--yes` を指定するか、既存ディレクトリを削除してください。")
                return 1
            if not _prompt_yes_no("既存のインストールを削除して続行しますか?", False):
                _write_stdout("キャンセルしました。")
                return 0
        _remove_existing(target)

    success = (
        _install_copy(source=source, target=target)
        if mode is InstallMode.COPY
        else _install_symlink(
            source=source,
            target=target,
            interactive=interactive,
            assume_yes=options.yes,
        )
    )

    if not success:
        _write_stderr("インストールに失敗しました。")
        return 1

    _write_stdout("")
    _write_stdout("インストールが完了しました。")
    _write_stdout(f"配置先: {target}")
    _write_stdout("GIMP を再起動して、Filters > Processing からプラグインを確認してください。")
    return 0


def main() -> int:
    return run(_parse_args(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
