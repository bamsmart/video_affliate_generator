"""Smart Shopee/TikTok screenshot cropper to produce clean product Ingredients for Google Flow."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image


def is_mobile_screenshot(img_bytes: bytes) -> bool:
    """Return True when image aspect ratio matches a vertical phone screenshot (H/W >= 1.65)."""
    with Image.open(io.BytesIO(img_bytes)) as im:
        w, h = im.size
        if w <= 0:
            return False
        return (h / float(w)) >= 1.65


def prepare_clean_product_ingredient(
    img_bytes: bytes,
    top_crop_pct: float = 0.11,
    bottom_crop_pct: float = 0.34,
) -> tuple[bytes, bool]:
    """Crop out mobile status/search bars & bottom price/buy bars from tall Shopee screenshots.

    On a typical Shopee mobile product screenshot (e.g. 1080x2400), the top ~11% holds the OS
    status bar + search bar, the middle ~55% holds the 1:1 hero product gallery photo, and the
    bottom ~34% holds price banners, vouchers, title text, and the 'Beli Sekarang' bar.
    If the image is already a clean product photo (H/W < 1.65), it is normalized without cropping.
    Returns `(jpeg_bytes, was_cropped)`.
    """
    with Image.open(io.BytesIO(img_bytes)) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        was_cropped = False

        if w > 0 and (h / float(w)) >= 1.65:
            t_pct = max(0.0, min(0.35, top_crop_pct))
            b_pct = max(0.0, min(0.55, bottom_crop_pct))
            top_px = int(round(h * t_pct))
            bottom_px = int(round(h * (1.0 - b_pct)))
            if bottom_px - top_px >= int(w * 0.6):
                rgb = rgb.crop((0, top_px, w, bottom_px))
                was_cropped = True

        rgb.thumbnail((1440, 1440), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=93, optimize=True)
        return buf.getvalue(), was_cropped


def save_clean_ingredient_image(
    img_bytes: bytes,
    output_dir: Path,
    top_crop_pct: float = 0.11,
    bottom_crop_pct: float = 0.34,
) -> tuple[Path, bool]:
    """Save `ingredient_produk_bersih.jpg` into output_dir and return `(path, was_cropped)`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_bytes, was_cropped = prepare_clean_product_ingredient(
        img_bytes,
        top_crop_pct=top_crop_pct,
        bottom_crop_pct=bottom_crop_pct,
    )
    out_path = output_dir / "ingredient_produk_bersih.jpg"
    out_path.write_bytes(clean_bytes)
    return out_path, was_cropped
