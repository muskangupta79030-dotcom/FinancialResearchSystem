import re


class ReportAgent:
    """
    Report Agent for generating a structured financial report
    from extracted financial metrics and red-flag analysis.
    """

    def generate_report(
        self,
        company_name,
        extracted_metrics,
        red_flag_analysis=None
    ):
        if not company_name:
            company_name = "Financial Document"

        if not extracted_metrics:
            return {
                "status": "error",
                "message": "No extracted financial metrics available.",
                "company": company_name
            }

        executive_summary = self._generate_executive_summary(
            company_name,
            extracted_metrics,
            red_flag_analysis
        )

        key_financials = self._generate_key_financials(
            extracted_metrics
        )

        red_flags = self._format_red_flags(
            red_flag_analysis
        )

        return {
            "status": "success",
            "company": company_name,
            "report": {
                "executive_summary": executive_summary,
                "key_financials": key_financials,
                "red_flags": red_flags
            }
        }

    # =====================================================
    # EXECUTIVE SUMMARY
    # =====================================================

    def _generate_executive_summary(
        self,
        company_name,
        metrics,
        red_flag_analysis
    ):
        revenue = self._get_metric(
            metrics,
            [
                "revenue",
                "total_revenue",
                "net_sales",
                "sales"
            ]
        )

        net_income = self._get_metric(
            metrics,
            [
                "net_income",
                "net_profit",
                "profit_after_tax"
            ]
        )

        operating_income = self._get_metric(
            metrics,
            [
                "operating_income",
                "operating_profit"
            ]
        )

        parts = []

        parts.append(
            f"{company_name} financial report summary:"
        )

        if revenue:
            parts.append(
                f"Revenue was {self._format_metric(revenue)}."
            )

        if net_income:
            parts.append(
                f"Net income was {self._format_metric(net_income)}."
            )

        if operating_income:
            parts.append(
                f"Operating income was "
                f"{self._format_metric(operating_income)}."
            )

        if not revenue and not net_income and not operating_income:
            parts.append(
                "The available financial document contains "
                "financial information, but the key financial "
                "metrics could not be reliably extracted."
            )

        if red_flag_analysis:
            flag_count = self._count_flags(
                red_flag_analysis
            )

            if flag_count > 0:
                parts.append(
                    f"The analysis identified {flag_count} "
                    f"potential financial red flag(s) for review."
                )
            else:
                parts.append(
                    "No major financial red flags were identified "
                    "by the current automated analysis."
                )

        return " ".join(parts)

    # =====================================================
    # KEY FINANCIALS
    # =====================================================

    def _generate_key_financials(self, metrics):

        key_financials = {}

        revenue = self._get_metric(
            metrics,
            [
                "revenue",
                "total_revenue",
                "net_sales",
                "sales"
            ]
        )

        net_income = self._get_metric(
            metrics,
            [
                "net_income",
                "net_profit",
                "profit_after_tax"
            ]
        )

        operating_income = self._get_metric(
            metrics,
            [
                "operating_income",
                "operating_profit"
            ]
        )

        if revenue:
            key_financials["revenue"] = revenue

        if net_income:
            key_financials["net_income"] = net_income

        if operating_income:
            key_financials["operating_income"] = operating_income

        return key_financials

    # =====================================================
    # RED FLAGS
    # =====================================================

    def _format_red_flags(self, red_flag_analysis):

        if not red_flag_analysis:
            return []

        if isinstance(red_flag_analysis, list):
            return red_flag_analysis

        if isinstance(red_flag_analysis, dict):

            for key in [
                "red_flags",
                "flags",
                "findings",
                "alerts",
                "analysis"
            ]:
                value = red_flag_analysis.get(key)

                if isinstance(value, list):
                    return value

                if isinstance(value, str) and value.strip():
                    return [value]

            return []

        if isinstance(red_flag_analysis, str):
            text = red_flag_analysis.strip()

            if not text:
                return []

            return [text]

        return []

    # =====================================================
    # METRIC SEARCH
    # =====================================================

    def _get_metric(self, metrics, possible_names):

        if not isinstance(metrics, dict):
            return None

        # Direct key match
        for name in possible_names:

            if name in metrics:

                value = metrics[name]

                if value not in [None, "", "N/A"]:
                    return value

        # Case-insensitive key match
        lower_keys = {
            str(key).lower(): key
            for key in metrics.keys()
        }

        for name in possible_names:

            actual_key = lower_keys.get(
                name.lower()
            )

            if actual_key is not None:

                value = metrics[actual_key]

                if value not in [None, "", "N/A"]:
                    return value

        return None

    # =====================================================
    # FORMAT METRIC
    # =====================================================

    def _format_metric(self, metric):

        if isinstance(metric, dict):

            value = metric.get(
                "value",
                metric.get(
                    "amount",
                    metric.get(
                        "number",
                        ""
                    )
                )
            )

            unit = metric.get(
                "unit",
                ""
            )

            if value != "":
                if unit:
                    return f"{value} {unit}"

                return str(value)

            return str(metric)

        return str(metric)

    # =====================================================
    # COUNT RED FLAGS
    # =====================================================

    def _count_flags(self, red_flag_analysis):

        flags = self._format_red_flags(
            red_flag_analysis
        )

        return len(flags)
