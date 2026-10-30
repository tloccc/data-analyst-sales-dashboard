"""Pure, testable analytics functions used by the Data Analyst dashboard."""
from __future__ import annotations

import pandas as pd


def build_pareto_table(
    frame: pd.DataFrame,
    product_col: str = "product",
    revenue_col: str = "revenue",
    threshold_pct: float = 80.0,
) -> tuple[pd.DataFrame, int, float]:
    """Return positive-revenue products sorted by contribution and cumulative share.

    Returns (table, number_of_products_to_reach_threshold, achieved_share_pct).
    Negative/zero revenue is excluded so returns do not distort positive sales mix.
    """
    if not 0 < threshold_pct <= 100:
        raise ValueError("threshold_pct must be in (0, 100].")
    if product_col not in frame.columns or revenue_col not in frame.columns:
        return pd.DataFrame(columns=[product_col, revenue_col, "contribution_pct", "cumulative_pct"]), 0, 0.0

    work = frame[[product_col, revenue_col]].copy()
    work[revenue_col] = pd.to_numeric(work[revenue_col], errors="coerce")
    work = work.dropna(subset=[product_col, revenue_col])
    work[product_col] = work[product_col].astype("string").str.strip()
    work = work[(work[product_col] != "") & (work[revenue_col] > 0)]
    work = work.groupby(product_col, as_index=False)[revenue_col].sum()
    work = work[work[revenue_col] > 0].sort_values(revenue_col, ascending=False).reset_index(drop=True)
    if work.empty:
        work["contribution_pct"] = pd.Series(dtype=float)
        work["cumulative_pct"] = pd.Series(dtype=float)
        return work, 0, 0.0

    total = float(work[revenue_col].sum())
    work["contribution_pct"] = work[revenue_col] / total * 100.0
    work["cumulative_pct"] = work["contribution_pct"].cumsum()
    reached = work.index[work["cumulative_pct"] >= threshold_pct]
    count = int(reached[0] + 1) if len(reached) else len(work)
    achieved = float(work.iloc[count - 1]["cumulative_pct"])
    return work, count, achieved


