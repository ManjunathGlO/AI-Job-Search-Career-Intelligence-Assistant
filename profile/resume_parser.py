from pathlib import Path

def extract_resume_text(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.read()
    if name.endswith(".txt") or name.endswith(".md"):
        return data.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            return f"PDF extraction failed: {e}"

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(uploaded_file)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"DOCX extraction failed: {e}"

    return ""
