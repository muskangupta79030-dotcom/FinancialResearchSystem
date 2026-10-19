from pydantic import BaseModel


class FinancialMetrics(BaseModel):
    revenue: str | None = None
    net_income: str | None = None
    operating_profit: str | None = None
