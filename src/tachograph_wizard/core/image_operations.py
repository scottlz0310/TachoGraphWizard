"""画像操作モジュール.

GIMP画像の操作に関するユーティリティ関数を提供する。
画像の複製、クロップ、マスク適用などの機能を含む。
"""

from __future__ import annotations

import datetime
import os
from collections.abc import Callable
from pathlib import Path

import gi

gi.require_version("Gimp", "3.0")

from gi.repository import Gimp, GObject

from tachograph_wizard.core.pdb_runner import run_pdb_procedure


def _default_debug_log(message: str) -> None:
    """デフォルトのデバッグログ関数.

    環境変数TEMPまたはTMPで指定されたディレクトリにログを出力する。

    Args:
        message: ログメッセージ
    """
    try:
        base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
        if not base:
            return
        log_path = Path(base) / "tachograph_wizard.log"
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{ts}] image_operations: {message}\n")
    except Exception:
        return


def duplicate_image(image: Gimp.Image, debug_log: Callable[[str], None] | None = None) -> Gimp.Image:
    """画像を複製する.

    Args:
        image: 複製元のGIMP画像
        debug_log: デバッグログ関数(オプション)

    Returns:
        複製されたGIMP画像
    """
    log_fn = debug_log or _default_debug_log

    dup_fn = getattr(image, "duplicate", None)
    if callable(dup_fn):
        return dup_fn()

    result = run_pdb_procedure(
        "gimp-image-duplicate",
        [GObject.Value(Gimp.Image, image)],
        debug_log=log_fn,
    )
    return result.index(1)


def crop_image(
    image: Gimp.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    debug_log: Callable[[str], None] | None = None,
) -> None:
    """画像をクロップする.

    Args:
        image: クロップ対象のGIMP画像
        x: クロップ開始X座標
        y: クロップ開始Y座標
        width: クロップ後の幅
        height: クロップ後の高さ
        debug_log: デバッグログ関数(オプション)
    """
    log_fn = debug_log or _default_debug_log

    crop_fn = getattr(image, "crop", None)
    if callable(crop_fn):
        crop_fn(width, height, x, y)
        return

    run_pdb_procedure(
        "gimp-image-crop",
        [
            GObject.Value(Gimp.Image, image),
            GObject.Value(GObject.TYPE_INT, width),
            GObject.Value(GObject.TYPE_INT, height),
            GObject.Value(GObject.TYPE_INT, x),
            GObject.Value(GObject.TYPE_INT, y),
        ],
        debug_log=log_fn,
    )


