from app.rag.models import RAGChunk, RAGDocument


class DocumentChunker:
    """
    Splits RAG documents into deterministic, retrieval-ready chunks.

    Chunk boundaries prefer existing line boundaries so structured API
    context is not arbitrarily split in the middle of a semantic section.
    """

    def __init__(self, max_chunk_size: int = 1000) -> None:
        if max_chunk_size <= 0:
            raise ValueError("Maximum chunk size must be positive.")

        self.max_chunk_size = max_chunk_size

    def chunk(self, document: RAGDocument) -> list[RAGChunk]:
        """
        Split a RAG document into chunks while preserving its metadata.
        """

        sections = [
            section.strip()
            for section in document.content.splitlines()
            if section.strip()
        ]

        if not sections:
            return []

        chunk_contents = self._build_chunks(sections)

        return [
            self._create_chunk(
                document=document,
                content=content,
                chunk_index=index,
            )
            for index, content in enumerate(chunk_contents)
        ]

    def _build_chunks(self, sections: list[str]) -> list[str]:
        chunks: list[str] = []
        current_sections: list[str] = []
        current_length = 0

        for section in sections:
            if len(section) > self.max_chunk_size:
                if current_sections:
                    chunks.append("\n".join(current_sections))
                    current_sections = []
                    current_length = 0

                chunks.extend(self._split_large_section(section))
                continue

            separator_length = 1 if current_sections else 0
            proposed_length = current_length + separator_length + len(section)

            if proposed_length > self.max_chunk_size:
                chunks.append("\n".join(current_sections))
                current_sections = [section]
                current_length = len(section)
            else:
                current_sections.append(section)
                current_length = proposed_length

        if current_sections:
            chunks.append("\n".join(current_sections))

        return chunks

    def _split_large_section(self, section: str) -> list[str]:
        """
        Split an individual oversized section safely on word boundaries.
        """

        words = section.split()

        chunks: list[str] = []
        current_words: list[str] = []
        current_length = 0

        for word in words:
            if len(word) > self.max_chunk_size:
                if current_words:
                    chunks.append(" ".join(current_words))
                    current_words = []
                    current_length = 0

                chunks.extend(self._split_oversized_word(word))
                continue

            separator_length = 1 if current_words else 0
            proposed_length = current_length + separator_length + len(word)

            if proposed_length > self.max_chunk_size:
                chunks.append(" ".join(current_words))
                current_words = [word]
                current_length = len(word)
            else:
                current_words.append(word)
                current_length = proposed_length

        if current_words:
            chunks.append(" ".join(current_words))

        return chunks

    def _split_oversized_word(self, word: str) -> list[str]:
        """
        Handle pathological tokens longer than the configured chunk size.
        """

        return [
            word[index : index + self.max_chunk_size]
            for index in range(0, len(word), self.max_chunk_size)
        ]

    def _create_chunk(
        self,
        document: RAGDocument,
        content: str,
        chunk_index: int,
    ) -> RAGChunk:
        return RAGChunk(
            content=content,
            specification_id=document.specification_id,
            endpoint_id=document.endpoint_id,
            chunk_index=chunk_index,
            path=document.path,
            method=document.method,
            operation_id=document.operation_id,
            metadata=dict(document.metadata),
        )
