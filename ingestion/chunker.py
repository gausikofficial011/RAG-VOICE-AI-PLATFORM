"""
Structure-Aware Document Chunker
Splits parsed documents into overlapping chunks preserving sentence boundaries, headings, and page numbers.
Tracks complete provenance for evidence grounding.
"""

from typing import Any, Dict, List
import re
from ingestion.parser import ParsedPage


class Chunk:
    def __init__(
        self,
        chunk_index: int,
        content: str,
        page_number: int,
        section: str,
        token_count: int,
        chunk_metadata: Dict[str, Any] = None,
    ):
        self.chunk_index = chunk_index
        self.content = content
        self.page_number = page_number
        self.section = section
        self.token_count = token_count
        self.chunk_metadata = chunk_metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "content": self.content,
            "page_number": self.page_number,
            "section": self.section,
            "token_count": self.token_count,
            "chunk_metadata": self.chunk_metadata,
        }


class StructureAwareChunker:
    def __init__(self, target_chunk_size: int = 500, chunk_overlap: int = 80):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split on sentence terminals while keeping punctuation
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_pages(self, pages: List[ParsedPage]) -> List[Chunk]:
        chunks: List[Chunk] = []
        global_index = 0

        for page in pages:
            sentences = self._split_into_sentences(page.text)
            if not sentences:
                continue

            current_chunk_sentences: List[str] = []
            current_len = 0

            for sent in sentences:
                sent_len = len(sent)
                if current_len + sent_len > self.target_chunk_size and current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    token_approx = len(chunk_text.split())
                    chunks.append(
                        Chunk(
                            chunk_index=global_index,
                            content=chunk_text,
                            page_number=page.page_number,
                            section=page.section,
                            token_count=token_approx,
                            chunk_metadata={"has_tables": len(page.tables) > 0},
                        )
                    )
                    global_index += 1

                    # Retain overlap sentences
                    overlap_sentences: List[str] = []
                    overlap_len = 0
                    for s in reversed(current_chunk_sentences):
                        if overlap_len + len(s) <= self.chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_len += len(s)
                        else:
                            break
                    current_chunk_sentences = overlap_sentences
                    current_len = overlap_len

                current_chunk_sentences.append(sent)
                current_len += sent_len

            # Flush remaining sentences for the page
            if current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                token_approx = len(chunk_text.split())
                chunks.append(
                    Chunk(
                        chunk_index=global_index,
                        content=chunk_text,
                        page_number=page.page_number,
                        section=page.section,
                        token_count=token_approx,
                        chunk_metadata={"has_tables": len(page.tables) > 0},
                    )
                )
                global_index += 1

        return chunks


chunker = StructureAwareChunker()
