"""Valuation helpers matching the project's P/E, PEG-style, and cash metrics formulas."""

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, field_validator


def _compute_value(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("b cannot be zero")
    return a / (100 * b)


class ValuationMetricsInput(BaseModel):
    """All amounts must share the same unit (e.g. all in INR crores)."""

    net_profit: float = Field(
        ...,
        description="Trailing net profit on the research anchor (e.g. 9MFY26 TTM PAT, INR crores).",
    )
    future_profit: float = Field(
        ...,
        description="Forward net profit for the target year (e.g. FY28 consensus/guidance)—used as 'future' in Future P/E; not TTM.",
    )
    market_cap: float = Field(..., description="Market capitalization, same unit as profits.")
    operating_cash_flow: float = Field(
        ...,
        description="Operating cash flow (OCF) for cash conversion and MCap/OCF.",
    )
    ebitda: float = Field(..., description="EBITDA for cash conversion ratio (OCF/EBITDA).")
    current_revenue: float = Field(
        ...,
        description="Recent revenue on same TTM convention as net_profit (e.g. 9MFY26 TTM sales).",
    )
    prior_revenue: float = Field(
        ...,
        description="Prior comparable revenue (e.g. year-earlier TTM) so (current/prior)^(1/T)-1 matches the chosen horizon.",
    )
    growth_period_years: float = Field(
        default=2.25,
        description=(
            "Years T for implied growth: b=(future_profit/net_profit)^(1/T), "
            "c=(current_revenue/prior_revenue)^(1/T). Default 2.25 when T equals "
            "year-fraction from TTM anchor (e.g. 9MFY26) to FY28; override if your "
            "dates imply a different span."
        ),
    )

    @field_validator(
        "net_profit",
        "future_profit",
        "market_cap",
        "operating_cash_flow",
        "ebitda",
        "current_revenue",
        "prior_revenue",
        "growth_period_years",
    )
    @classmethod
    def must_be_finite(cls, v: float) -> float:
        if v != v or v in (float("inf"), float("-inf")):  # noqa: PLR0124
            raise ValueError("must be a finite number")
        return v


class ValuationMetricsTool(BaseTool):
    name: str = "valuation_metrics_calculator"
    description: str = (
        "Computes derived metrics: net_profit should be trailing (e.g. 9MFY26 TTM PAT); "
        "future_profit should be forward-year estimate (e.g. FY28). Implied profit and sales "
        "growth % use T=growth_period_years (default 2.25 when that is years from TTM anchor to FY28). "
        "Future P/E = market_cap/future_profit; Future PEG uses b=(future_profit/net_profit)^(1/T). "
        "Also OCF/EBITDA % and market_cap/OCF. Same unit for all money fields (e.g. INR crores)."
    )
    args_schema: Type[BaseModel] = ValuationMetricsInput

    def _run(
        self,
        net_profit: float,
        future_profit: float,
        market_cap: float,
        operating_cash_flow: float,
        ebitda: float,
        current_revenue: float,
        prior_revenue: float,
        growth_period_years: float = 2.25,
    ) -> str:
        t = growth_period_years
        lines: list[str] = []

        try:
            if future_profit == 0:
                return "Error: future_profit cannot be zero (Future P/E undefined)."
            if net_profit == 0:
                return "Error: net_profit cannot be zero (growth factor b undefined)."
            if prior_revenue == 0:
                return "Error: prior_revenue cannot be zero (sales growth undefined)."

            a = market_cap / future_profit
            b = (future_profit / net_profit) ** (1 / t)
            c = (current_revenue / prior_revenue) ** (1 / t)

            lines.append(f"Implied profit growth ({t}y horizon, %): {(b - 1) * 100:.2f}")
            lines.append(f"Implied sales growth ({t}y horizon, %): {(c - 1) * 100:.2f}")

            b_minus_1 = b - 1
            if abs(b_minus_1) < 1e-12:
                lines.append("Future PEG: undefined (implied profit growth factor b equals 1, b-1 is zero).")
            else:
                lines.append(f"Future PEG: {_compute_value(a, b_minus_1):.2f}")

            lines.append(f"Future P/E: {a:.2f}")

            if ebitda == 0:
                lines.append("Cash conversion (OCF/EBITDA %): undefined (EBITDA is zero).")
            else:
                lines.append(f"Cash conversion (OCF/EBITDA %): {(operating_cash_flow / ebitda) * 100:.2f}")

            if operating_cash_flow == 0:
                lines.append("Real valuation (market cap / OCF): undefined (OCF is zero).")
            else:
                lines.append(f"Real valuation (market cap / OCF): {market_cap / operating_cash_flow:.2f}")

            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"
