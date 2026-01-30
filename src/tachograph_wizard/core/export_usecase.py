"""Template export use cases for separating business logic from UI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import gi

    gi.require_version("Gimp", "3.0")
    from gi.repository import Gimp


class ExportTemplateUseCase:
    """テンプレートエクスポートのビジネスロジックをカプセル化したUseCaseクラス."""

    @staticmethod
    def sanitize_template_name(template_name: str) -> str:
        """テンプレート名を正規化する.

        Args:
            template_name: テンプレート名

        Returns:
            正規化されたテンプレート名(.json拡張子を除去)
        """
        normalized = template_name.strip()
        if normalized.lower().endswith(".json"):
            normalized = normalized[:-5]
        return normalized

    @staticmethod
    def compute_output_path(template_name: str, output_dir: Path) -> Path:
        """テンプレートの出力パスを計算する.

        Args:
            template_name: テンプレート名
            output_dir: 出力ディレクトリ

        Returns:
            出力パス
        """
        normalized_name = ExportTemplateUseCase.sanitize_template_name(template_name)
        return output_dir / f"{normalized_name}.json"

    @staticmethod
    def export_template(
        image: Gimp.Image,
        template_name: str,
        output_dir: Path,
        description: str = "",
    ) -> Path:
        """テンプレートをエクスポートする.

        Args:
            image: GIMP画像
            template_name: テンプレート名
            output_dir: 出力ディレクトリ
            description: テンプレートの説明(オプション)

        Returns:
            エクスポートされたファイルのパス

        Raises:
            TemplateExportError: エクスポートに失敗した場合
        """
        from tachograph_wizard.core.template_exporter import TemplateExporter

        normalized_name = ExportTemplateUseCase.sanitize_template_name(template_name)
        output_path = output_dir / f"{normalized_name}.json"

        exporter = TemplateExporter(image)
        return exporter.export_template(normalized_name, output_path, description=description)
