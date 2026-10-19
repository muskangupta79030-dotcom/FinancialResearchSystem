import re

from backend.services.embeddings import generate_embeddings
from backend.services.vector_store import search_documents


class ResearchAgent:
    """
    Research Agent for answering financial questions
    using information retrieved from indexed financial documents.
    """

    def research(self, query, top_k=5, filename=None):
        """
        Retrieve relevant financial document chunks and
        generate a grounded answer from the retrieved sources.
        """

        # =========================================================
        # STEP 1: Validate query
        # =========================================================

        if not query or not query.strip():
            return {
                "status": "error",
                "message": "Research query cannot be empty.",
                "query": query,
                "answer": "",
                "sources": []
            }

        query = query.strip()

        # =========================================================
        # STEP 2: Generate query embedding
        # =========================================================

        query_embedding = generate_embeddings([query])[0]

        # =========================================================
        # STEP 3: Retrieve relevant document chunks
        # =========================================================

        retrieved_chunks = search_documents(
            query_embedding=query_embedding,
            top_k=top_k,
            filename=filename
        )

        # =========================================================
        # STEP 4: Handle no results
        # =========================================================

        if not retrieved_chunks:
            return {
                "status": "no_results",
                "message": (
                    "No relevant information was found "
                    "in the indexed financial documents."
                ),
                "query": query,
                "answer": "",
                "sources": []
            }

        # =========================================================
        # STEP 5: Generate grounded answer
        # =========================================================

        answer = self._generate_answer(
            query,
            retrieved_chunks
        )

        # =========================================================
        # STEP 6: Prepare source citations
        # =========================================================

        sources = []

        for index, item in enumerate(retrieved_chunks, start=1):

            sources.append(
                {
                    "source_id": f"S{index}",
                    "filename": item.get(
                        "filename",
                        "Unknown"
                    ),
                    "chunk_index": item.get(
                        "chunk_index",
                        -1
                    ),
                    "relevance_distance": item.get(
                        "distance",
                        None
                    ),
                    "content": item.get(
                        "document",
                        ""
                    )
                }
            )

        # =========================================================
        # STEP 7: Final response
        # =========================================================

        return {
            "status": "success",
            "query": query,
            "answer": answer,
            "retrieved_chunks": len(retrieved_chunks),
            "sources": sources
        }

    # =============================================================
    # ANSWER GENERATION
    # =============================================================

    def _generate_answer(
        self,
        query,
        retrieved_chunks
    ):
        """
        Generate an answer using retrieved document content only.
        Exact financial-statement values are prioritized over
        approximate narrative values.
        """

        query_lower = query.lower()

        # ---------------------------------------------------------
        # Revenue / Net Sales
        # ---------------------------------------------------------

        if any(
            keyword in query_lower
            for keyword in [
                "revenue",
                "net sales",
                "total sales"
            ]
        ):

            answer = self._find_revenue_answer(
                retrieved_chunks
            )

            if answer:
                return answer

        # ---------------------------------------------------------
        # Net Income / Net Profit
        # ---------------------------------------------------------

        if any(
            keyword in query_lower
            for keyword in [
                "net income",
                "net profit",
                "profit after tax"
            ]
        ):

            answer = self._find_net_income_answer(
                retrieved_chunks
            )

            if answer:
                return answer

        # ---------------------------------------------------------
        # Operating Income / Operating Profit
        # ---------------------------------------------------------

        if any(
            keyword in query_lower
            for keyword in [
                "operating income",
                "operating profit"
            ]
        ):

            answer = self._find_operating_income_answer(
                retrieved_chunks
            )

            if answer:
                return answer

        # ---------------------------------------------------------
        # Generic research question
        # ---------------------------------------------------------

        best_source = retrieved_chunks[0]

        content = best_source.get(
            "document",
            ""
        ).strip()

        if content:

            if len(content) > 1200:
                content = content[:1200] + "..."

            return (
                "Based on the indexed financial document, "
                "the most relevant information is:\n\n"
                + content
                + "\n\n[Source: S1]"
            )

        return (
            "Relevant information was retrieved from the "
            "indexed financial documents, but a specific "
            "answer could not be extracted."
        )

    # =============================================================
    # REVENUE EXTRACTION
    # =============================================================

    def _find_revenue_answer(
        self,
        retrieved_chunks
    ):
        """
        Find exact revenue / net sales information.

        Priority:
        1. Consolidated financial statement
        2. Net Sales table
        3. Narrative revenue statement
        """

        # =========================================================
        # PASS 1: Exact financial statement
        # =========================================================

        for index, item in enumerate(
            retrieved_chunks,
            start=1
        ):

            text = item.get(
                "document",
                ""
            )

            if not text:
                continue

            # -----------------------------------------------------
            # Total net sales:
            # 574,785 637,959 716,924
            # -----------------------------------------------------

            pattern = re.search(
                r"Total\s+net\s+sales\s+"
                r"\$?\s*([\d,]+)\s+"
                r"\$?\s*([\d,]+)\s+"
                r"\$?\s*([\d,]+)",
                text,
                re.IGNORECASE
            )

            if pattern:

                values = pattern.groups()

                return (
                    "According to Amazon's 2025 annual report, "
                    "total net sales in 2025 were "
                    f"${values[-1]} million "
                    f"(${self._million_to_billion(values[-1])} billion). "
                    f"[Source: S{index}]"
                )

        # =========================================================
        # PASS 2: Consolidated Net Sales table
        # =========================================================

        for index, item in enumerate(
            retrieved_chunks,
            start=1
        ):

            text = item.get(
                "document",
                ""
            )

            if not text:
                continue

            # -----------------------------------------------------
            # Consolidated $ 637,959 $ 716,924
            # -----------------------------------------------------

            pattern = re.search(
                r"Consolidated\s+\$?\s*"
                r"([\d,]+)\s+\$?\s*"
                r"([\d,]+)",
                text,
                re.IGNORECASE
            )

            if pattern:

                values = pattern.groups()

                return (
                    "According to Amazon's 2025 annual report, "
                    "consolidated net sales in 2025 were "
                    f"${values[-1]} million "
                    f"(${self._million_to_billion(values[-1])} billion). "
                    f"[Source: S{index}]"
                )

        # =========================================================
        # PASS 3: Narrative approximate revenue
        # =========================================================

        for index, item in enumerate(
            retrieved_chunks,
            start=1
        ):

            text = item.get(
                "document",
                ""
            )

            if not text:
                continue

            pattern = re.search(
                r"revenue\s+in\s+2025.*?"
                r"from\s+\$?[\d.]+\s*billion\s+to\s+"
                r"\$?([\d.]+)\s*billion",
                text,
                re.IGNORECASE |
                re.DOTALL
            )

            if pattern:

                revenue = pattern.group(1)

                return (
                    "According to Amazon's 2025 annual report, "
                    "revenue in 2025 was approximately "
                    f"${revenue} billion. "
                    f"[Source: S{index}]"
                )

        return None

    # =============================================================
    # NET INCOME EXTRACTION
    # =============================================================

    def _find_net_income_answer(
        self,
        retrieved_chunks
    ):
        """
        Find exact net income from the consolidated
        financial statements.
        """

        # =========================================================
        # PASS 1: Exact Net Income financial statement
        # =========================================================

        for index, item in enumerate(
            retrieved_chunks,
            start=1
        ):

            text = item.get(
                "document",
                ""
            )

            if not text:
                continue

            pattern = re.search(
                r"Net\s+income\s+"
                r"\$?\s*([\d,]+)\s+"
                r"\$?\s*([\d,]+)\s+"
                r"\$?\s*([\d,]+)",
                text,
                re.IGNORECASE
            )

            if pattern:

                values = pattern.groups()

                return (
                    "According to Amazon's 2025 annual report, "
                    "net income in 2025 was "
                    f"${values[-1]} million "
                    f"(${self._million_to_billion(values[-1])} billion). "
                    f"[Source: S{index}]"
                )

        # =========================================================
        # PASS 2: Simpler net income pattern
        # =========================================================

        for index, item in enumerate(
            retrieved_chunks,
            start=1
        ):

            text = item.get(
                "document",
                ""
            )

            if not text:
                continue

            pattern = re.search(
                r"net\s+income.*?"
                r"([\d,]+)\s+"
                r"([\d,]+)\s+"
                r"([\d,]+)",
                text,
                re.IGNORECASE |
                re.DOTALL
            )

            if pattern:

                values = pattern.groups()

                return (
                    "According to the indexed financial "
                    "document, net income in 2025 was "
                    f"${values[-1]} million. "
                    f"[Source: S{index}]"
                )

        return None

    # =============================================================
    # OPERATING INCOME EXTRACTION
    # =============================================================

    def _find_operating_income_answer(
        self,
        retrieved_chunks
    ):
        """
        Find exact operating income from the financial statement.
        """

        for index, item in enumerate(
            retrieved_chunks,
            start=1
        ):

            text = item.get(
                "document",
                ""
            )

            if not text:
                continue

            pattern = re.search(
                r"Operating\s+income\s+"
                r"([\d,]+)\s+"
                r"([\d,]+)\s+"
                r"([\d,]+)",
                text,
                re.IGNORECASE
            )

            if pattern:

                values = pattern.groups()

                return (
                    "According to Amazon's 2025 annual report, "
                    "operating income in 2025 was "
                    f"${values[-1]} million "
                    f"(${self._million_to_billion(values[-1])} billion). "
                    f"[Source: S{index}]"
                )

        return None

    # =============================================================
    # MILLION TO BILLION
    # =============================================================

    def _million_to_billion(
        self,
        value
    ):
        """
        Convert millions to billions.
        """

        try:

            number = float(
                value.replace(",", "")
            )

            return f"{number / 1000:.3f}"

        except (
            ValueError,
            AttributeError
        ):

            return value
