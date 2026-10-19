import re


class ExtractionAgent:
    """
    Financial Extraction Agent

    Extracts:
    - Revenue
    - Net Income
    - Operating Profit

    Designed for annual-report PDF text extracted using pypdf.
    """

    def extract_metrics(self, text):

        if not text:
            return {}

        text = self._normalize_text(text)

        metrics = {}

        # ---------------------------------------------------------
        # REVENUE
        # ---------------------------------------------------------

        revenue = self._extract_revenue(text)

        if revenue:
            metrics["revenue"] = revenue["value"]
            metrics["revenue_source"] = revenue["source"]

        # ---------------------------------------------------------
        # NET INCOME
        # ---------------------------------------------------------

        net_income = self._extract_net_income(text)

        if net_income:
            metrics["net_income"] = net_income["value"]
            metrics["net_income_source"] = net_income["source"]

        # ---------------------------------------------------------
        # OPERATING PROFIT
        # ---------------------------------------------------------

        operating_profit = self._extract_operating_profit(text)

        if operating_profit:
            metrics["operating_profit"] = operating_profit["value"]
            metrics["operating_profit_source"] = operating_profit["source"]

        return metrics

    # ============================================================
    # FIND CONSOLIDATED FINANCIAL STATEMENT
    # ============================================================

    @staticmethod
    def _find_statement_blocks(text):

        headings = [
            r"consolidated\s+statements?\s+of\s+operations",
            r"consolidated\s+statement\s+of\s+profit\s+and\s+loss",
            r"consolidated\s+statements?\s+of\s+profit\s+and\s+loss",
            r"consolidated\s+income\s+statement",
            r"statement\s+of\s+profit\s+and\s+loss",
            r"statement\s+of\s+operations"
        ]

        blocks = []

        for heading in headings:

            matches = list(
                re.finditer(
                    heading,
                    text,
                    re.IGNORECASE
                )
            )

            for match in matches:

                start = match.start()

                end = min(
                    len(text),
                    start + 12000
                )

                block = text[start:end]

                lower = block.lower()

                score = 0

                if "year ended" in lower:
                    score += 10

                if "net income" in lower:
                    score += 10

                if "operating income" in lower:
                    score += 10

                if "operating profit" in lower:
                    score += 10

                if "total net sales" in lower:
                    score += 10

                if "revenue" in lower:
                    score += 5

                blocks.append(
                    {
                        "score": score,
                        "text": block
                    }
                )

        blocks.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return [
            item["text"]
            for item in blocks
        ]

    # ============================================================
    # REVENUE
    # ============================================================

    def _extract_revenue(self, text):

        blocks = self._find_statement_blocks(text)

        search_texts = blocks if blocks else [text]

        patterns = [
            r"\btotal\s+net\s+sales\b",
            r"\btotal\s+revenue\b",
            r"\btotal\s+revenues\b",
            r"\brevenue\s+from\s+operations\b",
            r"\brevenues\b"
        ]

        for block in search_texts:

            for pattern in patterns:

                match = re.search(
                    pattern,
                    block,
                    re.IGNORECASE
                )

                if not match:
                    continue

                context_before = block[
                    max(0, match.start() - 500):
                    match.start()
                ]

                if re.search(
                    r"unearned\s+revenue|deferred\s+revenue",
                    context_before,
                    re.IGNORECASE
                ):
                    continue

                row = self._get_row_after_label(
                    block,
                    match.end(),
                    [
                        r"\boperating\s+expenses?\b",
                        r"\bcost\s+of\s+sales\b",
                        r"\bcost\s+of\s+revenue\b",
                        r"\boperating\s+income\b",
                        r"\boperating\s+profit\b",
                        r"\boperating\s+margin\b",
                        r"\bprofit\s+before\s+tax\b",
                        r"\bprofit\s+after\s+tax\b",
                        r"\bnet\s+income\b"
                    ]
                )

                values = self._numbers(row)

                if not values:
                    continue

                value = self._latest_value(
                    values,
                    block
                )

                return {
                    "value": self._format(value),
                    "source": self._source(
                        block,
                        match.start(),
                        row
                    )
                }

        return self._fallback_revenue(text)

    # ============================================================
    # NET INCOME
    # ============================================================

    def _extract_net_income(self, text):

        blocks = self._find_statement_blocks(text)

        # --------------------------------------------------------
        # FIRST: STRICT CONSOLIDATED OPERATIONS STATEMENT
        # --------------------------------------------------------

        for block in blocks:

            # Ignore blocks that clearly belong to cash-flow
            # statements when looking for the main net income row.
            block_lower = block.lower()

            if (
                "cash flows" in block_lower
                and "total net sales" not in block_lower
                and "operating income" not in block_lower
            ):
                continue

            # ----------------------------------------------------
            # AMAZON / US-STYLE:
            #
            # Net income
            # 30,425 59,248 77,670
            # ----------------------------------------------------

            matches = list(
                re.finditer(
                    r"\bnet\s+income\b",
                    block,
                    re.IGNORECASE
                )
            )

            for match in matches:

                row = self._get_row_after_label(
                    block,
                    match.end(),
                    [
                        r"\badjustments?\s+to\s+reconcile\b",
                        r"\bdepreciation\s+and\s+amortization\b",
                        r"\boperating\s+activities\b",
                        r"\bcash\s+flows?\b",
                        r"\bbasic\s+earnings\s+per\s+share\b",
                        r"\bdiluted\s+earnings\s+per\s+share\b",
                        r"\bearnings\s+per\s+share\b",
                        r"\bother\s+comprehensive\s+income\b",
                        r"\btotal\s+comprehensive\s+income\b"
                    ]
                )

                values = self._numbers(row)

                # A valid annual-report net-income row should
                # normally contain 1 or more meaningful values.
                if not values:
                    continue

                # ------------------------------------------------
                # IMPORTANT:
                #
                # For Amazon:
                #
                # 2023  2024  2025
                # 30,425 59,248 77,670
                #
                # We want the LAST value.
                # ------------------------------------------------

                if len(values) >= 3:

                    value = values[-1]

                    return {
                        "value": self._format(value),
                        "source": self._source(
                            block,
                            match.start(),
                            row
                        )
                    }

                # If only one or two values are available,
                # use year-aware selection.
                value = self._latest_value(
                    values,
                    block
                )

                return {
                    "value": self._format(value),
                    "source": self._source(
                        block,
                        match.start(),
                        row
                    )
                }

        # --------------------------------------------------------
        # INDIAN ANNUAL-REPORT STYLE
        # --------------------------------------------------------

        for block in blocks:

            match = re.search(
                r"\bprofit\s+after\s+tax\b",
                block,
                re.IGNORECASE
            )

            if not match:
                continue

            row = self._get_row_after_label(
                block,
                match.end(),
                [
                    r"\bother\s+comprehensive\s+income\b",
                    r"\btotal\s+comprehensive\s+income\b",
                    r"\bearnings\s+per\s+share\b"
                ]
            )

            values = self._numbers(row)

            if not values:
                continue

            value = self._latest_value(
                values,
                block
            )

            return {
                "value": self._format(value),
                "source": self._source(
                    block,
                    match.start(),
                    row
                )
            }

        # --------------------------------------------------------
        # FALLBACK
        # --------------------------------------------------------

        return self._fallback_net_income(text)

    # ============================================================
    # OPERATING PROFIT
    # ============================================================

    def _extract_operating_profit(self, text):

        blocks = self._find_statement_blocks(text)

        search_texts = blocks if blocks else [text]

        patterns = [
            r"\boperating\s+income\b",
            r"\boperating\s+profit\b",
            r"\bprofit\s+from\s+operations\b"
        ]

        for block in search_texts:

            for pattern in patterns:

                match = re.search(
                    pattern,
                    block,
                    re.IGNORECASE
                )

                if not match:
                    continue

                context = block[
                    max(0, match.start() - 600):
                    match.start()
                ]

                lower_context = context.lower()

                segment_terms = [
                    "north america",
                    "international",
                    "aws",
                    "segment information",
                    "geographic information"
                ]

                if any(
                    term in lower_context
                    for term in segment_terms
                ):
                    continue

                row = self._get_row_after_label(
                    block,
                    match.end(),
                    [
                        r"\binterest\s+income\b",
                        r"\binterest\s+expense\b",
                        r"\bother\s+operating\s+(?:expense|income)\b",
                        r"\bother\s+income\b",
                        r"\bprofit\s+before\s+tax\b",
                        r"\bincome\s+before\s+income\s+tax(?:es)?\b",
                        r"\bnet\s+income\b"
                    ]
                )

                values = self._numbers(row)

                if not values:
                    continue

                value = self._latest_value(
                    values,
                    block
                )

                return {
                    "value": self._format(value),
                    "source": self._source(
                        block,
                        match.start(),
                        row
                    )
                }

        return self._fallback_operating_profit(text)

    # ============================================================
    # GET ROW AFTER LABEL
    # ============================================================

    @staticmethod
    def _get_row_after_label(
        text,
        start,
        stop_patterns
    ):

        end = min(
            len(text),
            start + 600
        )

        row = text[start:end]

        stop_positions = []

        for pattern in stop_patterns:

            match = re.search(
                pattern,
                row,
                re.IGNORECASE
            )

            if match:
                stop_positions.append(
                    match.start()
                )

        if stop_positions:

            row = row[
                :min(stop_positions)
            ]

        return row.strip()

    # ============================================================
    # NUMBER EXTRACTION
    # ============================================================

    @staticmethod
    def _numbers(text):

        pattern = re.compile(
            r"(?<![\w])"
            r"(\(?"
            r"(?:[$₹]|rs\.?|inr|usd)?"
            r"\s*"
            r"\d[\d,]*(?:\.\d+)?"
            r"\)?)"
            r"(?![\w])",
            re.IGNORECASE
        )

        values = []

        for match in pattern.finditer(text):

            raw = match.group(1)

            after = text[
                match.end():
                min(
                    len(text),
                    match.end() + 5
                )
            ]

            if re.match(
                r"\s*%",
                after
            ):
                continue

            cleaned = raw

            cleaned = re.sub(
                r"^(?:\$|₹|rs\.?|inr|usd)",
                "",
                cleaned,
                flags=re.IGNORECASE
            )

            negative = (
                cleaned.startswith("(")
                and cleaned.endswith(")")
            )

            cleaned = (
                cleaned
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
                .strip()
            )

            try:
                number = float(cleaned)
            except ValueError:
                continue

            # Ignore years.
            if 1900 <= abs(number) <= 2100:
                continue

            # Ignore very small PDF/OCR fragments.
            if abs(number) < 10:
                continue

            if negative:
                number = -number

            values.append(number)

        return values

    # ============================================================
    # LATEST VALUE
    # ============================================================

    @staticmethod
    def _latest_value(
        values,
        context
    ):

        if not values:
            return None

        if len(values) == 1:
            return values[0]

        years = [
            int(year)
            for year in re.findall(
                r"\b20\d{2}\b",
                context
            )
        ]

        unique_years = []

        for year in years:

            if year not in unique_years:
                unique_years.append(year)

        if len(unique_years) >= 2:

            if unique_years == sorted(
                unique_years
            ):
                return values[-1]

            if unique_years == sorted(
                unique_years,
                reverse=True
            ):
                return values[0]

        return values[-1]

    # ============================================================
    # FALLBACK REVENUE
    # ============================================================

    def _fallback_revenue(self, text):

        match = re.search(
            r"\brevenues?\s+(?:were|was|of|amounted\s+to)"
            r"\s+(?:₹|rs\.?|inr|\$|usd)?\s*"
            r"([\d,]+(?:\.\d+)?)",
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        value = float(
            match.group(1).replace(",", "")
        )

        return {
            "value": self._format(value),
            "source": match.group(0)
        }

    # ============================================================
    # FALLBACK NET INCOME
    # ============================================================

    def _fallback_net_income(self, text):

        match = re.search(
            r"\bnet\s+income\b"
            r".{0,250}?"
            r"(\d[\d,]*(?:\.\d+)?)"
            r".{0,150}?"
            r"(\d[\d,]*(?:\.\d+)?)"
            r".{0,150}?"
            r"(\d[\d,]*(?:\.\d+)?)",
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        values = [
            float(match.group(1).replace(",", "")),
            float(match.group(2).replace(",", "")),
            float(match.group(3).replace(",", ""))
        ]

        return {
            "value": self._format(values[-1]),
            "source": match.group(0)
        }

    # ============================================================
    # FALLBACK OPERATING PROFIT
    # ============================================================

    def _fallback_operating_profit(self, text):

        match = re.search(
            r"\boperating\s+(?:income|profit)\b"
            r".{0,250}?"
            r"(\d[\d,]*(?:\.\d+)?)"
            r".{0,150}?"
            r"(\d[\d,]*(?:\.\d+)?)"
            r".{0,150}?"
            r"(\d[\d,]*(?:\.\d+)?)",
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        values = [
            float(match.group(1).replace(",", "")),
            float(match.group(2).replace(",", "")),
            float(match.group(3).replace(",", ""))
        ]

        return {
            "value": self._format(values[-1]),
            "source": match.group(0)
        }

    # ============================================================
    # SOURCE
    # ============================================================

    @staticmethod
    def _source(
        text,
        position,
        row
    ):

        start = max(
            0,
            position - 180
        )

        prefix = text[
            start:position
        ]

        source = (
            prefix
            + " "
            + row
        )

        source = re.sub(
            r"\s+",
            " ",
            source
        ).strip()

        return source

    # ============================================================
    # NORMALIZE
    # ============================================================

    @staticmethod
    def _normalize_text(text):

        text = text.replace(
            "\u00a0",
            " "
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        text = re.sub(
            r"\n+",
            "\n",
            text
        )

        return text

    # ============================================================
    # FORMAT
    # ============================================================

    @staticmethod
    def _format(number):

        if number.is_integer():
            return f"{int(number):,}"

        return f"{number:,.2f}"
