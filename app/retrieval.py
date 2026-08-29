from pathlib import Path
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class DocumentChunk:
    text: str
    filename: str
    heading: str
    status: str
    authority: str
    score: float = 0.0


def get_document_metadata(filename: str):
    """
    Assign basic metadata based on the supplied knowledge-base files.
    """

    if filename == "01-returns-policy-current.md":
        return "active", "official"

    if filename == "02-returns-policy-legacy.md":
        return "superseded", "official"

    if filename == "14-internal-content-migration-notes.md":
        return "internal", "untrusted"

    return "active", "official"


def remove_front_matter(text: str) -> str:
    """
    Remove YAML front matter from a Markdown document.
    """

    text = text.strip()

    if text.startswith("---"):

        parts = text.split("---", 2)

        if len(parts) == 3:
            return parts[2].strip()

    return text


def load_documents(
    knowledge_base_path: str
) -> List[DocumentChunk]:
    """
    Load Markdown files from the knowledge-base directory
    and convert them into document chunks.
    """

    knowledge_base = Path(knowledge_base_path)

    chunks = []

    for file_path in sorted(knowledge_base.glob("*.md")):

        text = file_path.read_text(
            encoding="utf-8"
        )

        # Remove YAML front matter.
        text = remove_front_matter(text)

        status, authority = get_document_metadata(
            file_path.name
        )

        # Split using Markdown level-2 headings.
        sections = text.split("\n## ")

        for section in sections:

            section = section.strip()

            if not section:
                continue

            lines = section.splitlines()

            heading = lines[0].lstrip("#").strip()

            content = "\n".join(
                lines[1:]
            ).strip()

            if not content:
                continue

            chunks.append(
                DocumentChunk(
                    text=content,
                    filename=file_path.name,
                    heading=heading,
                    status=status,
                    authority=authority
                )
            )

    return chunks


class Retriever:

    def __init__(
        self,
        chunks: List[DocumentChunk]
    ):

        self.chunks = chunks

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english"
        )

        self.document_vectors = (
            self.vectorizer.fit_transform(
                [
                    self._prepare_text(chunk)
                    for chunk in chunks
                ]
            )
        )

    def _prepare_text(
        self,
        chunk: DocumentChunk
    ) -> str:
        """
        Combine useful information from a chunk
        before creating the TF-IDF representation.
        """

        return (
            f"{chunk.heading} "
            f"{chunk.filename} "
            f"{chunk.text}"
        )

    def detect_query_intent(
        self,
        query: str
    ) -> str:
        """
        Detect whether the query is about:
        - current information
        - historical information
        - TrailPlus
        """

        query_lower = query.lower()

        historical_words = historical_words = [
            "old policy",
            "old return policy",
            "legacy policy",
            "legacy version",
            "previous policy",
            "previous version",
            "former policy",
            "historical policy",
            "historical version",
            "earlier policy",
            "earlier version",
            "used to",
            "before april 2026",
        ]

        trailplus_words = [
            "trailplus",
            "trail plus",
            "membership",
            "member"
        ]

        if any(
            word in query_lower
            for word in historical_words
        ):
            return "historical"

        if any(
            word in query_lower
            for word in trailplus_words
        ):
            return "trailplus"

        return "current"

    def get_authority_bonus(
        self,
        chunk: DocumentChunk,
        intent: str
    ) -> float:
        """
        Adjust the retrieval score based on
        document status and query intent.
        """

        # Historical query
        if intent == "historical":

            if chunk.status == "superseded":
                return 0.30

            if chunk.status == "active":
                return -0.10

        # TrailPlus query
        elif intent == "trailplus":

            filename = chunk.filename.lower()
            heading = chunk.heading.lower()
            text = chunk.text.lower()

            trailplus_content = (
                "trailplus" in filename
                or "trailplus" in heading
                or "trailplus" in text
            )

            if trailplus_content:
                return 0.20

        # Current query
        else:

            if (
                chunk.status == "active"
                and chunk.authority == "official"
            ):
                return 0.10

            if chunk.status == "superseded":
                return -0.10

        # Untrusted content should be strongly
        # penalized regardless of query intent.
        if chunk.authority == "untrusted":
            return -0.50

        return 0.0

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[DocumentChunk]:
        """
        Search the knowledge base and return
        the most relevant chunks.
        """

        intent = self.detect_query_intent(
            query
        )

        query_vector = self.vectorizer.transform(
            [query]
        )

        scores = cosine_similarity(
            query_vector,
            self.document_vectors
        )[0]

        adjusted_scores = []

        for index, score in enumerate(scores):

            chunk = self.chunks[index]

            authority_bonus = (
                self.get_authority_bonus(
                    chunk,
                    intent
                )
            )

            final_score = (
                float(score)
                + authority_bonus
            )

            adjusted_scores.append(
                final_score
            )

        ranked_indices = sorted(
            range(len(adjusted_scores)),
            key=lambda i: adjusted_scores[i],
            reverse=True
        )

        print(
            f"Detected intent: {intent}"
        )

        results = []

        for index in ranked_indices[:top_k]:

            chunk = self.chunks[index]

            chunk.score = adjusted_scores[index]

            results.append(chunk)

        return results


if __name__ == "__main__":

    knowledge_base_path = "knowledge-base"

    chunks = load_documents(
        knowledge_base_path
    )

    print(
        f"Loaded {len(chunks)} document chunks.\n"
    )

    retriever = Retriever(chunks)

    while True:

        query = input(
            "\nEnter your question (or 'exit'): "
        )

        if query.lower().strip() == "exit":
            break

        results = retriever.search(
            query,
            top_k=5
        )

        print(
            "\nRelevant documents:\n"
        )

        for i, result in enumerate(
            results,
            start=1
        ):

            print(
                f"--- Result {i} ---"
            )

            print(
                f"File: {result.filename}"
            )

            print(
                f"Heading: {result.heading}"
            )

            print(
                f"Status: {result.status}"
            )

            print(
                f"Authority: {result.authority}"
            )

            print(
                f"Score: {result.score:.4f}"
            )

            print(
                f"Text: {result.text[:300]}..."
            )

            print()