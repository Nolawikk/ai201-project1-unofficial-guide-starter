import os
import re

# ── Config ──────────────────────────────────────────────────────────────────
DOCUMENTS_DIR = "documents"
CHUNK_SIZE = 400       # characters
OVERLAP = 80           # characters


# ── Cleaning ─────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Remove HTML, boilerplate, and noise from raw document text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove Reddit usernames (u/username)
    text = re.sub(r"u/\w+", "", text)
    # Remove Reddit vote counts and timestamps (e.g. "1.2k points", "6y ago", "3h ago")
    text = re.sub(r"\d+\.?\d*k? points?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+ comments?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+[ydhm] ago", "", text, flags=re.IGNORECASE)
    # Remove Reddit UI artifacts (avatar, share, reply, etc.)
    text = re.sub(r"\b(avatar|share|reply|report|save|follow|edit|delete|permalink)\b", "", text, flags=re.IGNORECASE)
    # Remove PDF artifacts: rows of dots, page numbers, stray numbers on their own line
    text = re.sub(r"\.{3,}", "", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    # Remove lines that are just punctuation or 1-2 characters
    text = re.sub(r"^\s*[\W]{1,3}\s*$", "", text, flags=re.MULTILINE)
    # Remove repeated whitespace and blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ── Chunking ──────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Split text into chunks using paragraph boundaries first.
    If a paragraph exceeds chunk_size, fall back to fixed-character splitting with overlap.
    Filters out empty or very short chunks.
    """
    chunks = []
    paragraphs = text.split("\n\n")

    current_chunk = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If paragraph fits in remaining space, add it
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = (current_chunk + "\n\n" + para).strip()
        else:
            # Save current chunk if it has content
            if len(current_chunk) > 50:
                chunks.append(current_chunk)

            # If paragraph itself is larger than chunk_size, split it
            if len(para) > chunk_size:
                start = 0
                while start < len(para):
                    end = start + chunk_size
                    chunks.append(para[start:end].strip())
                    start += chunk_size - overlap
            else:
                current_chunk = para

    # Don't forget the last chunk
    if len(current_chunk) > 50:
        chunks.append(current_chunk)

    return [c for c in chunks if len(c) > 50]


# ── Load and process all documents ───────────────────────────────────────────
def load_documents(directory: str) -> list[dict]:
    """Load all files from the documents directory."""
    documents = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and not filename.startswith("."):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
                documents.append({
                    "filename": filename,
                    "raw_text": raw_text
                })
                print(f"Loaded: {filename} ({len(raw_text)} chars)")
            except Exception as e:
                print(f"Could not load {filename}: {e}")
    return documents


def ingest(directory: str = DOCUMENTS_DIR) -> list[dict]:
    """Full pipeline: load → clean → chunk → return list of chunk dicts."""
    documents = load_documents(directory)
    all_chunks = []

    for doc in documents:
        cleaned = clean_text(doc["raw_text"])
        chunks = chunk_text(cleaned)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["filename"],
                "chunk_index": i
            })

    return all_chunks


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chunks = ingest()

    print(f"\n{'='*50}")
    print(f"Total chunks: {len(chunks)}")
    print(f"{'='*50}\n")

    # Print 5 sample chunks for inspection
    print("── 5 Sample Chunks ──\n")
    import random
    samples = random.sample(chunks, min(5, len(chunks)))
    for i, chunk in enumerate(samples):
        print(f"[Chunk {i+1}] Source: {chunk['source']} | Index: {chunk['chunk_index']}")
        print(chunk["text"])
        print()
