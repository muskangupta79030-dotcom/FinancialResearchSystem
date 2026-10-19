import re


class RedFlagAgent:
    """
    Red Flag Agent

    Analyzes extracted financial metrics and annual-report text
    to identify potentially concerning financial patterns.

    The agent reports indicators for further review.
    It does not automatically conclude that a company has
    financial problems merely because a keyword appears.
    """

    def analyze(self, text, extracted_metrics=None):

        if extracted_metrics is None:
            extracted_metrics = {}

        text = text or ""

        red_flags = []
        observations = []

        # ---------------------------------------------------------
        # 1. Check important financial metrics
        # ---------------------------------------------------------

        important_metrics = [
            "revenue",
            "net_income",
            "operating_profit"
        ]

        missing_metrics = [
            metric
            for metric in important_metrics
            if metric not in extracted_metrics
        ]

        if missing_metrics:
            observations.append(
                "The following financial metrics were not detected: "
                + ", ".join(missing_metrics)
            )

        # ---------------------------------------------------------
        # 2. Revenue
        # ---------------------------------------------------------

        revenue = self._to_number(
            extracted_metrics.get("revenue")
        )

        if revenue is not None:

            if revenue < 0:

                red_flags.append({
                    "type": "Negative Revenue",
                    "severity": "High",
                    "message": (
                        "The extracted revenue value is negative "
                        "and requires review."
                    ),
                    "metric": "revenue",
                    "value": revenue
                })

            else:

                observations.append(
                    f"Revenue detected: {revenue:,.2f}"
                )

        # ---------------------------------------------------------
        # 3. Net Income
        # ---------------------------------------------------------

        net_income = self._to_number(
            extracted_metrics.get("net_income")
        )

        if net_income is not None:

            if net_income < 0:

                red_flags.append({
                    "type": "Negative Net Income",
                    "severity": "High",
                    "message": (
                        "The extracted net income is negative, "
                        "indicating a reported net loss."
                    ),
                    "metric": "net_income",
                    "value": net_income
                })

            else:

                observations.append(
                    f"Net income detected: {net_income:,.2f}"
                )

        # ---------------------------------------------------------
        # 4. Operating Profit
        # ---------------------------------------------------------

        operating_profit = self._to_number(
            extracted_metrics.get("operating_profit")
        )

        if operating_profit is not None:

            if operating_profit < 0:

                red_flags.append({
                    "type": "Negative Operating Profit",
                    "severity": "High",
                    "message": (
                        "Operating profit is negative, "
                        "indicating an operating loss."
                    ),
                    "metric": "operating_profit",
                    "value": operating_profit
                })

            else:

                observations.append(
                    f"Operating profit detected: "
                    f"{operating_profit:,.2f}"
                )

        # ---------------------------------------------------------
        # 5. Net Profit Margin
        # ---------------------------------------------------------

        if revenue is not None and net_income is not None:

            if revenue > 0:

                net_margin = (
                    net_income / revenue
                ) * 100

                observations.append(
                    f"Calculated net profit margin: "
                    f"{net_margin:.2f}%"
                )

                if net_margin < 0:

                    red_flags.append({
                        "type": "Negative Profit Margin",
                        "severity": "High",
                        "message": (
                            "The calculated net profit margin is negative."
                        ),
                        "metric": "net_profit_margin",
                        "value": round(net_margin, 2)
                    })

                elif net_margin < 5:

                    red_flags.append({
                        "type": "Low Profit Margin",
                        "severity": "Medium",
                        "message": (
                            "The calculated net profit margin "
                            "is below 5% and may require review."
                        ),
                        "metric": "net_profit_margin",
                        "value": round(net_margin, 2)
                    })

        # ---------------------------------------------------------
        # 6. Operating Margin
        # ---------------------------------------------------------

        if revenue is not None and operating_profit is not None:

            if revenue > 0:

                operating_margin = (
                    operating_profit / revenue
                ) * 100

                observations.append(
                    f"Calculated operating margin: "
                    f"{operating_margin:.2f}%"
                )

                if operating_margin < 0:

                    red_flags.append({
                        "type": "Negative Operating Margin",
                        "severity": "High",
                        "message": (
                            "The calculated operating margin is negative."
                        ),
                        "metric": "operating_margin",
                        "value": round(operating_margin, 2)
                    })

                elif operating_margin < 5:

                    red_flags.append({
                        "type": "Low Operating Margin",
                        "severity": "Medium",
                        "message": (
                            "The calculated operating margin "
                            "is below 5% and may require review."
                        ),
                        "metric": "operating_margin",
                        "value": round(operating_margin, 2)
                    })

        # ---------------------------------------------------------
        # 7. Debt Information
        # ---------------------------------------------------------

        debt_patterns = [
            r"\btotal\s+debt\b",
            r"\blong[\s-]+term\s+debt\b",
            r"\bshort[\s-]+term\s+debt\b",
            r"\btotal\s+borrowings\b",
            r"\bdebt\s+and\s+borrowings\b"
        ]

        debt_found = False

        for pattern in debt_patterns:

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                debt_found = True

                observations.append(
                    "Debt or borrowing-related information "
                    "was detected in the document."
                )

                break

        if not debt_found:

            observations.append(
                "No clear debt-related terminology was detected."
            )

        # ---------------------------------------------------------
        # 8. Rising Debt
        # ---------------------------------------------------------

        debt_increase_patterns = [
            r"(?:debt|borrowings).{0,100}"
            r"(?:increased|increase|higher|grew|growth|rose)",

            r"(?:increased|increase|higher|grew|growth|rose)"
            r".{0,100}"
            r"(?:debt|borrowings)"
        ]

        for pattern in debt_increase_patterns:

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                red_flags.append({
                    "type": "Rising Debt",
                    "severity": "Medium",
                    "message": (
                        "The document contains language indicating "
                        "that debt or borrowings may have increased. "
                        "Further review of the financial table is recommended."
                    ),
                    "metric": "debt"
                })

                break

        # ---------------------------------------------------------
        # 9. Falling Margins
        # ---------------------------------------------------------

        margin_decline_patterns = [
            r"(?:operating|profit|net)\s+margin"
            r".{0,100}"
            r"(?:declined|decreased|fell|dropped|lower|reduced)",

            r"(?:declined|decreased|fell|dropped|lower|reduced)"
            r".{0,100}"
            r"(?:operating|profit|net)\s+margin"
        ]

        for pattern in margin_decline_patterns:

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                red_flags.append({
                    "type": "Falling Margin",
                    "severity": "Medium",
                    "message": (
                        "The document contains language indicating "
                        "that a profit margin may have declined."
                    ),
                    "metric": "margin"
                })

                break

        # ---------------------------------------------------------
        # 10. Auditor Qualification
        # ---------------------------------------------------------
        #
        # IMPORTANT:
        # Search specifically for strong auditor-opinion wording.
        #
        # A report can contain words such as "qualified", "opinion",
        # "audit", or "material" in many ordinary contexts.
        # Those words alone must NOT create an auditor flag.
        #
        # We therefore require the phrase to appear in an
        # auditor-report context.
        # ---------------------------------------------------------

        auditor_patterns = [
            r"\bqualified\s+opinion\b",
            r"\bopinion\s+is\s+qualified\b",
            r"\bbasis\s+for\s+qualified\s+opinion\b",
            r"\bqualified\s+audit\s+opinion\b",
            r"\badverse\s+opinion\b",
            r"\bopinion\s+is\s+adverse\b",
            r"\bdisclaimer\s+of\s+opinion\b",
            r"\bopinion\s+is\s+disclaimed\b"
        ]

        auditor_match = None

        for pattern in auditor_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                auditor_match = match
                break

        if auditor_match:

            source_start = max(
                0,
                auditor_match.start() - 250
            )

            source_end = min(
                len(text),
                auditor_match.end() + 350
            )

            auditor_source = text[
                source_start:source_end
            ]

            auditor_source = re.sub(
                r"\s+",
                " ",
                auditor_source
            ).strip()

            red_flags.append({
                "type": "Auditor Qualification",
                "severity": "High",
                "message": (
                    "A strong audit-opinion phrase associated with "
                    "a qualified, adverse, or disclaimed opinion "
                    "was detected. The auditor's report should be "
                    "reviewed directly."
                ),
                "metric": "auditor",
                "source": auditor_source
            })

        else:

            observations.append(
                "No strong auditor qualification terminology "
                "was detected."
            )

        # ---------------------------------------------------------
        # 11. Going Concern
        # ---------------------------------------------------------

        going_concern_patterns = [
            r"substantial\s+doubt.{0,100}going\s+concern",
            r"material\s+uncertainty.{0,100}going\s+concern",
            r"going\s+concern.{0,100}material\s+uncertainty",
            r"ability\s+to\s+continue\s+as\s+a\s+going\s+concern"
        ]

        for pattern in going_concern_patterns:

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                red_flags.append({
                    "type": "Going Concern Indicator",
                    "severity": "High",
                    "message": (
                        "The report contains contextual language "
                        "that may indicate a going-concern issue. "
                        "The relevant section should be reviewed."
                    ),
                    "metric": "going_concern"
                })

                break

        # ---------------------------------------------------------
        # 12. Unusual Financial Language
        # ---------------------------------------------------------

        unusual_patterns = {
            "restatement": r"\brestatement\b",

            "accounting irregularity":
                r"\baccounting\s+irregularit",

            "financial irregularity":
                r"\bfinancial\s+irregularit",

            "significant impairment":
                r"\bsignificant\s+impairment\b"
        }

        unusual_findings = []

        for name, pattern in unusual_patterns.items():

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                unusual_findings.append(name)

        if unusual_findings:

            red_flags.append({
                "type": "Potentially Unusual Financial Disclosure",
                "severity": "Medium",
                "message": (
                    "The document contains financial disclosure "
                    "terms that may require further review. "
                    "The presence of these terms alone does not "
                    "confirm a financial problem."
                ),
                "indicators": unusual_findings
            })

        # ---------------------------------------------------------
        # 13. Risk Level
        # ---------------------------------------------------------

        risk_level = self._calculate_risk_level(
            red_flags
        )

        # ---------------------------------------------------------
        # 14. Final Result
        # ---------------------------------------------------------

        return {
            "risk_level": risk_level,
            "red_flag_count": len(red_flags),
            "red_flags": red_flags,
            "observations": observations,
            "analyzed_metrics": extracted_metrics
        }

    # =============================================================
    # Helper: Convert extracted value into a number
    # =============================================================

    @staticmethod
    def _to_number(value):

        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):

            cleaned = value.replace(",", "")
            cleaned = cleaned.replace("₹", "")
            cleaned = cleaned.replace("$", "")
            cleaned = cleaned.replace("%", "")
            cleaned = cleaned.strip()

            try:
                return float(cleaned)

            except ValueError:
                return None

        return None

    # =============================================================
    # Helper: Calculate overall risk level
    # =============================================================

    @staticmethod
    def _calculate_risk_level(red_flags):

        if not red_flags:
            return "Low"

        high_count = sum(
            1
            for flag in red_flags
            if flag.get("severity") == "High"
        )

        medium_count = sum(
            1
            for flag in red_flags
            if flag.get("severity") == "Medium"
        )

        if high_count >= 1:
            return "High"

        if medium_count >= 2:
            return "Medium"

        if medium_count == 1:
            return "Medium"

        return "Low"
