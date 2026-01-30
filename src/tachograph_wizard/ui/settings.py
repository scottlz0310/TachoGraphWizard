"""Settings object for TextInserter dialog.

統一されたsettingsアクセスを提供するクラス。
内部的にsettings_managerの関数を使用しているが、
メソッドベースのオブジェクト指向なAPIを提供する。
"""

from __future__ import annotations

import datetime
from pathlib import Path

from tachograph_wizard.core import settings_manager


class Settings:
    """TextInserterダイアログの設定を管理するクラス。

    内部的にsettings_managerの関数を呼び出すラッパー。
    メソッドベースのAPIで、よりオブジェクト指向的なアクセスを提供。
    """

    def load_last_used_date(self) -> datetime.date | None:
        """最後に使用した日付をロードする。

        Returns:
            最後に使用した日付、または None。
        """
        return settings_manager.load_last_used_date()

    def save_last_used_date(self, selected_date: datetime.date) -> None:
        """最後に使用した日付を保存する。

        Args:
            selected_date: 保存する日付。
        """
        settings_manager.save_last_used_date(selected_date)

    def load_template_dir(self, default_dir: Path) -> Path:
        """テンプレートディレクトリをロードする。

        Args:
            default_dir: 設定が存在しない場合のデフォルトディレクトリ。

        Returns:
            テンプレートディレクトリのパス。
        """
        return settings_manager.load_template_dir(default_dir)

    def save_template_dir(self, selected_dir: Path) -> None:
        """テンプレートディレクトリを保存する。

        Args:
            selected_dir: 保存するディレクトリ。
        """
        settings_manager.save_template_dir(selected_dir)

    def load_csv_path(self) -> Path | None:
        """最後に使用したCSVファイルパスをロードする。

        Returns:
            CSVファイルのパス、または None。
        """
        return settings_manager.load_csv_path()

    def save_csv_path(self, csv_path: Path) -> None:
        """CSVファイルパスを保存する。

        Args:
            csv_path: 保存するCSVファイルパス。
        """
        settings_manager.save_csv_path(csv_path)

    def load_output_dir(self) -> Path | None:
        """最後に使用した出力ディレクトリをロードする。

        Returns:
            出力ディレクトリのパス、または None。
        """
        return settings_manager.load_output_dir()

    def save_output_dir(self, output_dir: Path) -> None:
        """出力ディレクトリを保存する。

        Args:
            output_dir: 保存するディレクトリ。
        """
        settings_manager.save_output_dir(output_dir)

    def load_filename_fields(self) -> list[str]:
        """保存されたファイル名フィールド選択をロードする。

        Returns:
            選択されたファイル名フィールドのリスト。デフォルトは ["date"]。
        """
        return settings_manager.load_filename_fields()

    def save_filename_fields(self, fields: list[str]) -> None:
        """ファイル名フィールド選択を保存する。

        Args:
            fields: 保存するファイル名フィールドのリスト。
        """
        settings_manager.save_filename_fields(fields)

    def load_window_size(self) -> tuple[int, int]:
        """保存されたウィンドウサイズをロードする。

        Returns:
            (幅, 高さ) のタプル。デフォルトは (500, 600)。
        """
        return settings_manager.load_window_size()

    def save_window_size(self, width: int, height: int) -> None:
        """ウィンドウサイズを保存する。

        Args:
            width: ウィンドウの幅(ピクセル)。
            height: ウィンドウの高さ(ピクセル)。
        """
        settings_manager.save_window_size(width, height)