def apply_component_mask(
    image: Gimp.Image,
    comp_mask: bytearray,
    mask_width: int,
    mask_height: int,
    crop_x: int,
    crop_y: int,
    scale_x: float,
    scale_y: float,
    threshold: int,  # noqa: ARG001 - kept for API compatibility
    debug_log: Callable[[str], None] | None = None,
) -> None:
    """コンポーネントマスクの外側のゴミピクセルを除去する.

    検出されたコンポーネントの外側のピクセルを透明にし、
    内側のピクセルはすべて保持する。

    Args:
        image: クロップ済みの画像
        comp_mask: 分析解像度でのバイナリマスク
        mask_width: 分析マスクの幅
        mask_height: 分析マスクの高さ
        crop_x: 元画像でのクロップX座標オフセット
        crop_y: 元画像でのクロップY座標オフセット
        scale_x: 分析スケール係数X
        scale_y: 分析スケール係数Y
        threshold: 検出に使用した閾値(検出時と同じ値)
        debug_log: デバッグログ関数(オプション)
    """
    log_fn = debug_log or _default_debug_log

    try:
        layers = image.get_layers()
        if not layers:
            return

        layer = layers[0]
        img_width = image.get_width()
        img_height = image.get_height()

        # レイヤーにアルファチャンネルを追加
        if not layer.has_alpha():
            layer.add_alpha()

        # 空の選択範囲で開始
        run_pdb_procedure(
            "gimp-selection-none",
            [GObject.Value(Gimp.Image, image)],
            debug_log=log_fn,
        )

        # 分析座標でのコンポーネントの境界ボックスを検出
        min_ax, max_ax = mask_width, 0
        min_ay, max_ay = mask_height, 0
        component_pixel_count = 0
        for ay in range(mask_height):
            for ax in range(mask_width):
                if comp_mask[ay * mask_width + ax] == 1:
                    min_ax = min(min_ax, ax)
                    max_ax = max(max_ax, ax)
                    min_ay = min(min_ay, ay)
                    max_ay = max(max_ay, ay)
                    component_pixel_count += 1

        log_fn(
            f"garbage_removal: component bbox in analysis coords: "
            f"x=[{min_ax},{max_ax}] y=[{min_ay},{max_ay}] pixels={component_pixel_count}",
        )

        # フル解像度座標に変換
        full_min_x = int((min_ax / scale_x) - crop_x)
        full_max_x = int((max_ax / scale_x) - crop_x)
        full_min_y = int((min_ay / scale_y) - crop_y)
        full_max_y = int((max_ay / scale_y) - crop_y)

        log_fn(
            f"garbage_removal: bbox in cropped image coords (before clamp): "
            f"x=[{full_min_x},{full_max_x}] y=[{full_min_y},{full_max_y}]",
        )

        # 画像の境界にクランプ
        full_min_x = max(0, full_min_x)
        full_max_x = min(img_width - 1, full_max_x)
        full_min_y = max(0, full_min_y)
        full_max_y = min(img_height - 1, full_max_y)

        # Select component area using ellipse - better for circular discs
        width = full_max_x - full_min_x + 1
        height = full_max_y - full_min_y + 1

        log_fn(
            f"garbage_removal: ellipse selection params: "
            f"x={full_min_x} y={full_min_y} w={width} h={height} "
            f"(image size: {img_width}x{img_height})",
        )

        if width > 0 and height > 0:
            # 楕円でコンポーネント領域を選択
            run_pdb_procedure(
                "gimp-image-select-ellipse",
                [
                    GObject.Value(Gimp.Image, image),
                    GObject.Value(Gimp.ChannelOps, Gimp.ChannelOps.REPLACE),
                    GObject.Value(GObject.TYPE_DOUBLE, float(full_min_x)),
                    GObject.Value(GObject.TYPE_DOUBLE, float(full_min_y)),
                    GObject.Value(GObject.TYPE_DOUBLE, float(width)),
                    GObject.Value(GObject.TYPE_DOUBLE, float(height)),
                ],
                debug_log=log_fn,
            )

            # 選択範囲を少しフェザーして硬いエッジを避ける
            run_pdb_procedure(
                "gimp-selection-feather",
                [
                    GObject.Value(Gimp.Image, image),
                    GObject.Value(GObject.TYPE_DOUBLE, 2.0),  # 2px feather
                ],
                debug_log=log_fn,
            )

            # Invert selection to select garbage outside the ellipse
            run_pdb_procedure(
                "gimp-selection-invert",
                [GObject.Value(Gimp.Image, image)],
                debug_log=log_fn,
            )

            # Check if selection is empty
            is_empty_result = run_pdb_procedure(
                "gimp-selection-is-empty",
                [GObject.Value(Gimp.Image, image)],
                debug_log=log_fn,
            )
            is_empty = is_empty_result.index(1)

            if is_empty:
                log_fn("garbage_removal: selection is empty, nothing to delete")
            else:
                # Delete garbage - make selected area transparent
                run_pdb_procedure(
                    "gimp-drawable-edit-clear",
                    [GObject.Value(Gimp.Drawable, layer)],
                    debug_log=log_fn,
                )
                log_fn("garbage_removal: deleted garbage outside ellipse")

            # 選択範囲を解除
            run_pdb_procedure(
                "gimp-selection-none",
                [GObject.Value(Gimp.Image, image)],
                debug_log=log_fn,
            )

            log_fn("garbage_removal: applied successfully")
        else:
            log_fn("garbage_removal: component too small, skipped")

    except Exception as e:
        log_fn(f"garbage_removal failed: {type(e).__name__}: {e}")
        # ゴミ除去に失敗しても処理を継続
