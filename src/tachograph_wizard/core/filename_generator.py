"""Filename generation module for tachograph chart exports.

日付や車両番号などからファイル名を生成するモジュール。
日付を指定しない場合は実行時の「今日」を使用しつつ、副作用を最小限に抑えテスト容易性を重視した設計。
"""

from __future__ import annotations

import datetime


def generate_filename(
    date: datetime.date | None = None,
    vehicle_number: str = "",
    driver_name: str = "",
    extension: str = "png",
) -> str:
    """ファイル名命名規則に従ってファイル名を生成する。

    フォーマット: YYYYMMDD_車番_運転手.png
    例: 20250101_123_TaroYamada.png

    Args:
        date: ファイル名に使用する日付(デフォルト: 今日)。
        vehicle_number: 含める車両番号。
        driver_name: 含める運転手名。
        extension: ファイル拡張子(デフォルト: 'png')。

    Returns:
        生成されたファイル名文字列。
    """
    if date is None:
        date = datetime.date.today()

    date_str = date.strftime("%Y%m%d")
    parts = [date_str]

    if vehicle_number:
        # 車両番号をサニタイズ(スペースをアンダースコアに置換)  # noqa: ERA001
        vehicle_clean = vehicle_number.replace(" ", "_").replace("/", "-")
        parts.append(vehicle_clean)

    if driver_name:
        # 運転手名をサニタイズ(スペースと特殊文字を除去)  # noqa: ERA001
        driver_clean = (
            driver_name.replace(" ", "")
            .replace("　", "")  # 全角スペースを除去
            .replace("/", "-")
            .replace("\\", "-")
        )
        parts.append(driver_clean)

    filename = "_".join(parts) + f".{extension}"
    return filename
