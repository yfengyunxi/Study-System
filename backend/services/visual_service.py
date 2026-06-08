import shutil
import zipfile
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def extract_visual_assets(material):
    extension = Path(material.file_path).suffix.lower()
    output_dir = (
        Path(current_app.config["UPLOAD_FOLDER"])
        / str(material.user_id)
        / "assets"
        / str(material.id)
    )
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if extension == ".pdf":
        return _extract_pdf_pages(material, output_dir)
    if extension == ".pptx":
        return _extract_pptx_images(material, output_dir)
    return []


def delete_visual_asset_files(material):
    output_dir = (
        Path(current_app.config["UPLOAD_FOLDER"])
        / str(material.user_id)
        / "assets"
        / str(material.id)
    )
    if output_dir.exists():
        shutil.rmtree(output_dir)


def _extract_pdf_pages(material, output_dir):
    try:
        import fitz
    except ImportError as exc:
        raise ValueError("PDF 页面视觉索引需要安装 PyMuPDF") from exc

    max_assets = current_app.config["MAX_VISUAL_ASSETS_PER_MATERIAL"]
    dpi = current_app.config["PDF_RENDER_DPI"]
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    assets = []

    document = fitz.open(material.file_path)
    try:
        for page_index in range(min(len(document), max_assets)):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_dir / f"pdf-page-{page_index + 1}.png"
            pixmap.save(str(image_path))
            _normalize_image(image_path)
            assets.append(
                {
                    "asset_type": "pdf_page",
                    "asset_index": page_index,
                    "page_number": page_index + 1,
                    "caption": f"{material.title} 第 {page_index + 1} 页页面图",
                    "image_path": str(image_path),
                }
            )
    finally:
        document.close()
    return assets


def _extract_pptx_images(material, output_dir):
    max_assets = current_app.config["MAX_VISUAL_ASSETS_PER_MATERIAL"]
    assets = []
    with zipfile.ZipFile(material.file_path) as archive:
        media_names = sorted(
            [
                name
                for name in archive.namelist()
                if name.startswith("ppt/media/")
                and Path(name).suffix.lower() in IMAGE_EXTENSIONS
            ]
        )
        for index, name in enumerate(media_names[:max_assets]):
            suffix = Path(name).suffix.lower()
            image_path = output_dir / f"ppt-image-{index + 1}{suffix}"
            with archive.open(name) as source, open(image_path, "wb") as target:
                shutil.copyfileobj(source, target)
            _normalize_image(image_path)
            assets.append(
                {
                    "asset_type": "ppt_image",
                    "asset_index": index,
                    "page_number": None,
                    "caption": f"{material.title} PPT 图片 {index + 1}",
                    "image_path": str(image_path),
                }
            )
    return assets


def _normalize_image(image_path):
    max_side = current_app.config["VISUAL_IMAGE_MAX_SIDE"]
    max_bytes = current_app.config["VISUAL_IMAGE_MAX_BYTES"]
    path = Path(image_path)

    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode == "P" and "transparency" in image.info:
            image = image.convert("RGBA")
        image.thumbnail((max_side, max_side))
        if image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")

        save_path = path
        save_kwargs = {}
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            save_kwargs = {"quality": 88, "optimize": True}
        else:
            save_kwargs = {"optimize": True}
        image.save(save_path, **save_kwargs)

    if path.stat().st_size <= max_bytes:
        return

    with Image.open(path) as image:
        image = image.convert("RGB")
        quality = 82
        while quality >= 55:
            image.save(path, quality=quality, optimize=True)
            if path.stat().st_size <= max_bytes:
                break
            quality -= 8
