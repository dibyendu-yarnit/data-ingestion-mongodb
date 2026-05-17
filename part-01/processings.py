from typing import Any



class RecursiveCharacterSplitter:
    """
        Pure-Python recursive character text splitter with configurable chunk size, overlap, and separator hierarchy.
    """

    # Default separators: try to split on paragraphs, then lines, then sentences, then words, then characters.
    DEFAULT_SEPARATORS: list[str] = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        try:
            if not isinstance(chunk_size, int) or chunk_size <= 0:
                raise ValueError(f"chunk_size must be a positive integer, got: {chunk_size}")
            
            if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
                raise ValueError(f"chunk_overlap must be a non-negative integer, got: {chunk_overlap}")
            
            if chunk_overlap >= chunk_size:
                raise ValueError(
                    f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
                )

            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.separators = separators if separators is not None else self.DEFAULT_SEPARATORS

        except ValueError:
            raise

        except Exception as exc:
            raise RuntimeError(f"Failed to initialize RecursiveCharacterSplitter: {exc}") from exc


    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """
            Recursively split ``text`` using ``separators``.

            Tries the first separator; any resulting piece that still exceeds
            ``chunk_size`` is passed back recursively with the remaining
            separators. The empty-string separator acts as a character-level
            fallback that always succeeds.
        """
        try:
            if not text:
                return []

            separator = separators[0]
            remaining = separators[1:]

            if separator == "":
                # Character-level split — hard-chop into chunk_size pieces.
                return [text[i: i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

            raw_splits = text.split(separator)
            pieces: list[str] = []
            current = ""

            for part in raw_splits:
                candidate = (current + separator + part).lstrip(separator) if current else part
                if len(candidate) <= self.chunk_size:
                    current = candidate
                
                else:
                    if current:
                        pieces.append(current)
                    # Part alone is too big — recurse with finer separators.
                    if len(part) > self.chunk_size and remaining:
                        pieces.extend(self._split_text(part, remaining))
                    
                    else:
                        current = part

            if current:
                pieces.append(current)

            return [p for p in pieces if p.strip()]

        except RecursionError:
            return [text[i: i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        except Exception as exc:
            raise


    def _apply_overlap(self, pieces: list[str]) -> list[str]:
        """
            Stitch an overlap tail from each chunk into the beginning of the next.
        """
        try:
            if len(pieces) <= 1 or self.chunk_overlap == 0:
                return pieces

            result: list[str] = [pieces[0]]
            for i in range(1, len(pieces)):
                tail = result[-1][-self.chunk_overlap:]
                merged = tail + pieces[i]
                result.append(merged)

            return result

        except Exception as exc:
            raise


    def split_text(self, text: str) -> list[str]:
        """
            Split a single string into overlapping chunks.
        """
        try:
            if not text or not text.strip():
                return []

            pieces = self._split_text(text, self.separators)
            chunks = self._apply_overlap(pieces)

            return chunks

        except Exception as exc:
            raise


    def split_documents(
        self,
        documents: list[dict],
        extra_metadata: dict[str, Any] | None = None,
    ) -> list[dict]:
        """
            Split a list of page dicts (output of PDFLoader.load) into chunks.

            Each page dict must have ``"content"`` and ``"metadata"`` keys.
            ``extra_metadata`` is merged into every chunk's metadata, letting
            callers attach document-level tags (e.g. kb_id, doc_title).

            Returns a list of chunk dicts:
                {
                    "content":     str,
                    "chunk_index": int,   # global index across all pages
                    "token_count": int,   # word-based approximation
                    "metadata":    dict,  # page meta + extra_metadata + chunk_index
                }
        """
        try:
            if not documents:
                return []

            extra = extra_metadata or {}
            chunks: list[dict] = []
            global_index = 0
            skipped_pages = 0

        
            for page_num, doc in enumerate(documents, start=1):
                try:
                    page_content: str = doc.get("content", "").strip()
                    page_meta: dict = doc.get("metadata", {})

                    if not page_content:
                        skipped_pages += 1
                        continue

                    pieces = self.split_text(page_content)

                    for piece in pieces:
                        piece = piece.strip()
                        if not piece:
                            continue

                        chunk_meta = {**page_meta, **extra, "chunk_index": global_index}
                        chunks.append({
                            "content": piece,
                            "chunk_index": global_index,
                            "token_count": len(piece.split()),
                            "metadata": chunk_meta,
                        })
                        global_index += 1

                except Exception as page_exc:
                    skipped_pages += 1
           
            return chunks

        except Exception as exc:
            raise



# Global instance of RecursiveCharacterSplitter
text_splitter = RecursiveCharacterSplitter()