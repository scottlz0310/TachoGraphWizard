"""Text insertion use cases for separating business logic from UI."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from tachograph_wizard.core.settings_manager import parse_date_string, save_csv_path, save_output_dir

if TYPE_CHECKING:
    import gi

    gi.require_version("Gimp", "3.0")
    from gi.repository import Gimp


class CsvDateError(ValueError):
    """Raised when CSV date values are invalid."""

    @classmethod
    def from_components(cls, year: str, month: str, day: str) -> CsvDateError:
        message = f"Invalid date components in CSV: {year}-{month}-{day}"
        return cls(message)

    @classmethod
    def from_string(cls, value: str) -> CsvDateError:
        message = f"Invalid date format in CSV: {value}"
        return cls(message)


class TextInsertUseCase:
    """ビジネスロジックをカプセル化したUseCaseクラス."""

    @staticmethod
    def resolve_date_from_row(
        row_data: dict[str, str],
        *,
        strict: bool,
    ) -> tuple[datetime.date | None, str]:
        """CSV行から日付を解決する.

        Args:
            row_data: CSV行データ
            strict: 厳密モード(エラー時に例外を投げる)

        Returns:
            (解決された日付 or None, ソース)
            ソースは "csv_parts" | "csv_date" | "invalid" | "none"

        Raises:
            CsvDateError: strict=True で日付が無効な場合
        """
        year = row_data.get("date_year", "").strip()
        month = row_data.get("date_month", "").strip()
        day = row_data.get("date_day", "").strip()
        if year or month or day:
            # All three components must be present; partial components are ignored
            if year and month and day:
                try:
                    return datetime.date(int(year), int(month), int(day)), "csv_parts"
                except ValueError as exc:
                    if strict:
                        raise CsvDateError.from_components(year, month, day) from exc
                    return None, "invalid"

        date_value = row_data.get("date", "").strip()
        if date_value:
            parsed = parse_date_string(date_value)
            if parsed is None:
                if strict:
                    raise CsvDateError.from_string(date_value)
                return None, "invalid"
            return parsed, "csv_date"

        return None, "none"

    @staticmethod
    def build_row_data(
        row_data: dict[str, str],
        selected_date: datetime.date,
        *,
        strict: bool,
    ) -> dict[str, str]:
        """CSV行データに日付情報を付加する.

        Args:
            row_data: CSV行データ
            selected_date: UIで選択された日付(フォールバック用)
            strict: 厳密モード(エラー時に例外を投げる)

        Returns:
            date_year, date_month, date_day, date フィールドが埋められた行データ

        Raises:
            CsvDateError: strict=True で日付が無効な場合
        """
        result = dict(row_data)
        resolved_date, source = TextInsertUseCase.resolve_date_from_row(row_data, strict=strict)
        if resolved_date is None:
            resolved_date = selected_date
            source = "ui"

        if source != "csv_parts":
            result["date_year"] = str(resolved_date.year)
            result["date_month"] = str(resolved_date.month)
            result["date_day"] = str(resolved_date.day)

        if not result.get("date", "").strip():
            result["date"] = resolved_date.isoformat()

        return result

    @staticmethod
    def generate_filename_from_row(
        row_data: dict[str, str],
        selected_date: datetime.date,
        selected_fields: list[str],
    ) -> str:
        """CSV行データとフィールド選択からファイル名を生成する.

        Args:
            row_data: CSV行データ
            selected_date: UIで選択された日付
            selected_fields: 選択されたファイル名フィールド

        Returns:
            生成されたファイル名
        """
        from tachograph_wizard.core.filename_generator import generate_filename

        return generate_filename(
            date=selected_date,
            vehicle_number=row_data.get("vehicle_no", "") if "vehicle_no" in selected_fields else "",
            driver_name=row_data.get("driver", "") if "driver" in selected_fields else "",
        )

    @staticmethod
    def load_csv(csv_path: Path) -> list[dict[str, str]]:
        """CSVファイルを読み込む.

        Args:
            csv_path: CSVファイルパス

        Returns:
            パースされたCSVデータ(行のリスト)

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            ValueError: CSVのパースに失敗した場合
        """
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_data = CSVParser.parse(csv_path)
        save_csv_path(csv_path)
        return csv_data

    @staticmethod
    def insert_text_from_csv(
        image: Gimp.Image,
        template_path: Path,
        row_data: dict[str, str],
        selected_date: datetime.date,
    ) -> list[Gimp.Layer]:
        """CSVデータからテキストレイヤーを挿入する.

        Args:
            image: GIMP画像
            template_path: テンプレートファイルパス
            row_data: CSV行データ
            selected_date: UIで選択された日付

        Returns:
            挿入されたレイヤーのリスト

        Raises:
            CsvDateError: 日付が無効な場合
        """
        from tachograph_wizard.core.template_manager import TemplateManager
        from tachograph_wizard.core.text_renderer import TextRenderer

        template_manager = TemplateManager()
        template = template_manager.load_template(template_path)

        renderer = TextRenderer(image, template)

        enriched_row = TextInsertUseCase.build_row_data(row_data, selected_date, strict=True)
        return renderer.render_from_csv_row(enriched_row)

    @staticmethod
    def save_image_with_metadata(
        image: Gimp.Image,
        output_folder: Path,
        row_data: dict[str, str],
        selected_date: datetime.date,
        selected_fields: list[str],
    ) -> Path:
        """画像をメタデータ(ファイル名)付きで保存する.

        Args:
            image: GIMP画像
            output_folder: 出力フォルダ
            row_data: CSV行データ
            selected_date: UIで選択された日付
            selected_fields: 選択されたファイル名フィールド

        Returns:
            保存されたファイルのパス

        Raises:
            CsvDateError: 日付が無効な場合
        """
        from tachograph_wizard.core.exporter import Exporter

        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=True)

        save_output_dir(output_folder)

        enriched_row = TextInsertUseCase.build_row_data(row_data, selected_date, strict=True)
        filename = TextInsertUseCase.generate_filename_from_row(enriched_row, selected_date, selected_fields)
        output_path = output_folder / filename

        # Duplicate image before saving to avoid modifying the original
        export_image = image.duplicate()
        try:
            Exporter.save_png(export_image, output_path, flatten=False)
        finally:
            if hasattr(export_image, "delete"):
                export_image.delete()

        return output_path
