"""Smart screenshot cropper, Storyboard Grid Auto-Splitter, & batch ZIP builder for Google Flow."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from PIL import Image, ImageOps


def is_mobile_screenshot(img_bytes: bytes) -> bool:
    """Return True when image aspect ratio matches a full tall phone screen capture (H/W >= 1.92)."""
    with Image.open(io.BytesIO(img_bytes)) as im:
        w, h = im.size
        if w <= 0:
            return False
        return (h / float(w)) >= 1.92


def prepare_clean_product_ingredient(
    img_bytes: bytes,
    top_crop_pct: float = 0.08,
    bottom_crop_pct: float = 0.24,
) -> tuple[bytes, bool]:
    """Safely trim mobile OS status bar & bottom buy bar without cutting off product legs/base.

    Standard 9:16 photos (H/W ~1.78) are preserved 100% intact so bottom product legs/parts
    are never sliced off. Only ultra-tall phone screenshots (H/W >= 1.92, e.g. 20:9) are trimmed
    conservatively (8% top, 24% bottom) to preserve full 1:1 and 3:4 product gallery frames.
    Returns `(jpeg_bytes, was_cropped)`.
    """
    with Image.open(io.BytesIO(img_bytes)) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        was_cropped = False

        if w > 0 and (h / float(w)) >= 1.92:
            t_pct = max(0.0, min(0.35, top_crop_pct))
            b_pct = max(0.0, min(0.55, bottom_crop_pct))
            top_px = int(round(h * t_pct))
            bottom_px = int(round(h * (1.0 - b_pct)))
            if bottom_px - top_px >= int(w * 0.75):
                rgb = rgb.crop((0, top_px, w, bottom_px))
                was_cropped = True

        rgb.thumbnail((1440, 1440), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=93, optimize=True)
        return buf.getvalue(), was_cropped


def save_clean_ingredient_image(
    img_bytes: bytes,
    output_dir: Path,
    top_crop_pct: float = 0.08,
    bottom_crop_pct: float = 0.24,
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


def build_product_turnaround_sheet(
    images_bytes: list[bytes],
    top_crop_pct: float = 0.08,
    bottom_crop_pct: float = 0.24,
) -> tuple[bytes, bool]:
    """Combine 2-4 multi-angle product photos into a neutral Product Turnaround Sheet (Slot 1).

    When only 1 photo is provided, falls back cleanly to `prepare_clean_product_ingredient`.
    """
    valid = [b for b in images_bytes[:4] if b]
    if not valid:
        raise ValueError("Minimal 1 gambar produk diperlukan untuk membuat Product Authority.")
    if len(valid) == 1:
        return prepare_clean_product_ingredient(
            valid[0],
            top_crop_pct=top_crop_pct,
            bottom_crop_pct=bottom_crop_pct,
        )

    cleaned_imgs: list[Image.Image] = []
    any_cropped = False
    for raw_b in valid:
        clean_b, was_crop = prepare_clean_product_ingredient(
            raw_b,
            top_crop_pct=top_crop_pct,
            bottom_crop_pct=bottom_crop_pct,
        )
        any_cropped = any_cropped or was_crop
        with Image.open(io.BytesIO(clean_b)) as im:
            cleaned_imgs.append(im.convert("RGB"))

    count = len(cleaned_imgs)
    cols, rows = (2, 1) if count == 2 else ((3, 1) if count == 3 else (2, 2))
    cell_size = 640
    pad = 24
    canvas_w = cols * cell_size + (cols + 1) * pad
    canvas_h = rows * cell_size + (rows + 1) * pad
    canvas = Image.new("RGB", (canvas_w, canvas_h), (245, 245, 245))

    for idx, angle_im in enumerate(cleaned_imgs):
        r = idx // cols
        c = idx % cols
        fitted = ImageOps.contain(angle_im, (cell_size, cell_size), Image.Resampling.LANCZOS)
        x0 = pad + c * (cell_size + pad) + (cell_size - fitted.width) // 2
        y0 = pad + r * (cell_size + pad) + (cell_size - fitted.height) // 2
        canvas.paste(fitted, (x0, y0))

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=93, optimize=True)
    return buf.getvalue(), any_cropped


def save_product_authority_image(
    images_bytes: list[bytes],
    output_dir: Path,
    top_crop_pct: float = 0.08,
    bottom_crop_pct: float = 0.24,
) -> tuple[Path, bool]:
    """Save single clean product photo or multi-angle Turnaround Sheet to `ingredient_produk_bersih.jpg`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sheet_bytes, any_cropped = build_product_turnaround_sheet(
        images_bytes,
        top_crop_pct=top_crop_pct,
        bottom_crop_pct=bottom_crop_pct,
    )
    out_path = output_dir / "ingredient_produk_bersih.jpg"
    out_path.write_bytes(sheet_bytes)
    return out_path, any_cropped


def parse_grid_layout(layout: str) -> tuple[int, int]:
    """Parse grid layout label ('2x2', '3x2', '2x3', '3x3') into `(cols, rows)`."""
    clean = (layout or "").strip().lower().replace("×", "x")
    mapping = {
        "2x2": (2, 2),
        "3x2": (3, 2),
        "2x3": (2, 3),
        "3x3": (3, 3),
    }
    return mapping.get(clean, (2, 2))


def split_storyboard_grid(
    img_bytes: bytes,
    cols: int = 2,
    rows: int = 2,
    trim_margin_pct: float = 0.015,
) -> list[bytes]:
    """Slice a Nano Banana contact sheet grid image into individual keyframe JPEGs (left-to-right, top-to-bottom)."""
    safe_cols = max(1, min(4, cols))
    safe_rows = max(1, min(4, rows))
    safe_trim = max(0.0, min(0.08, trim_margin_pct))

    with Image.open(io.BytesIO(img_bytes)) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        if w < safe_cols or h < safe_rows:
            raise ValueError("Dimensi gambar grid terlalu kecil untuk dipotong.")

        cell_w = w / float(safe_cols)
        cell_h = h / float(safe_rows)
        margin_x = int(round(cell_w * safe_trim))
        margin_y = int(round(cell_h * safe_trim))

        frames: list[bytes] = []
        for r in range(safe_rows):
            for c in range(safe_cols):
                x0 = int(round(c * cell_w)) + margin_x
                y0 = int(round(r * cell_h)) + margin_y
                x1 = int(round((c + 1) * cell_w)) - margin_x
                y1 = int(round((r + 1) * cell_h)) - margin_y
                if x1 - x0 < 16 or y1 - y0 < 16:
                    x0, y0 = int(round(c * cell_w)), int(round(r * cell_h))
                    x1, y1 = int(round((c + 1) * cell_w)), int(round((r + 1) * cell_h))

                panel = rgb.crop((x0, y0, x1, y1))
                panel.thumbnail((1440, 1440), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                panel.save(buf, format="JPEG", quality=93, optimize=True)
                frames.append(buf.getvalue())
        return frames


def build_frames_zip(frames: list[bytes], prefix: str = "keyframe") -> bytes:
    """Package split keyframe JPEGs into an in-memory ZIP archive for 1-click Laptop download."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, img_data in enumerate(frames, start=1):
            zf.writestr(f"{prefix}_{idx}.jpg", img_data)
    return zip_buf.getvalue()
