"""
Clause chunker - splits long clauses into smaller chunks
"""

from typing import List, Dict, Any
import config


class ClauseChunker:
    """Split clauses into manageable chunks for embedding"""

    def chunk(self, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk clauses for embedding

        Args:
            clauses: List of parsed clauses

        Returns:
            List of chunked clauses (may be more than input if split)
        """
        chunked = []

        for clause in clauses:
            text = clause["text"]

            # If clause is small enough, keep as-is
            if len(text) <= config.CHUNK_SIZE:
                chunked.append(clause)
            else:
                # Split into smaller chunks
                chunks = self._split_text(text, config.CHUNK_SIZE)

                for idx, chunk_text in enumerate(chunks):
                    chunked_clause = clause.copy()
                    chunked_clause["text"] = chunk_text
                    chunked_clause["clause_id"] = f"{clause['clause_id']}_part{idx + 1}"
                    chunked_clause["metadata"] = {
                        **clause.get("metadata", {}),
                        "is_chunk": True,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "original_clause_id": clause["clause_id"],
                    }
                    chunked.append(chunked_clause)

        return chunked

    def _split_text(self, text: str, max_size: int) -> List[str]:
        """
        Split text into chunks at sentence boundaries

        Args:
            text: Text to split
            max_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        # Split by sentences
        sentences = text.replace("\n", " ").split(". ")

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add period back if it was removed
            if not sentence.endswith("."):
                sentence += "."

            sentence_size = len(sentence)

            # If adding this sentence exceeds max_size, start new chunk
            if current_size + sentence_size > max_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
