"""画像分析モジュール.

画像の分析に関するユーティリティ関数を提供する。
連結成分検出、大津の二値化閾値、DPI取得などの機能を含む。
"""

from __future__ import annotations

from dataclasses import dataclass

import gi

gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")

from gi.repository import Gegl, Gimp


@dataclass
class Component:
    """連結成分を表すデータクラス.

    画像内で検出された連結成分の境界ボックスと面積を保持する。
    """

    min_x: int
    min_y: int
    max_x: int
    max_y: int
    area: int

    @property
    def width(self) -> int:
        """コンポーネントの幅を返す."""
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        """コンポーネントの高さを返す."""
        return self.max_y - self.min_y + 1

    @property
    def diameter(self) -> int:
        """コンポーネントの直径(幅と高さの最大値)を返す."""
        return max(self.width, self.height)


# Maximum image size for analysis in pixels
_ANALYSIS_MAX_SIZE = 1200


def get_analysis_scale(width: int, height: int) -> float:
    """分析用のスケール係数を計算する.

    画像サイズが_ANALYSIS_MAX_SIZEを超える場合、縮小スケールを返す。

    Args:
        width: 画像の幅
        height: 画像の高さ

    Returns:
        分析用のスケール係数(0.0 < scale <= 1.0)
    """
    max_dim = max(width, height)
    if max_dim <= 0:
        return 1.0
    return min(1.0, _ANALYSIS_MAX_SIZE / max_dim)


def get_image_dpi(image: Gimp.Image) -> float | None:
    """画像のDPIを取得する.

    Args:
        image: GIMP画像オブジェクト

    Returns:
        DPI値(取得できない場合はNone)
    """
    try:
        resolution = image.get_resolution()
    except Exception:
        resolution = None

    if isinstance(resolution, (tuple, list)) and len(resolution) >= 2:
        try:
            x_res = float(resolution[0])
            y_res = float(resolution[1])
            dpi = y_res if y_res > 0 else x_res
            if 50.0 <= dpi <= 1200.0:
                return dpi
        except (TypeError, ValueError):
            return None

    return None


def get_analysis_drawable(image: Gimp.Image) -> Gimp.Drawable:
    """分析用のドローアブルを取得する.

    アクティブなドローアブル、または最初のレイヤーを返す。

    Args:
        image: GIMP画像オブジェクト

    Returns:
        分析用のドローアブル

    Raises:
        RuntimeError: レイヤーが存在しない場合
    """
    try:
        drawable = image.get_active_drawable()
        if drawable is not None:
            return drawable
    except Exception:
        pass

    layers = image.get_layers()
    if not layers:
        msg = "No layers available for analysis"
        raise RuntimeError(msg)
    return layers[0]


def buffer_get_bytes(
    buffer: Gegl.Buffer,
    rect: Gegl.Rectangle,
    scale: float,
    fmt: str,
) -> bytes:
    """バッファからバイトデータを取得する.

    GIMP/GEGLのバージョン差異を吸収し、複数の方法でバイトデータ取得を試みる。

    Args:
        buffer: GEGLバッファ
        rect: 取得範囲の矩形
        scale: スケール係数
        fmt: ピクセルフォーマット(例: "R'G'B'A u8")

    Returns:
        取得したバイトデータ

    Raises:
        RuntimeError: データ取得に失敗した場合
    """
    attempts = [
        (rect, scale, fmt, Gegl.AbyssPolicy.CLAMP),
        (rect, scale, fmt),
        (rect, fmt, Gegl.AbyssPolicy.CLAMP),
        (rect, fmt),
    ]
    last_error: Exception | None = None
    for args in attempts:
        try:
            data = buffer.get(*args)
            if isinstance(data, (bytes, bytearray)):
                return bytes(data)
            get_data = getattr(data, "get_data", None)
            if callable(get_data):
                return bytes(get_data())  # type: ignore[arg-type]
            return bytes(data)  # type: ignore[arg-type]
        except Exception as exc:
            last_error = exc
            continue
    msg = f"Failed to read buffer data ({type(last_error).__name__}: {last_error})"
    raise RuntimeError(msg)


def otsu_threshold(hist: list[int], total: int) -> int:
    """大津の方法で二値化閾値を計算する.

    ヒストグラムからクラス間分散を最大化する閾値を求める。

    Args:
        hist: 256要素のヒストグラム(各輝度値の出現回数)
        total: 総ピクセル数

    Returns:
        最適な閾値(0-255)
    """
    if total <= 0:
        return 255
    sum_total = sum(i * hist[i] for i in range(256))
    sum_back = 0
    weight_back = 0
    max_var = -1.0
    threshold = 200

    for t in range(256):
        weight_back += hist[t]
        if weight_back == 0:
            continue
        weight_fore = total - weight_back
        if weight_fore == 0:
            break
        sum_back += t * hist[t]
        mean_back = sum_back / weight_back
        mean_fore = (sum_total - sum_back) / weight_fore
        between_var = weight_back * weight_fore * (mean_back - mean_fore) ** 2
        if between_var > max_var:
            max_var = between_var
            threshold = t

    return threshold


def find_components(mask: bytearray, width: int, height: int) -> list[Component]:
    """マスク画像から連結成分を検出する.

    4連結で連結成分を検出し、各成分の境界ボックスと面積を返す。

    Args:
        mask: バイナリマスク(0=背景、非0=前景)
        width: マスクの幅
        height: マスクの高さ

    Returns:
        検出された連結成分のリスト
    """
    visited = bytearray(len(mask))
    components: list[Component] = []

    for idx, value in enumerate(mask):
        if value == 0 or visited[idx]:
            continue

        stack = [idx]
        visited[idx] = 1
        min_x = max_x = idx % width
        min_y = max_y = idx // width
        area = 0

        while stack:
            current = stack.pop()
            x = current % width
            y = current // width
            area += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

            left = current - 1
            right = current + 1
            up = current - width
            down = current + width

            if x > 0 and mask[left] and not visited[left]:
                visited[left] = 1
                stack.append(left)
            if x < width - 1 and mask[right] and not visited[right]:
                visited[right] = 1
                stack.append(right)
            if y > 0 and mask[up] and not visited[up]:
                visited[up] = 1
                stack.append(up)
            if y < height - 1 and mask[down] and not visited[down]:
                visited[down] = 1
                stack.append(down)

        components.append(Component(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y, area=area))

    return components
