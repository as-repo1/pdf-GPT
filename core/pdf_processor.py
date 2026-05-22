"""
PDF text extraction and chunking utilities.
Supports multiple PDF uploads, page-labelled text, and smart splitting.
"""

import io
from typing import List

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_text_from_pdfs(pdf_files) -> str:
    """
    Extract and concatenate text from one or more uploaded PDF file objects.
    Each page is prefixed with [filename — Page N] for traceability.
    """
    all_parts: List[str] = []

    for pdf_file in pdf_files:
        # Support both UploadedFile (getvalue) and raw file objects (read)
        content = (
            pdf_file.getvalue()
            if hasattr(pdf_file, "getvalue")
            else pdf_file.read()
        )
        reader = PdfReader(io.BytesIO(content))
        file_parts: List[str] = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                file_parts.append(
                    f"[{pdf_file.name} — Page {i + 1}]\n{text.strip()}"
                )

        if file_parts:
            all_parts.append("\n\n".join(file_parts))

    return "\n\n".join(all_parts)


def split_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Split extracted text into overlapping chunks suitable for embedding.
    Uses RecursiveCharacterTextSplitter for natural boundary preservation.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if c.strip()]
