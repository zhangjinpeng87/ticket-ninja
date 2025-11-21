import re
from typing import List
from bs4 import BeautifulSoup


class ContentProcessor:
    """Responsible for turning fetched HTML/XML into clean text chunks."""

    STRIP_TAGS = ["script", "style", "nav", "header", "footer", "noscript", "aside"]

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in self.STRIP_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
        if not text:
            return []

        words = text.split()
        if len(words) <= chunk_size:
            return [" ".join(words)]

        chunks: List[str] = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = words[start:end]
            chunks.append(" ".join(chunk))
            if end == len(words):
                break
            start = max(end - overlap, 0)
        return chunks

    def summarize(self, text: str, max_sentences: int = 2) -> str:
        sentences = re.split(r"(?<=[.!?]) +", text)
        summary = " ".join(sentences[:max_sentences]).strip()
        return summary or text[:200]

    def chunk_to_solutions(self, text: str, max_items: int = 3) -> List[str]:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text]
        return paragraphs[:max_items]

