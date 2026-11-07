from pathlib import Path
from pypdf import PdfReader
from docx import Document

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

def extract_text(path: str) -> tuple[str, list[str]]:
    p = Path(path)
    ext = p.suffix.lower()
    warnings = []
    try:
        if ext == ".pdf":
            reader = PdfReader(str(p))
            text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
            if not text:
                text = _ocr_pdf(reader, warnings)
            return text, warnings
        if ext == ".docx":
            doc = Document(str(p))
            parts = [x.text for x in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            return "\n".join(parts).strip(), warnings
        if ext in {".txt", ".csv", ".md"}:
            return p.read_text(encoding="utf-8", errors="ignore")[:100000], warnings
        if ext in IMAGE_EXTS:
            return _ocr_image_or_pdf(path, warnings), warnings
    except Exception as exc:
        warnings.append(f"Text extraction warning: {exc}")
    return "", warnings

def _ocr_pdf(reader, warnings: list[str]) -> str:
    """OCR the images embedded in a scanned PDF (first 10 pages)."""
    try:
        import io
        import pytesseract
        from PIL import Image
        parts = []
        for page in reader.pages[:10]:
            for img in page.images:
                parts.append(pytesseract.image_to_string(Image.open(io.BytesIO(img.data))))
        text = "\n".join(parts).strip()[:100000]
        if not text:
            warnings.append("No readable text found in this PDF, even after OCR.")
        return text
    except Exception:
        warnings.append("OCR was unavailable. Install Tesseract OCR and ensure it is on PATH for scanned files.")
        return ""

def _ocr_image_or_pdf(path: str, warnings: list[str]) -> str:
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(path)
        return pytesseract.image_to_string(image)[:100000].strip()
    except Exception:
        warnings.append("OCR was unavailable. Install Tesseract OCR and ensure it is on PATH for scanned files.")
        return ""