def detect_revenue_anomalies(
    frame: pd.DataFrame,
    date_col: str = "date",
    revenue_col: str = "revenue",
    min_points: int = 7,
    robust_z_threshold: float = 3.5,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Flag unusual daily revenue using robust z-score, with IQR fallback.

    The output flags review candidates, not proof of errors or causation.
    """
    cols = [date_col, revenue_col]
    if any(c not in frame.columns for c in cols):
        empty = pd.DataFrame(columns=cols + ["robust_score", "reason"])
        return empty, empty.copy(), "Không đủ cột dữ liệu"
    work = frame[cols].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work[revenue_col] = pd.to_numeric(work[revenue_col], errors="coerce")
    work = work.dropna(subset=cols).sort_values(date_col).reset_index(drop=True)
    if len(work) < min_points:
        work["robust_score"] = float("nan")
        work["reason"] = "Chưa đủ dữ liệu"
        return work, work.iloc[0:0].copy(), f"Cần tối thiểu {min_points} điểm dữ liệu"

    values = work[revenue_col].astype(float)
    median_value = float(values.median())
    mad = float((values - median_value).abs().median())
    if mad > 0:
        scores = 0.6745 * (values - median_value) / mad
        work["robust_score"] = scores
        work["reason"] = scores.map(lambda z: "Cao bất thường" if z > robust_z_threshold else ("Thấp bất thường" if z < -robust_z_threshold else "Trong ngưỡng"))
        flagged = work[scores.abs() > robust_z_threshold].copy()
        method = f"Median Absolute Deviation (robust z-score > {robust_z_threshold:g})"
    else:
        q1, q3 = float(values.quantile(0.25)), float(values.quantile(0.75))
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        work["robust_score"] = float("nan")
        work["reason"] = values.map(lambda v: "Cao bất thường" if v > upper else ("Thấp bất thường" if v < lower else "Trong ngưỡng"))
        flagged = work[work["reason"] != "Trong ngưỡng"].copy()
        method = "Quy tắc IQR (ngoài Q1 − 1,5×IQR hoặc Q3 + 1,5×IQR)"
    return work, flagged, method

def compare_revenue_periods(
    current_frame: pd.DataFrame,
    previous_frame: pd.DataFrame,
    revenue_col: str = "revenue",
) -> dict:
    """Compare revenue totals between two periods without inventing missing data."""
    result = {
        "status": "ok",
        "current_revenue": None,
        "previous_revenue": None,
        "change": None,
        "change_pct": None,
        "message": "",
    }

    if revenue_col not in current_frame.columns or revenue_col not in previous_frame.columns:
        result["status"] = "missing_column"
        result["message"] = f"Thiếu cột '{revenue_col}' ở một trong hai kỳ."
        return result

    current = pd.to_numeric(current_frame[revenue_col], errors="coerce").dropna()
    previous = pd.to_numeric(previous_frame[revenue_col], errors="coerce").dropna()

    if current.empty or previous.empty:
        result["status"] = "insufficient_data"
        result["message"] = "Một trong hai kỳ không có doanh thu hợp lệ để so sánh."
        return result

    current_total = float(current.sum())
    previous_total = float(previous.sum())
    change = current_total - previous_total

    result["current_revenue"] = current_total
    result["previous_revenue"] = previous_total
    result["change"] = change

    if previous_total != 0:
        result["change_pct"] = change / abs(previous_total) * 100
        result["status"] = "increase" if change > 0 else (
            "decrease" if change < 0 else "unchanged"
        )
        result["message"] = (
            f"Doanh thu tăng {result['change_pct']:.2f}%."
            if change > 0
            else f"Doanh thu giảm {abs(result['change_pct']):.2f}%."
            if change < 0
            else "Doanh thu không thay đổi."
        )
    elif current_total > 0:
        result["status"] = "increase_from_zero"
        result["message"] = (
            "Kỳ hiện tại có doanh thu dương, trong khi doanh thu kỳ trước bằng 0; "
            "không thể tính phần trăm tăng trưởng thông thường."
        )
    elif current_total < 0:
        result["status"] = "negative_from_zero"
        result["message"] = (
            "Kỳ hiện tại có tổng doanh thu âm và kỳ trước bằng 0; "
            "không thể tính phần trăm tăng trưởng thông thường."
        )
    else:
        result["status"] = "unchanged"
        result["change_pct"] = 0.0
        result["message"] = "Cả hai kỳ đều có tổng doanh thu bằng 0."

    return result


def get_top_products(
    frame: pd.DataFrame,
    product_col: str = "product",
    revenue_col: str = "revenue",
    top_n: int = 5,
) -> pd.DataFrame:
    """Rank products by positive revenue and calculate their share of positive revenue."""
    columns = [product_col, revenue_col, "contribution_pct"]

    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    if product_col not in frame.columns or revenue_col not in frame.columns:
        return pd.DataFrame(columns=columns)

    work = frame[[product_col, revenue_col]].copy()
    work[revenue_col] = pd.to_numeric(work[revenue_col], errors="coerce")
    work = work.dropna(subset=[product_col, revenue_col])
    work[product_col] = work[product_col].astype("string").str.strip()
    work = work[(work[product_col] != "") & (work[revenue_col] > 0)]

    work = (
        work.groupby(product_col, as_index=False)[revenue_col]
        .sum()
    )
    work = work[work[revenue_col] > 0]
    work = work.sort_values(
        revenue_col, ascending=False
    ).reset_index(drop=True)

    if work.empty:
        work["contribution_pct"] = pd.Series(dtype=float)
        return work[columns]

    total = float(work[revenue_col].sum())
    work["contribution_pct"] = work[revenue_col] / total * 100
    return work.head(top_n)[columns].reset_index(drop=True)


def generate_business_insights(
    current_frame: pd.DataFrame,
    previous_frame: pd.DataFrame | None = None,
    product_col: str = "product",
    revenue_col: str = "revenue",
    top_n: int = 3,
) -> list[str]:
    """Generate concise, evidence-based observations from available sales data."""
    insights = []

    if revenue_col not in current_frame.columns:
        return [f"Chưa thể phân tích: thiếu cột '{revenue_col}'."]

    current_revenue = pd.to_numeric(
        current_frame[revenue_col], errors="coerce"
    ).dropna()

    if current_revenue.empty:
        return ["Chưa thể phân tích: không có dữ liệu doanh thu hợp lệ."]

    total = float(current_revenue.sum())
    insights.append(f"Tổng doanh thu trong dữ liệu hiện tại: {total:,.0f}.")

    if previous_frame is not None:
        comparison = compare_revenue_periods(
            current_frame, previous_frame, revenue_col
        )
        if comparison["status"] == "ok":
            insights.append(comparison["message"])
        elif comparison["status"] == "unchanged":
            insights.append(comparison["message"])
        else:
            insights.append(comparison["message"])

    top_products = get_top_products(
        current_frame, product_col, revenue_col, top_n
    )

    if not top_products.empty:
        leaders = top_products.head(3)
        names = ", ".join(
            f"{row[product_col]} ({row['contribution_pct']:.1f}%)"
            for _, row in leaders.iterrows()
        )
        insights.append(
            "Sản phẩm đóng góp doanh thu dương cao nhất trong dữ liệu: "
            + names
            + "."
        )
    elif product_col not in current_frame.columns:
        insights.append(
            f"Chưa thể xếp hạng sản phẩm: thiếu cột '{product_col}'."
        )
    else:
        insights.append(
            "Chưa có sản phẩm nào với doanh thu dương hợp lệ để xếp hạng."
        )

    insights.append(
        "Gợi ý kiểm tra: đối chiếu các sản phẩm dẫn đầu với tồn kho, "
        "biên lợi nhuận và dữ liệu của kỳ trước trước khi quyết định kinh doanh."
    )

    return insights
