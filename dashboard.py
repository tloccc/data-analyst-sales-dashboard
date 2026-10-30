import hashlib
from datetime import datetime
import io
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# 1. CẤU HÌNH TRANG
# =========================================================
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --app-bg: #0a1020;
        --panel-bg: #111b2e;
        --panel-soft: #15233a;
        --border: rgba(148, 163, 184, .18);
        --text-main: #f1f5f9;
        --text-muted: #9fb0c8;
        --accent: #60a5fa;
        --accent-2: #34d399;
    }
    .stApp { background: radial-gradient(ellipse at 15% 0%, #142440 0%, var(--app-bg) 45%); color: var(--text-main); }
    [data-testid="stHeader"] { background: rgba(10, 16, 32, .78); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #101a2d, #0c1425); border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
    .block-container { max-width: 1580px; padding-top: 1.35rem; padding-bottom: 3rem; }
    h1, h2, h3, h4 { color: var(--text-main) !important; letter-spacing: -.025em; }
    p, label, li { color: #cbd5e1; }
    [data-testid="stCaptionContainer"] { color: var(--text-muted); }
    .hero {
        position: relative; overflow: hidden; padding: 30px 32px; margin: 0 0 24px;
        border: 1px solid rgba(96, 165, 250, .25); border-radius: 22px;
        background: linear-gradient(115deg, rgba(21, 39, 68, .98), rgba(15, 25, 44, .95) 58%, rgba(18, 48, 68, .88));
        box-shadow: 0 18px 50px rgba(0, 0, 0, .18);
    }
    .hero:after { content: ""; position: absolute; width: 240px; height: 240px; right: -75px; top: -115px; border-radius: 50%; border: 1px solid rgba(96,165,250,.22); box-shadow: 0 0 0 28px rgba(96,165,250,.035), 0 0 0 58px rgba(96,165,250,.025); pointer-events: none; }
    .hero-eyebrow { color: #93c5fd; font-size: 11px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; margin-bottom: 10px; }
    .hero-title { font-size: clamp(26px, 3vw, 36px); line-height: 1.15; font-weight: 800; color: #f8fafc; letter-spacing: -.04em; }
    .hero-subtitle { font-size: 14px; line-height: 1.7; color: #b6c6dc; margin-top: 10px; max-width: 760px; }
    .hero-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
    .hero-pill { border: 1px solid rgba(148,163,184,.23); border-radius: 999px; background: rgba(15,23,42,.45); padding: 6px 11px; font-size: 11px; font-weight: 650; color: #dbeafe; }
    div[data-testid="stMetric"] { background: linear-gradient(145deg, rgba(21, 34, 56, .96), rgba(15, 25, 42, .96)); border: 1px solid var(--border); border-radius: 16px; padding: 17px 18px; min-height: 112px; box-shadow: 0 8px 24px rgba(0,0,0,.10); transition: border-color .18s ease, transform .18s ease; }
    div[data-testid="stMetric"]:hover { border-color: rgba(96,165,250,.48); transform: translateY(-1px); }
    div[data-testid="stMetricLabel"] { color: var(--text-muted); font-size: 12px; font-weight: 650; }
    div[data-testid="stMetricValue"] { color: #f8fafc; font-size: clamp(22px, 2.2vw, 29px); font-weight: 800; letter-spacing: -.035em; }
    div[data-testid="stMetricDelta"] { font-size: 12px; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--border) !important; border-radius: 16px !important; background: rgba(15, 25, 42, .30); }
    div[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
    [data-testid="stFileUploader"] { border: 1px dashed rgba(96,165,250,.45); border-radius: 16px; padding: 10px; background: rgba(17,27,46,.48); }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 7px; border-bottom: 1px solid var(--border); }
    [data-testid="stTabs"] button[role="tab"] { border-radius: 9px 9px 0 0; padding: 10px 15px; color: #b8c7dc; }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: #bfdbfe; background: rgba(37,99,235,.14); }
    [data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 12px; background: rgba(17,27,46,.34); }
    [data-testid="stSelectbox"], [data-testid="stDateInput"], [data-testid="stTextInput"], [data-testid="stNumberInput"] { border-radius: 10px; }
    div.stButton > button, div.stDownloadButton > button, [data-testid="stFormSubmitButton"] button { border-radius: 10px; min-height: 42px; font-weight: 700; transition: all .18s ease; }
    div.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] { background: linear-gradient(110deg, #2563eb, #3b82f6); border: 1px solid #60a5fa; color: white; box-shadow: 0 7px 18px rgba(37,99,235,.18); }
    div.stButton > button:hover, div.stDownloadButton > button:hover { border-color: #60a5fa; transform: translateY(-1px); }
    .small-muted { color: var(--text-muted); font-size: 12px; }
    hr { border-color: var(--border); }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# SQLITE — LỊCH SỬ PHÂN TÍCH DATA QUALITY
# =========================================================
HISTORY_DB_PATH = Path(__file__).resolve().parent / "data_quality_history.db"


def init_history_db():
    """Create the local history table if it does not exist."""
    with sqlite3.connect(HISTORY_DB_PATH, timeout=10) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source_file TEXT NOT NULL,
                status TEXT NOT NULL,
                rows_before INTEGER,
                rows_after INTEGER,
                ai_model TEXT,
                metrics_json TEXT NOT NULL,
                cleaning_log_json TEXT NOT NULL,
                ai_explanation TEXT,
                report_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at "
            "ON analysis_history(created_at DESC)"
        )
        conn.commit()


def save_history_record(record):
    """Persist one explicit user-approved snapshot in SQLite."""
    init_history_db()
    with sqlite3.connect(HISTORY_DB_PATH, timeout=10) as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_history (
                created_at, source_file, status, rows_before, rows_after,
                ai_model, metrics_json, cleaning_log_json, ai_explanation, report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["created_at"],
                record["source_file"],
                record["status"],
                record.get("rows_before"),
                record.get("rows_after"),
                record.get("ai_model"),
                json.dumps(record.get("metrics", {}), ensure_ascii=False, default=str),
                json.dumps(record.get("cleaning_log", []), ensure_ascii=False, default=str),
                record.get("ai_explanation"),
                json.dumps(record.get("report", {}), ensure_ascii=False, default=str),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def load_history_records(limit=50):
    """Return recent history summaries, newest first."""
    init_history_db()
    with sqlite3.connect(HISTORY_DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, created_at, source_file, status, rows_before, rows_after, ai_model
            FROM analysis_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return [dict(row) for row in rows]


def load_history_record(record_id):
    """Load a full saved snapshot by its SQLite ID."""
    init_history_db()
    with sqlite3.connect(HISTORY_DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM analysis_history WHERE id = ?",
            (int(record_id),),
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    for field in ("metrics_json", "cleaning_log_json", "report_json"):
        try:
            result[field.replace("_json", "")] = json.loads(result[field])
        except (TypeError, json.JSONDecodeError):
            result[field.replace("_json", "")] = {}
    return result


# =========================================================
# 2. SESSION STATE
# =========================================================
DEFAULTS = {
    "access_token": None,
    "user_email": None,
    "api_base": "http://127.0.0.1:8000",
    "analysis_result": None,
    "filtered_ai_result": None,
    "filtered_ai_signature": None,
    "last_filename": None,
    "source_df": None,
    "backend_status": "unknown",
    "cleaned_df": None,
    "cleaning_log": None,
    "cleaned_source_signature": None,
    "quality_ai_result": None,
    "quality_ai_signature": None,
    "before_after_report_data": None,
    "target_revenue_vnd": 100_000_000,
    "target_order_count": 100,
    "target_aov_vnd": 2_000_000,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 3. HÀM HỖ TRỢ
# =========================================================
def api_url(path):
    return st.session_state.api_base.rstrip("/") + path


def show_api_error(response):
    try:
        payload = response.json()
        detail = payload.get("detail", response.text)
    except (ValueError, AttributeError):
        detail = response.text

    st.error(f"API báo lỗi ({response.status_code}): {detail}")


def normalize_name(value):
    """Chuẩn hóa tên cột để nhận diện cả tiếng Việt có dấu."""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )
    value = value.replace("đ", "d")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def find_column(df, aliases):
    """Chỉ trả về cột nếu tên cột khớp với danh sách cho phép."""
    normalized = {
        normalize_name(column): column
        for column in df.columns
    }

    for alias in aliases:
        key = normalize_name(alias)
        if key in normalized:
            return normalized[key]

    return None



REVENUE_ALIASES = [
    "doanh_thu",
    "tong_doanh_thu",
    "revenue",
    "total_revenue",
    "sales_revenue",
    "net_sales",
    "gross_sales",
    "revenue_vnd",
    "amount",
    "sales_amount",
]

ORDER_ALIASES = [
    "don_hang",
    "so_don_hang",
    "tong_don_hang",
    "orders",
    "order_count",
    "total_orders",
    "number_of_orders",
    "order_id",
    "transaction_id",
]

EMPLOYEE_ALIASES = [
    "nhan_vien",
    "ten_nhan_vien",
    "employee",
    "employee_name",
    "staff",
    "salesperson",
]

PRODUCT_ALIASES = [
    "san_pham", "ten_san_pham", "product", "product_name", "item", "item_name",
    "sku_name", "mat_hang",
]

CATEGORY_ALIASES = [
    "danh_muc", "loai_san_pham", "category", "product_category", "product_type",
]

QUANTITY_ALIASES = [
    "so_luong", "quantity", "qty", "units_sold", "item_quantity", "sales_quantity",
]

DATE_ALIASES = [
    "ngay",
    "ngay_ban",
    "ngay_dat_hang",
    "date",
    "order_date",
    "sale_date",
    "transaction_date",
    "record_date",
    "created_at",
]


def read_csv_safely(file_bytes):
    """Đọc CSV với một số encoding và cách nhận diện dấu phân cách."""
    last_error = None

    for encoding in ["utf-8-sig", "utf-8", "cp1258", "latin1"]:
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                sep=None,
                engine="python",
                encoding=encoding,
            )

            # Từ chối file không có cột hoặc chỉ có một cột rỗng.
            if len(df.columns) == 0:
                continue

            df.columns = [
                str(column).strip()
                for column in df.columns
            ]
            return df

        except Exception as exc:
            last_error = exc

    raise ValueError(f"Không đọc được CSV: {last_error}")


def to_numeric_series(series):
    """
    Chuyển số ở nhiều định dạng phổ biến sang số:
    1,500,000 | 1.500.000 | 1,500.50 | 1.500,50.
    Giá trị không thể nhận diện sẽ thành NaN, không tự biến thành 0.
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    def parse_value(value):
        if pd.isna(value):
            return float("nan")

        raw = str(value).strip()
        if not raw:
            return float("nan")

        # Số âm có thể được biểu diễn bằng ngoặc: (1,200) -> -1200.
        negative_by_parentheses = raw.startswith("(") and raw.endswith(")")
        if negative_by_parentheses:
            raw = raw[1:-1].strip()

        # Bỏ khoảng trắng và các ký hiệu tiền tệ; giữ lại dấu phân cách và dấu âm.
        raw = raw.replace(" ", "").replace("\\u00a0", "")
        raw = re.sub(r"[^0-9,\.\-+]", "", raw)
        if not raw or raw in {"-", "+", ".", ","}:
            return float("nan")

        comma_count = raw.count(",")
        dot_count = raw.count(".")

        if comma_count and dot_count:
            # Dấu xuất hiện cuối cùng thường là dấu thập phân:
            # 1,234.56 hoặc 1.234,56.
            decimal_sep = "," if raw.rfind(",") > raw.rfind(".") else "."
            thousands_sep = "." if decimal_sep == "," else ","
            raw = raw.replace(thousands_sep, "")
            if decimal_sep == ",":
                raw = raw.replace(",", ".")
        elif comma_count > 1:
            # Ví dụ 1,500,000: dấu phẩy là phân cách hàng nghìn.
            raw = raw.replace(",", "")
        elif dot_count > 1:
            # Ví dụ 1.500.000: dấu chấm là phân cách hàng nghìn.
            raw = raw.replace(".", "")
        elif comma_count == 1:
            left, right = raw.split(",")
            # Một nhóm đúng 3 chữ số sau dấu phẩy được xem là hàng nghìn.
            raw = left + right if len(right) == 3 and left.lstrip("+-").isdigit() else left + "." + right
        elif dot_count == 1:
            left, right = raw.split(".")
            # Một nhóm đúng 3 chữ số sau dấu chấm được xem là hàng nghìn.
            raw = left + right if len(right) == 3 and left.lstrip("+-").isdigit() else raw

        try:
            number = float(raw)
            return -abs(number) if negative_by_parentheses else number
        except (TypeError, ValueError):
            return float("nan")

    return series.map(parse_value).astype("float64")


def build_data_quality_report(df):
    """Tạo báo cáo tổng hợp và chi tiết theo từng dòng/cột; không sửa dữ liệu gốc."""
    row_count, column_count = df.shape

    # Coi cả chuỗi rỗng/khoảng trắng là thiếu, không chỉnh sửa df nguồn.
    missing_mask = df.isna() | df.astype("string").apply(
        lambda column: column.str.strip().eq("").fillna(False)
    )
    missing_by_column = missing_mask.sum()
    missing_cells = int(missing_by_column.sum())
    duplicate_mask = df.duplicated(keep="first")
    duplicate_rows = int(duplicate_mask.sum())

    column_rows = []
    issue_rows = []
    detail_rows = []
    numeric_aliases = {normalize_name(name) for name in REVENUE_ALIASES + ORDER_ALIASES}
    date_aliases = {normalize_name(name) for name in DATE_ALIASES}

    def csv_row_number(index_value, fallback_position):
        # DataFrame từ read_csv giữ index 0-based ngay cả khi lọc, nên +2 là dòng CSV
        # tính cả header. Có fallback an toàn nếu index không phải số nguyên.
        if isinstance(index_value, int) and index_value >= 0:
            return index_value + 2
        if hasattr(index_value, "item"):
            try:
                native = index_value.item()
                if isinstance(native, int) and native >= 0:
                    return native + 2
            except (ValueError, TypeError):
                pass
        return fallback_position + 2

    for position, (index_value, row) in enumerate(df.iterrows()):
        if bool(duplicate_mask.iloc[position]):
            row_values = "; ".join(
                f"{col}={row[col]}" for col in df.columns
            )
            detail_rows.append({
                "Dòng CSV": csv_row_number(index_value, position),
                "Cột": "Toàn bộ dòng",
                "Giá trị gốc": row_values[:500],
                "Loại vấn đề": "Dòng trùng lặp",
                "Mức độ": "Cảnh báo",
                "Khuyến nghị": "Xác minh có phải bản ghi lặp thật hay không; chưa tự xóa.",
            })

    for column in df.columns:
        series = df[column]
        name_key = normalize_name(column)
        missing_count = int(missing_mask[column].sum())
        missing_pct = (missing_count / row_count * 100) if row_count else 0.0
        numeric_values = to_numeric_series(series)
        non_missing_mask = ~missing_mask[column]
        numeric_valid_count = int((numeric_values.notna() & non_missing_mask).sum())
        numeric_invalid_count = 0
        numeric_like = False

        if name_key in numeric_aliases or pd.api.types.is_numeric_dtype(series):
            numeric_like = True
        else:
            non_missing_count = int(non_missing_mask.sum())
            if non_missing_count > 0 and numeric_valid_count > 0:
                numeric_like = (numeric_valid_count / non_missing_count) >= 0.8

        if numeric_like:
            numeric_invalid_mask = non_missing_mask & numeric_values.isna()
            numeric_invalid_count = int(numeric_invalid_mask.sum())
        else:
            numeric_invalid_mask = pd.Series(False, index=df.index)

        date_invalid_mask = pd.Series(False, index=df.index)
        date_invalid_count = 0
        date_like = name_key in date_aliases
        if date_like:
            parsed_dates = parse_date_series(series)
            date_invalid_mask = non_missing_mask & parsed_dates.isna()
            date_invalid_count = int(date_invalid_mask.sum())

        unique_count = int(series.nunique(dropna=True))
        column_rows.append({
            "Tên cột": str(column),
            "Kiểu dữ liệu": str(series.dtype),
            "Giá trị thiếu": missing_count,
            "% thiếu": round(missing_pct, 2),
            "Số giá trị duy nhất": unique_count,
            "Cột số được kiểm tra": "Có" if numeric_like else "Không",
            "Giá trị số không hợp lệ": numeric_invalid_count if numeric_like else 0,
            "Giá trị ngày không hợp lệ": date_invalid_count,
        })

        if missing_count:
            issue_rows.append({
                "Mức độ": "Cảnh báo", "Cột": str(column),
                "Vấn đề": "Giá trị thiếu", "Số lượng": missing_count,
                "Ví dụ": "Ô trống/NaN",
                "Khuyến nghị": "Xác minh nguồn dữ liệu; chỉ điền/xóa khi có quy tắc nghiệp vụ."
            })
            for position, (index_value, value) in enumerate(series.items()):
                if bool(missing_mask[column].iloc[position]):
                    detail_rows.append({
                        "Dòng CSV": csv_row_number(index_value, position),
                        "Cột": str(column),
                        "Giá trị gốc": "(trống)",
                        "Loại vấn đề": "Giá trị thiếu",
                        "Mức độ": "Cảnh báo",
                        "Khuyến nghị": "Xác minh nguồn dữ liệu; chỉ điền/xóa khi có quy tắc nghiệp vụ.",
                    })

        if numeric_like and numeric_invalid_count:
            examples = ", ".join(series[numeric_invalid_mask].astype(str).drop_duplicates().head(5).tolist())
            issue_rows.append({
                "Mức độ": "Lỗi dữ liệu", "Cột": str(column),
                "Vấn đề": "Giá trị số không hợp lệ", "Số lượng": numeric_invalid_count,
                "Ví dụ": examples or "—",
                "Khuyến nghị": "Kiểm tra dấu phân cách, ký hiệu tiền tệ hoặc giá trị nhập sai; không tự đổi thành 0."
            })
            for position, (index_value, value) in enumerate(series.items()):
                if bool(numeric_invalid_mask.iloc[position]):
                    detail_rows.append({
                        "Dòng CSV": csv_row_number(index_value, position),
                        "Cột": str(column),
                        "Giá trị gốc": str(value),
                        "Loại vấn đề": "Giá trị số không hợp lệ",
                        "Mức độ": "Lỗi dữ liệu",
                        "Khuyến nghị": "Kiểm tra dấu phân cách, ký hiệu tiền tệ hoặc giá trị nhập sai; không tự đổi thành 0.",
                    })

        if date_invalid_count:
            examples = ", ".join(series[date_invalid_mask].astype(str).drop_duplicates().head(5).tolist())
            issue_rows.append({
                "Mức độ": "Lỗi dữ liệu", "Cột": str(column),
                "Vấn đề": "Ngày không hợp lệ", "Số lượng": date_invalid_count,
                "Ví dụ": examples or "—",
                "Khuyến nghị": "Chuẩn hóa định dạng ngày và xác minh các giá trị không đọc được."
            })
            for position, (index_value, value) in enumerate(series.items()):
                if bool(date_invalid_mask.iloc[position]):
                    detail_rows.append({
                        "Dòng CSV": csv_row_number(index_value, position),
                        "Cột": str(column),
                        "Giá trị gốc": str(value),
                        "Loại vấn đề": "Ngày không hợp lệ",
                        "Mức độ": "Lỗi dữ liệu",
                        "Khuyến nghị": "Chuẩn hóa định dạng ngày và xác minh giá trị trước khi chuyển đổi.",
                    })

    if duplicate_rows:
        issue_rows.append({
            "Mức độ": "Cảnh báo", "Cột": "Toàn bộ dòng",
            "Vấn đề": "Dòng trùng lặp", "Số lượng": duplicate_rows,
            "Ví dụ": "Các dòng giống hệt nhau",
            "Khuyến nghị": "Xác minh đây có phải giao dịch lặp thật hay dữ liệu trùng do xuất file; chưa tự xóa."
        })

    total_numeric_invalid = sum(row["Giá trị số không hợp lệ"] for row in column_rows)
    total_invalid_dates = sum(row["Giá trị ngày không hợp lệ"] for row in column_rows)
    details_df = pd.DataFrame(detail_rows, columns=[
        "Dòng CSV", "Cột", "Giá trị gốc", "Loại vấn đề", "Mức độ", "Khuyến nghị"
    ])
    if not details_df.empty:
        details_df = details_df.sort_values(
            by=["Dòng CSV", "Cột", "Loại vấn đề"], kind="stable"
        ).reset_index(drop=True)

    return {
        "summary": {
            "row_count": int(row_count),
            "column_count": int(column_count),
            "total_cells": int(row_count * column_count),
            "missing_cells": missing_cells,
            "duplicate_rows": duplicate_rows,
            "invalid_numeric_cells": int(total_numeric_invalid),
            "invalid_date_cells": int(total_invalid_dates),
        },
        "columns": pd.DataFrame(column_rows),
        "issues": pd.DataFrame(issue_rows, columns=[
            "Mức độ", "Cột", "Vấn đề", "Số lượng", "Ví dụ", "Khuyến nghị"
        ]),
        "issue_details": details_df,
    }


def detect_cleaning_columns(df):
    """Identify likely numeric and date columns without modifying the source."""
    numeric_columns = []
    date_columns = []
    numeric_aliases = {normalize_name(name) for name in REVENUE_ALIASES + ORDER_ALIASES}
    date_aliases = {normalize_name(name) for name in DATE_ALIASES}

    for column in df.columns:
        key = normalize_name(column)
        series = df[column]
        non_missing = series.notna() & series.astype("string").str.strip().ne("").fillna(False)
        valid_numeric = to_numeric_series(series).notna() & non_missing
        denominator = int(non_missing.sum())
        ratio = (int(valid_numeric.sum()) / denominator) if denominator else 0
        if key in numeric_aliases or pd.api.types.is_numeric_dtype(series) or (denominator and ratio >= 0.8):
            numeric_columns.append(column)
        if key in date_aliases:
            date_columns.append(column)
    return numeric_columns, date_columns


def build_cleaned_candidate(df, numeric_columns, date_columns, remove_duplicates):
    """Create a separate cleaned copy. Invalid values are preserved, never coerced to zero."""
    cleaned = df.copy(deep=True)
    log_rows = []

    for column in numeric_columns:
        original = cleaned[column].copy()
        parsed = to_numeric_series(original)
        nonblank = original.notna() & original.astype("string").str.strip().ne("").fillna(False)
        convertible = nonblank & parsed.notna()
        changed = 0
        for idx in cleaned.index[convertible]:
            old_value = original.loc[idx]
            new_value = float(parsed.loc[idx])
            if isinstance(old_value, str):
                # Store normalized numeric values as numbers; pandas will serialize consistently.
                cleaned.at[idx, column] = new_value
                if str(old_value).strip() != str(new_value):
                    changed += 1
        if changed:
            log_rows.append({
                "Hành động": "Chuẩn hóa số",
                "Cột": str(column),
                "Số ô thay đổi": int(changed),
                "Quy tắc": "Chỉ chuẩn hóa giá trị đọc được thành số; giá trị lỗi và ô trống được giữ nguyên.",
            })
        invalid_count = int((nonblank & parsed.isna()).sum())
        if invalid_count:
            log_rows.append({
                "Hành động": "Giữ nguyên giá trị số lỗi",
                "Cột": str(column),
                "Số ô thay đổi": 0,
                "Quy tắc": f"Giữ nguyên {invalid_count} giá trị không đọc được; không tự đổi thành 0.",
            })

    for column in date_columns:
        original = cleaned[column].copy()
        parsed = parse_date_series(original)
        nonblank = original.notna() & original.astype("string").str.strip().ne("").fillna(False)
        convertible = nonblank & parsed.notna()
        changed = 0
        for idx in cleaned.index[convertible]:
            old_value = original.loc[idx]
            new_value = parsed.loc[idx].strftime("%Y-%m-%d")
            cleaned.at[idx, column] = new_value
            if str(old_value).strip() != new_value:
                changed += 1
        if changed:
            log_rows.append({
                "Hành động": "Chuẩn hóa ngày",
                "Cột": str(column),
                "Số ô thay đổi": int(changed),
                "Quy tắc": "Ngày đọc được chuyển về YYYY-MM-DD; ngày lỗi được giữ nguyên.",
            })
        invalid_count = int((nonblank & parsed.isna()).sum())
        if invalid_count:
            log_rows.append({
                "Hành động": "Giữ nguyên ngày lỗi",
                "Cột": str(column),
                "Số ô thay đổi": 0,
                "Quy tắc": f"Giữ nguyên {invalid_count} giá trị ngày không đọc được để người dùng quyết định.",
            })

    before_rows = len(cleaned)
    removed_rows = 0
    if remove_duplicates:
        duplicate_mask = cleaned.duplicated(keep="first")
        removed_rows = int(duplicate_mask.sum())
        cleaned = cleaned.loc[~duplicate_mask].copy()
        log_rows.append({
            "Hành động": "Xóa dòng trùng đã được xác nhận",
            "Cột": "Toàn bộ dòng",
            "Số ô thay đổi": removed_rows,
            "Quy tắc": f"Đã loại {removed_rows} dòng trùng hoàn toàn theo xác nhận của người dùng.",
        })

    if not log_rows:
        log_rows.append({
            "Hành động": "Không có thay đổi",
            "Cột": "—",
            "Số ô thay đổi": 0,
            "Quy tắc": "Không tìm thấy chuyển đổi nào được chọn có thể áp dụng; dữ liệu được giữ nguyên.",
        })

    log_df = pd.DataFrame(log_rows, columns=["Hành động", "Cột", "Số ô thay đổi", "Quy tắc"])
    summary = {
        "rows_before": int(before_rows),
        "rows_after": int(len(cleaned)),
        "duplicate_rows_removed": int(removed_rows),
        "logged_actions": int(len(log_df)),
    }
    return cleaned, log_df, summary


def format_number(value, decimals=0):
    if value is None:
        return "Chưa có dữ liệu phù hợp"

    try:
        number = float(value)

        if not pd.notna(number):
            return "Chưa có dữ liệu phù hợp"

        if decimals == 0 and number.is_integer():
            return f"{int(number):,}"

        return f"{number:,.{decimals}f}"

    except (TypeError, ValueError):
        return "Chưa có dữ liệu phù hợp"



def parse_date_series(series):
    """Parse ISO dates reliably and fall back to day-first for legacy formats."""
    text = series.astype("string").str.strip()
    parsed = pd.to_datetime(text, errors="coerce", format="mixed")
    # Fallback for environments / values where mixed parsing could not infer a date.
    missing = parsed.isna() & text.notna() & text.ne("")
    if missing.any():
        parsed.loc[missing] = pd.to_datetime(
            text.loc[missing], errors="coerce", dayfirst=True
        )
    return parsed


def filter_business_data(
    df,
    date_col=None,
    employee_col=None,
    start_date=None,
    end_date=None,
    selected_employees=None,
):
    """Lọc theo ngày và nhân viên; không sửa dữ liệu gốc."""
    filtered = df.copy()

    if date_col and (start_date is not None or end_date is not None):
        parsed_dates = parse_date_series(filtered[date_col])

        # Khi lọc theo ngày, loại dòng có ngày không hợp lệ.
        valid_date_mask = parsed_dates.notna()

        if start_date is not None:
            valid_date_mask &= parsed_dates.dt.date >= start_date

        if end_date is not None:
            valid_date_mask &= parsed_dates.dt.date <= end_date

        filtered = filtered.loc[valid_date_mask].copy()

    if employee_col and selected_employees is not None:
        selected_normalized = {str(value).strip().casefold() for value in selected_employees}
        employee_values = filtered[employee_col].astype("string").str.strip().str.casefold()
        filtered = filtered.loc[employee_values.isin(selected_normalized)].copy()

    return filtered


def get_business_metrics(df):
    """
    Tính KPI từ chính file CSV đã tải lên.
    Không có cột phù hợp thì trả về None, không giả lập số liệu.
    """
    metrics = {
        "revenue_column": find_column(df, REVENUE_ALIASES),
        "orders_column": find_column(df, ORDER_ALIASES),
        "employee_column": find_column(df, EMPLOYEE_ALIASES),
        "date_column": find_column(df, DATE_ALIASES),
    }

    revenue_col = metrics["revenue_column"]
    orders_col = metrics["orders_column"]
    employee_col = metrics["employee_column"]
    date_col = metrics["date_column"]

    metrics["total_revenue"] = None
    metrics["total_orders"] = None
    metrics["average_order_value"] = None
    metrics["employee_count"] = None
    metrics["revenue_valid_rows"] = None
    metrics["orders_valid_rows"] = None
    metrics["daily_revenue"] = None
    metrics["employee_revenue"] = None
    metrics["revenue_share"] = None

    revenue_values = None
    order_values = None

    if revenue_col is not None:
        revenue_values = to_numeric_series(df[revenue_col])
        valid_revenue = revenue_values.dropna()

        metrics["revenue_valid_rows"] = int(valid_revenue.size)

        if not valid_revenue.empty:
            metrics["total_revenue"] = float(valid_revenue.sum())

    if orders_col is not None:
        order_values = to_numeric_series(df[orders_col])
        valid_orders = order_values.dropna()

        metrics["orders_valid_rows"] = int(valid_orders.size)

        if not valid_orders.empty:
            metrics["total_orders"] = float(valid_orders.sum())

    # Chỉ tính giá trị trung bình mỗi đơn nếu có đủ cả hai tổng.
    if (
        metrics["total_revenue"] is not None
        and metrics["total_orders"] is not None
        and metrics["total_orders"] > 0
    ):
        metrics["average_order_value"] = (
            metrics["total_revenue"] / metrics["total_orders"]
        )

    if employee_col is not None:
        employee_values = (
            df[employee_col]
            .dropna()
            .astype(str)
            .str.strip()
        )
        employee_values = employee_values[employee_values != ""]

        if not employee_values.empty:
            metrics["employee_count"] = int(
                employee_values.nunique()
            )

    # Phân tích doanh thu theo nhân viên từ cột doanh thu và nhân viên.
    if (
        revenue_col is not None
        and employee_col is not None
        and revenue_values is not None
    ):
        employee_df = pd.DataFrame({
            "employee": df[employee_col].astype("string"),
            "revenue": revenue_values,
        }).dropna(subset=["employee", "revenue"])

        if not employee_df.empty:
            employee_df = employee_df[
                employee_df["employee"].str.strip() != ""
            ]

            if not employee_df.empty:
                employee_df = (
                    employee_df.groupby(
                        "employee",
                        as_index=False,
                    )["revenue"]
                    .sum()
                    .sort_values("revenue", ascending=False)
                )

                total = employee_df["revenue"].sum()

                if total != 0:
                    employee_df["revenue_share_pct"] = (
                        employee_df["revenue"] / total * 100
                    )
                else:
                    employee_df["revenue_share_pct"] = None

                metrics["employee_revenue"] = employee_df

    # Phân tích doanh thu theo ngày khi nhận diện được cột ngày.
    if (
        revenue_col is not None
        and date_col is not None
        and revenue_values is not None
    ):
        daily_df = pd.DataFrame({
            "date": parse_date_series(df[date_col]).dt.normalize(),
            "revenue": revenue_values,
        }).dropna(subset=["date", "revenue"])

        if not daily_df.empty:
            daily_df = (
                daily_df.groupby("date", as_index=False)["revenue"]
                .sum()
                .sort_values("date")
            )
            metrics["daily_revenue"] = daily_df

    return metrics


def summarize_business_period(df):
    """Tóm tắt KPI có thể so sánh; mã đơn được đếm distinct thay vì cộng số."""
    revenue_col = find_column(df, REVENUE_ALIASES)
    order_id_col = find_column(df, ["ma_don_hang", "order_id", "transaction_id", "order_number", "transaction_number"])
    order_col = find_column(df, ORDER_ALIASES)
    date_col = find_column(df, DATE_ALIASES)
    employee_col = find_column(df, EMPLOYEE_ALIASES)
    product_col = find_column(df, PRODUCT_ALIASES)

    revenue = to_numeric_series(df[revenue_col]).dropna() if revenue_col else pd.Series(dtype=float)
    total_revenue = float(revenue.sum()) if not revenue.empty else None

    if order_id_col:
        order_values = df[order_id_col].dropna().astype("string").str.strip()
        order_values = order_values[order_values.ne("")]
        total_orders = int(order_values.nunique())
    elif order_col:
        order_values = df[order_col].dropna().astype("string").str.strip()
        order_values = order_values[order_values.ne("")]
        numeric_orders = to_numeric_series(df[order_col]).dropna()
        total_orders = float(numeric_orders.sum()) if not numeric_orders.empty else int(order_values.nunique())
    else:
        total_orders = int(len(df)) if not df.empty else 0

    result = {
        "rows": int(len(df)),
        "revenue": total_revenue,
        "orders": total_orders,
        "aov": (total_revenue / total_orders) if total_revenue is not None and total_orders and total_orders > 0 else None,
        "active_employees": int(df[employee_col].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()) if employee_col else None,
        "date_col": date_col,
        "revenue_col": revenue_col,
        "order_col": order_col,
    }

    if date_col:
        dates = parse_date_series(df[date_col]).dropna()
        result["date_min"] = dates.min().date().isoformat() if not dates.empty else None
        result["date_max"] = dates.max().date().isoformat() if not dates.empty else None
    else:
        result["date_min"] = result["date_max"] = None

    if revenue_col and employee_col and not df.empty:
        temp = pd.DataFrame({"employee": df[employee_col].astype("string").str.strip(), "revenue": to_numeric_series(df[revenue_col])}).dropna()
        temp = temp[temp["employee"].ne("")]
        result["employee_revenue"] = temp.groupby("employee")["revenue"].sum().sort_values(ascending=False).to_dict()
    else:
        result["employee_revenue"] = {}

    if revenue_col and product_col and not df.empty:
        temp = pd.DataFrame({"product": df[product_col].astype("string").str.strip(), "revenue": to_numeric_series(df[revenue_col])}).dropna()
        temp = temp[temp["product"].ne("")]
        result["product_revenue"] = temp.groupby("product")["revenue"].sum().sort_values(ascending=False).to_dict()
    else:
        result["product_revenue"] = {}
    return result


def growth_pct(current, previous):
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def money_text(value):
    return "Chưa có dữ liệu" if value is None or pd.isna(value) else f"{value:,.0f} đ"


def make_chart_layout(fig, title):
    fig.update_layout(
        title={"text": title, "font": {"size": 18}},
        template="plotly_dark",
        paper_bgcolor="#111c30",
        plot_bgcolor="#111c30",
        font={"family": "Arial", "color": "#cbd5e1", "size": 12},
        margin=dict(l=20, r=30, t=65, b=35),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#263852")
    return fig


def section_heading(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def show_json_download(result):
    st.download_button(
        "⬇️ Tải báo cáo JSON",
        data=json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        file_name="data_analysis_report.json",
        mime="application/json",
        use_container_width=True,
    )


# =========================================================
# 4. SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## 📊 Data Analyst")
    st.caption("AI-Agents-Automation · Portfolio Project")
    st.divider()

    st.markdown("### Kết nối backend")

    st.session_state.api_base = st.text_input(
        "FastAPI URL",
        value=st.session_state.api_base,
    )

    if st.button("Kiểm tra kết nối", use_container_width=True):
        try:
            response = requests.get(
                api_url("/health"),
                timeout=5,
            )
            response.raise_for_status()
            st.session_state.backend_status = "online"
            st.success("Backend hoạt động bình thường.")
        except requests.RequestException:
            st.session_state.backend_status = "offline"
            st.error("Không kết nối được backend.")

    if st.session_state.backend_status == "online":
        st.markdown("🟢 Backend đang hoạt động")
    elif st.session_state.backend_status == "offline":
        st.markdown("🔴 Backend chưa kết nối")
    else:
        st.markdown("⚪ Chưa kiểm tra kết nối")

    st.divider()
    st.markdown("### Tài khoản")

    if st.session_state.access_token:
        st.success("Đã đăng nhập")
        st.caption(st.session_state.user_email or "")

        if st.button("Đăng xuất", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.user_email = None
            st.session_state.analysis_result = None
            st.session_state.filtered_ai_result = None
            st.session_state.filtered_ai_signature = None
            st.session_state.source_df = None
            st.session_state.last_filename = None
            st.rerun()
    else:
        st.info("Chưa đăng nhập")

    st.divider()
    st.markdown("### Công nghệ")
    st.markdown("Python · Pandas · Streamlit · FastAPI · Ollama")
    st.caption("Phân tích dữ liệu · KPI · Data Quality · AI cục bộ")


# =========================================================
# 5. HEADER
# =========================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">AI-AGENTS-AUTOMATION · ANALYTICS WORKSPACE</div>
        <div class="hero-title">📊 AI Data Analyst Dashboard</div>
        <div class="hero-subtitle">
            Biến dữ liệu thô thành insight rõ ràng — theo dõi KPI kinh doanh,
            kiểm soát chất lượng dữ liệu và hỗ trợ diễn giải bằng AI cục bộ.
        </div>
        <div class="hero-pills">
            <span class="hero-pill">BUSINESS KPI</span>
            <span class="hero-pill">DATA QUALITY</span>
            <span class="hero-pill">INTERACTIVE ANALYTICS</span>
            <span class="hero-pill">LOCAL AI · OLLAMA</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 6. ĐĂNG NHẬP / ĐĂNG KÝ
# =========================================================
if not st.session_state.access_token:
    section_heading(
        "🔐 Đăng nhập hệ thống",
        "Đăng nhập để sử dụng API phân tích dữ liệu.",
    )

    login_tab, register_tab = st.tabs(
        ["Đăng nhập", "Tạo tài khoản"]
    )

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mật khẩu", type="password")
            login_submit = st.form_submit_button(
                "Đăng nhập",
                type="primary",
                use_container_width=True,
            )

        if login_submit:
            if not email.strip() or not password:
                st.warning("Vui lòng nhập email và mật khẩu.")
            else:
                try:
                    response = requests.post(
                        api_url("/api/v1/auth/login"),
                        json={
                            "email": email.strip(),
                            "password": password,
                        },
                        timeout=30,
                    )

                    if response.status_code == 200:
                        payload = response.json()
                        st.session_state.access_token = payload[
                            "access_token"
                        ]
                        st.session_state.user_email = email.strip()
                        st.success("Đăng nhập thành công.")
                        st.rerun()
                    else:
                        show_api_error(response)

                except requests.RequestException as exc:
                    st.error(f"Lỗi kết nối API: {exc}")

    with register_tab:
        with st.form("register_form"):
            new_email = st.text_input("Email đăng ký")
            new_password = st.text_input(
                "Mật khẩu mới",
                type="password",
            )
            confirm_password = st.text_input(
                "Nhập lại mật khẩu",
                type="password",
            )
            register_submit = st.form_submit_button(
                "Tạo tài khoản",
                use_container_width=True,
            )

        if register_submit:
            if not new_email.strip():
                st.warning("Vui lòng nhập email.")
            elif len(new_password) < 8 or len(new_password) > 72:
                st.warning("Mật khẩu phải dài từ 8 đến 72 ký tự.")
            elif new_password != confirm_password:
                st.warning("Hai mật khẩu không khớp.")
            else:
                try:
                    response = requests.post(
                        api_url("/api/v1/auth/register"),
                        json={
                            "email": new_email.strip(),
                            "password": new_password,
                        },
                        timeout=30,
                    )

                    if response.status_code == 201:
                        st.success(
                            "Tạo tài khoản thành công. "
                            "Hãy chuyển sang tab Đăng nhập."
                        )
                    else:
                        show_api_error(response)

                except requests.RequestException as exc:
                    st.error(f"Lỗi kết nối API: {exc}")

    st.stop()


# =========================================================
# 7. TẢI CSV VÀ PHÂN TÍCH
# =========================================================
section_heading(
    "📁 Dữ liệu đầu vào",
    "Tải CSV lên để tính toán KPI từ dữ liệu thực tế.",
)

uploaded_file = st.file_uploader(
    "Chọn file CSV",
    type=["csv"],
    help="Giới hạn 5 MB.",
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    f1, f2 = st.columns(2)
    f1.metric("Tên file", uploaded_file.name)
    f2.metric("Dung lượng", f"{len(file_bytes) / 1024:.1f} KB")

    if len(file_bytes) > 5 * 1024 * 1024:
        st.error("File vượt quá giới hạn 5 MB.")
        st.stop()

    try:
        preview_df = read_csv_safely(file_bytes)

        with st.expander("👁️ Xem trước dữ liệu", expanded=False):
            st.dataframe(
                preview_df.head(100),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                f"{len(preview_df):,} dòng · "
                f"{len(preview_df.columns):,} cột"
            )

    except Exception as exc:
        st.error(f"Không đọc được CSV: {exc}")
        st.stop()

    if st.button(
        "🚀 Phân tích dữ liệu",
        type="primary",
        use_container_width=True,
    ):
        headers = {
            "Authorization": (
                f"Bearer {st.session_state.access_token}"
            )
        }
        files = {
            "file": (
                uploaded_file.name,
                file_bytes,
                "text/csv",
            )
        }

        try:
            with st.spinner("Đang phân tích dữ liệu..."):
                response = requests.post(
                    api_url("/api/v1/data-insights/analyze-csv"),
                    headers=headers,
                    files=files,
                    timeout=180,
                )

            if response.status_code == 401:
                st.error(
                    "Phiên đăng nhập không hợp lệ. "
                    "Hãy đăng xuất rồi đăng nhập lại."
                )
            elif response.status_code != 200:
                show_api_error(response)
            else:
                st.session_state.analysis_result = response.json()
                st.session_state.filtered_ai_result = None
                st.session_state.filtered_ai_signature = None
                st.session_state.source_df = preview_df.copy()
                st.session_state.last_filename = uploaded_file.name
                st.session_state.cleaned_df = None
                st.session_state.cleaning_log = None
                st.session_state.cleaned_source_signature = None
                st.success("Phân tích thành công.")

        except requests.Timeout:
            st.error("Yêu cầu quá thời gian chờ. Kiểm tra backend và Ollama.")
        except requests.RequestException as exc:
            st.error(f"Lỗi kết nối API: {exc}")
        except ValueError:
            st.error("API không trả về JSON hợp lệ.")


# =========================================================
# 8. HIỂN THỊ KẾT QUẢ VÀ KPI KINH DOANH
# =========================================================
result = st.session_state.analysis_result
source_df = st.session_state.source_df

if result:
    report = result.get("report") or {}
    analysis = result.get("analysis") or {}

    if source_df is None or source_df.empty:
        st.warning(
            "Không còn dữ liệu CSV gốc trong phiên hiện tại. "
            "Hãy tải lại file và phân tích lại để tính KPI kinh doanh."
        )
        st.stop()

    
    # Nhận diện cột dùng để lọc
    date_col = find_column(source_df, DATE_ALIASES)
    employee_col = find_column(source_df, EMPLOYEE_ALIASES)

    st.divider()
    section_heading(
        "🎛️ Bộ lọc phân tích",
        "Chọn khoảng thời gian và nhân viên. KPI kinh doanh "
        "và biểu đồ bên dưới sẽ cập nhật theo lựa chọn.",
    )

    filtered_df = source_df.copy()

    with st.container(border=True):
        start_date = None
        end_date = None

        if date_col:
            parsed_dates = parse_date_series(source_df[date_col]).dropna()

            if not parsed_dates.empty:
                min_date = parsed_dates.min().date()
                max_date = parsed_dates.max().date()
                period_mode = st.radio(
                    "Chế độ lọc thời gian",
                    ["Tùy chỉnh ngày", "Theo tháng", "Theo quý"],
                    horizontal=True,
                    key="period_filter_mode",
                    help="Chọn tháng/quý để phân tích theo kỳ báo cáo chuẩn, hoặc dùng ngày tùy chỉnh.",
                )

                if period_mode == "Tùy chỉnh ngày":
                    f1, f2 = st.columns(2)
                    with f1:
                        start_date = st.date_input(
                            "Từ ngày", value=min_date, min_value=min_date,
                            max_value=max_date, key="filter_start_date",
                        )
                    with f2:
                        end_date = st.date_input(
                            "Đến ngày", value=max_date, min_value=min_date,
                            max_value=max_date, key="filter_end_date",
                        )
                else:
                    available_years = sorted(parsed_dates.dt.year.unique().tolist())
                    selected_year = st.selectbox(
                        "Năm báo cáo", available_years,
                        index=len(available_years)-1, key="period_filter_year",
                    )
                    if period_mode == "Theo tháng":
                        month_options = list(range(1, 13))
                        month_names = {i: f"{i:02d} — {pd.Timestamp(2000, i, 1).strftime('%B')}" for i in month_options}
                        selected_month = st.selectbox(
                            "Tháng", month_options, index=(int(parsed_dates.max().month) - 1) if selected_year == max(available_years) else 0,
                            format_func=lambda m: month_names[m], key="period_filter_month",
                        )
                        start_date = pd.Timestamp(int(selected_year), int(selected_month), 1).date()
                        end_date = (pd.Timestamp(start_date) + pd.offsets.MonthEnd(0)).date()
                    else:
                        selected_quarter = st.selectbox(
                            "Quý", [1, 2, 3, 4],
                            index=(int(parsed_dates.max().quarter) - 1) if selected_year == max(available_years) else 0,
                            format_func=lambda q: f"Quý {q}", key="period_filter_quarter",
                        )
                        start_month = (int(selected_quarter) - 1) * 3 + 1
                        start_date = pd.Timestamp(int(selected_year), start_month, 1).date()
                        end_date = (pd.Timestamp(start_date) + pd.offsets.QuarterEnd(0)).date()
                    st.caption(f"Kỳ báo cáo: {start_date:%d/%m/%Y} – {end_date:%d/%m/%Y}. Ngày ngoài phạm vi dữ liệu sẽ tự không có giao dịch.")

                if start_date > end_date:
                    st.error("Ngày bắt đầu không được sau ngày kết thúc.")
                    st.stop()
            else:
                st.warning("Không thể đọc dữ liệu ngày trong cột đã nhận diện.")
        else:
            st.info("Không tìm thấy cột ngày. Bộ lọc thời gian chưa khả dụng.")

        selected_employees = None

        if employee_col:
            employee_options = sorted(
                source_df[employee_col]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[lambda s: s != ""]
                .unique()
                .tolist()
            )

            selected_employees = st.multiselect(
                "Nhân viên",
                options=employee_options,
                default=employee_options,
                help="Chọn một hoặc nhiều nhân viên để phân tích.",
            )
        else:
            st.info(
                "Không tìm thấy cột nhân viên. "
                "Bộ lọc nhân viên chưa khả dụng."
            )

        reset_filter = st.button(
            "↩️ Đặt lại bộ lọc",
            use_container_width=True,
        )

        if reset_filter:
            st.session_state.pop("filter_start_date", None)
            st.session_state.pop("filter_end_date", None)
            st.rerun()

    if employee_col and selected_employees == []:
        filtered_df = source_df.iloc[0:0].copy()
    else:
        filtered_df = filter_business_data(
            source_df,
            date_col=date_col,
            employee_col=employee_col,
            start_date=start_date,
            end_date=end_date,
            selected_employees=selected_employees,
        )

    metrics = get_business_metrics(filtered_df)

    st.caption(
        f"Đang phân tích {len(filtered_df):,} / "
        f"{len(source_df):,} dòng dữ liệu."
    )

    # Generate AI commentary for the exact filtered rows, not the original CSV.
    filtered_csv_bytes = filtered_df.to_csv(index=False).encode("utf-8-sig")
    filtered_signature = hashlib.sha256(filtered_csv_bytes).hexdigest()
    with st.container(border=True):
        st.markdown("**🤖 Diễn giải AI theo bộ lọc hiện tại**")
        st.caption(
            "Nhấn nút để gửi các dòng đang lọc đến API phân tích. "
            "Ollama chạy cục bộ, không cần API key trả phí."
        )
        if st.button(
            "Tạo diễn giải AI cho dữ liệu đang lọc",
            type="primary",
            use_container_width=True,
            disabled=filtered_df.empty,
            key="analyze_filtered_with_ai",
        ):
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            try:
                with st.spinner("Đang phân tích dữ liệu đã lọc bằng Ollama..."):
                    response = requests.post(
                        api_url("/api/v1/data-insights/analyze-csv"),
                        headers=headers,
                        files={"file": ("filtered_data.csv", filtered_csv_bytes, "text/csv")},
                        timeout=180,
                    )
                if response.status_code == 200:
                    st.session_state.filtered_ai_result = response.json()
                    st.session_state.filtered_ai_signature = filtered_signature
                    st.success("Đã tạo diễn giải cho đúng dữ liệu đang lọc.")
                    st.rerun()
                else:
                    show_api_error(response)
            except requests.Timeout:
                st.error("Yêu cầu AI quá thời gian chờ. Kiểm tra log backend và Ollama.")
            except requests.RequestException as exc:
                st.error(f"Không kết nối được API phân tích: {exc}")

    if filtered_df.empty:
        st.info("Bộ lọc hiện không có dòng dữ liệu; hãy chọn ít nhất một dòng để phân tích AI.")
    elif st.session_state.filtered_ai_signature != filtered_signature:
        st.caption("Chưa có diễn giải AI mới cho bộ lọc hiện tại. Nhấn nút phía trên để cập nhật.")

    # Render as vertically stacked sections rather than tabs so users can see
    # every analysis section immediately by scrolling down the dashboard.
    dashboard_tab_overview = st.container()
    dashboard_tab_trend = st.container()
    dashboard_tab_employee = st.container()
    dashboard_tab_product = st.container()
    dashboard_tab_quality = st.container()

    st.markdown(
        "**Các phần phân tích bên dưới:** Tổng quan kinh doanh → Xu hướng doanh thu "
        "→ Hiệu suất nhân viên → Phân tích sản phẩm → Chất lượng dữ liệu."
    )

    with dashboard_tab_overview:
        st.divider()
        section_heading(
            "📈 Tổng quan dữ liệu",
            f"File: {st.session_state.last_filename or 'CSV'}",
        )

        missing = report.get("missing_by_column") or {}
        missing_count = sum(
            value for value in missing.values()
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
        ) if isinstance(missing, dict) else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric(
            "Số dòng",
            format_number(report.get("row_count")),
        )
        k2.metric(
            "Số cột",
            format_number(report.get("column_count")),
        )
        k3.metric(
            "Dòng trùng lặp",
            format_number(report.get("duplicate_rows")),
        )
        k4.metric(
            "Giá trị thiếu",
            format_number(missing_count),
        )

        # -----------------------------------------------------
        # BUSINESS KPIs
        # -----------------------------------------------------
        st.divider()
        section_heading(
            "💼 KPI kinh doanh",
            "Chỉ tính chỉ số khi tìm thấy cột phù hợp trong CSV. "
            "Không có dữ liệu phù hợp sẽ không hiển thị số giả.",
        )

        revenue_col = metrics["revenue_column"]
        orders_col = metrics["orders_column"]
        employee_col = metrics["employee_column"]
        date_col = metrics["date_column"]

        b1, b2, b3, b4 = st.columns(4)

        with b1:
            st.metric(
                "Tổng doanh thu",
                (
                    format_number(metrics["total_revenue"])
                    if revenue_col
                    else "Chưa có dữ liệu"
                ),
            )
            st.caption(
                f"Cột: {revenue_col}"
                if revenue_col
                else "Không tìm thấy cột doanh thu"
            )

        with b2:
            st.metric(
                "Tổng đơn hàng",
                (
                    format_number(metrics["total_orders"])
                    if orders_col
                    else "Chưa có dữ liệu"
                ),
            )
            st.caption(
                f"Cột: {orders_col}"
                if orders_col
                else "Không tìm thấy cột đơn hàng"
            )

        with b3:
            st.metric(
                "Doanh thu / đơn",
                (
                    format_number(metrics["average_order_value"], 2)
                    if metrics["average_order_value"] is not None
                    else "Chưa đủ dữ liệu"
                ),
            )
            st.caption("Tổng doanh thu ÷ tổng đơn hàng")

        with b4:
            st.metric(
                "Số nhân viên",
                (
                    format_number(metrics["employee_count"])
                    if employee_col
                    else "Chưa có dữ liệu"
                ),
            )
            st.caption(
                f"Cột: {employee_col}"
                if employee_col
                else "Không tìm thấy cột nhân viên"
            )

        if revenue_col is None or orders_col is None:
            absent = []
            if revenue_col is None:
                absent.append("doanh thu")
            if orders_col is None:
                absent.append("đơn hàng")

            st.info(
                "Chưa tính được tất cả KPI kinh doanh vì không nhận diện "
                f"được cột: {', '.join(absent)}. "
                "Hãy kiểm tra tên cột CSV hoặc bổ sung alias trong code."
            )

        # -----------------------------------------------------
        # BUSINESS DATA QUALITY
        # -----------------------------------------------------
        with st.expander("🔎 Cột dữ liệu được nhận diện"):
            st.write({
                "Cột doanh thu": revenue_col,
                "Cột đơn hàng": orders_col,
                "Cột nhân viên": employee_col,
                "Cột ngày": date_col,
            })

            st.caption(
                "Việc nhận diện dựa trên tên cột. "
                "Hãy kiểm tra ý nghĩa cột trước khi dùng kết quả "
                "cho báo cáo kinh doanh chính thức."
            )

            st.write(
                "Số dòng có doanh thu hợp lệ:",
                (
                    format_number(metrics["revenue_valid_rows"])
                    if metrics["revenue_valid_rows"] is not None
                    else "Chưa có dữ liệu"
                ),
            )
            st.write(
                "Số dòng có đơn hàng hợp lệ:",
                (
                    format_number(metrics["orders_valid_rows"])
                    if metrics["orders_valid_rows"] is not None
                    else "Chưa có dữ liệu"
                ),
            )

    with dashboard_tab_employee:
        # -----------------------------------------------------
        # EMPLOYEE REVENUE ANALYSIS
        # -----------------------------------------------------
        employee_revenue = metrics["employee_revenue"]

        st.divider()
        section_heading(
            "👥 Hiệu quả theo nhân viên",
            "Tổng hợp doanh thu từ các dòng có nhân viên và doanh thu hợp lệ.",
        )

        if employee_revenue is not None and not employee_revenue.empty:
            display_employee = employee_revenue.copy()
            display_employee["revenue"] = display_employee["revenue"].map(
                lambda x: format_number(x)
            )
            display_employee["revenue_share_pct"] = (
                employee_revenue["revenue_share_pct"].map(
                    lambda x: f"{x:.2f}%"
                    if pd.notna(x)
                    else "Không xác định"
                )
            )
            display_employee = display_employee.rename(columns={
                "employee": "Nhân viên",
                "revenue": "Tổng doanh thu",
                "revenue_share_pct": "Tỷ trọng doanh thu",
            })

            st.dataframe(
                display_employee,
                use_container_width=True,
                hide_index=True,
            )

            fig = px.bar(
                employee_revenue.sort_values("revenue"),
                x="revenue",
                y="employee",
                orientation="h",
                text="revenue",
                labels={
                    "employee": "Nhân viên",
                    "revenue": "Tổng doanh thu",
                },
            )
            fig.update_traces(
                texttemplate="%{x:,.0f}",
                textposition="outside",
                cliponaxis=False,
            )
            fig = make_chart_layout(
                fig,
                "Tổng doanh thu theo nhân viên",
            )
            st.plotly_chart(fig, use_container_width=True)

            top = employee_revenue.iloc[0]
            st.success(
                f"Doanh thu cao nhất trong dữ liệu: "
                f"{top['employee']} — {format_number(top['revenue'])}."
            )
        else:
            st.info(
                "Chưa thể tạo phân tích doanh thu theo nhân viên. "
                "Cần có cả cột nhân viên và cột doanh thu nhận diện được."
            )

    with dashboard_tab_product:
        section_heading(
            "📦 Phân tích sản phẩm",
            "Xếp hạng sản phẩm và danh mục theo doanh thu trên dữ liệu đã lọc. Chỉ hiển thị chỉ số khi cột tương ứng tồn tại.",
        )
        product_col = find_column(filtered_df, PRODUCT_ALIASES)
        category_col = find_column(filtered_df, CATEGORY_ALIASES)
        quantity_col = find_column(filtered_df, QUANTITY_ALIASES)
        product_revenue_col = metrics.get("revenue_column")

        if product_col and product_revenue_col:
            product_work = pd.DataFrame({
                "product": filtered_df[product_col].astype("string").str.strip(),
                "revenue": to_numeric_series(filtered_df[product_revenue_col]),
            })
            if quantity_col:
                product_work["quantity"] = to_numeric_series(filtered_df[quantity_col])
            product_work = product_work.dropna(subset=["product", "revenue"])
            product_work = product_work[product_work["product"].ne("")]

            if not product_work.empty:
                agg = {"revenue": "sum"}
                if quantity_col:
                    agg["quantity"] = "sum"
                product_summary = (
                    product_work.groupby("product", as_index=False)
                    .agg(agg)
                    .sort_values("revenue", ascending=False)
                )
                total_product_revenue = product_summary["revenue"].sum()
                product_summary["revenue_share_pct"] = (
                    product_summary["revenue"] / total_product_revenue * 100
                    if total_product_revenue != 0 else 0
                )
                top_product = product_summary.iloc[0]
                p1, p2, p3 = st.columns(3)
                p1.metric("Số sản phẩm", format_number(product_summary["product"].nunique()))
                p2.metric("Sản phẩm dẫn đầu", str(top_product["product"])[:28], help=f"Doanh thu: {format_number(top_product['revenue'])}")
                p3.metric("Tỷ trọng sản phẩm dẫn đầu", f"{top_product['revenue_share_pct']:.1f}%")

                chart_col, table_col = st.columns([1.2, 1])
                top_n = min(10, len(product_summary))
                with chart_col:
                    fig_product = px.bar(
                        product_summary.head(top_n).sort_values("revenue"),
                        x="revenue", y="product", orientation="h",
                        text="revenue", labels={"product": "Sản phẩm", "revenue": "Doanh thu"},
                    )
                    fig_product.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
                    fig_product = make_chart_layout(fig_product, f"Top {top_n} sản phẩm theo doanh thu")
                    fig_product.update_layout(showlegend=False, height=max(360, 34 * top_n + 120))
                    st.plotly_chart(fig_product, use_container_width=True)
                with table_col:
                    display_product = product_summary.copy()
                    display_product["revenue"] = display_product["revenue"].map(lambda value: format_number(value))
                    display_product["revenue_share_pct"] = display_product["revenue_share_pct"].map(lambda value: f"{value:.2f}%")
                    if quantity_col:
                        display_product["quantity"] = display_product["quantity"].map(lambda value: format_number(value))
                    display_product = display_product.rename(columns={
                        "product": "Sản phẩm", "revenue": "Doanh thu",
                        "quantity": "Số lượng", "revenue_share_pct": "Tỷ trọng doanh thu",
                    })
                    st.markdown("#### Bảng xếp hạng")
                    st.dataframe(display_product.head(20), use_container_width=True, hide_index=True)

                # PARETO 80/20 ANALYSIS: positive revenue only so returns/negative
                # adjustments do not make contribution shares misleading.
                st.divider()
                section_heading(
                    "🎯 Phân tích Pareto 80/20",
                    "Xác định nhóm sản phẩm đóng góp phần lớn doanh thu. Phân tích này chỉ dùng sản phẩm có doanh thu dương; doanh thu âm/hoàn trả cần được phân tích riêng.",
                )
                pareto = product_summary.loc[product_summary["revenue"] > 0].copy()
                if not pareto.empty:
                    pareto = pareto.sort_values("revenue", ascending=False).reset_index(drop=True)
                    pareto_total = float(pareto["revenue"].sum())
                    pareto["contribution_pct"] = pareto["revenue"] / pareto_total * 100
                    pareto["cumulative_pct"] = pareto["contribution_pct"].cumsum()
                    products_for_80 = int((pareto["cumulative_pct"] < 80).sum() + 1)
                    products_for_80 = min(products_for_80, len(pareto))
                    share_for_80 = float(pareto.iloc[products_for_80 - 1]["cumulative_pct"])
                    q1, q2, q3 = st.columns(3)
                    q1.metric("Sản phẩm có doanh thu dương", format_number(len(pareto)))
                    q2.metric("Số sản phẩm chạm mốc 80%", format_number(products_for_80))
                    q3.metric("Tỷ trọng nhóm dẫn đầu", f"{share_for_80:.1f}%")
                    fig_pareto = px.bar(
                        pareto.head(20), x="product", y="contribution_pct",
                        labels={"product": "Sản phẩm", "contribution_pct": "Tỷ trọng doanh thu (%)"},
                        hover_data={"cumulative_pct": ":.2f", "revenue": ":,.0f"},
                    )
                    fig_pareto = make_chart_layout(fig_pareto, "Đóng góp doanh thu theo sản phẩm (Top 20)")
                    fig_pareto.update_layout(xaxis_tickangle=-35)
                    st.plotly_chart(fig_pareto, use_container_width=True)
                    st.dataframe(
                        pareto.assign(
                            revenue=pareto["revenue"].map(format_number),
                            contribution_pct=pareto["contribution_pct"].map(lambda v: f"{v:.2f}%"),
                            cumulative_pct=pareto["cumulative_pct"].map(lambda v: f"{v:.2f}%"),
                        ).rename(columns={"product":"Sản phẩm", "revenue":"Doanh thu", "contribution_pct":"Tỷ trọng", "cumulative_pct":"Tỷ trọng lũy kế"}).head(30),
                        use_container_width=True, hide_index=True,
                    )
                    st.info(
                        f"Insight Pareto: {products_for_80} sản phẩm đầu bảng đóng góp {share_for_80:.1f}% doanh thu dương. "
                        "Ưu tiên kiểm tra mức tồn kho, tỷ lệ hết hàng và hiệu quả khuyến mãi của nhóm này; đây là gợi ý cần xác minh, không phải kết luận nhân quả."
                    )
                else:
                    st.info("Chưa có sản phẩm nào có doanh thu dương để tính Pareto.")

                if category_col:
                    category_work = pd.DataFrame({
                        "category": filtered_df[category_col].astype("string").str.strip(),
                        "revenue": to_numeric_series(filtered_df[product_revenue_col]),
                    }).dropna(subset=["category", "revenue"])
                    category_work = category_work[category_work["category"].ne("")]
                    if not category_work.empty:
                        category_summary = category_work.groupby("category", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
                        fig_category = px.bar(
                            category_summary, x="category", y="revenue",
                            labels={"category": "Danh mục", "revenue": "Doanh thu"},
                        )
                        fig_category = make_chart_layout(fig_category, "Doanh thu theo danh mục sản phẩm")
                        fig_category.update_layout(xaxis_tickangle=-20)
                        st.plotly_chart(fig_category, use_container_width=True)
            else:
                st.info("Không có dòng sản phẩm và doanh thu hợp lệ trong phạm vi bộ lọc hiện tại.")
        else:
            missing_product_fields = []
            if not product_col:
                missing_product_fields.append("tên sản phẩm")
            if not product_revenue_col:
                missing_product_fields.append("doanh thu")
            st.info(
                "Chưa thể phân tích sản phẩm vì không nhận diện được cột: "
                + ", ".join(missing_product_fields)
                + ". Hãy kiểm tra tên cột CSV hoặc bổ sung alias trong code."
            )
        if quantity_col:
            st.caption(f"Cột số lượng được nhận diện: {quantity_col}")
        if category_col:
            st.caption(f"Cột danh mục được nhận diện: {category_col}")

    with dashboard_tab_trend:
        # -----------------------------------------------------
        # DAILY REVENUE ANALYSIS
        # -----------------------------------------------------
        st.divider()
        section_heading(
            "📅 Doanh thu theo ngày",
            "Tổng hợp theo ngày nếu CSV có cột ngày và doanh thu hợp lệ.",
        )

        daily_revenue = metrics["daily_revenue"]

        if daily_revenue is not None and not daily_revenue.empty:
            fig = px.line(
                daily_revenue,
                x="date",
                y="revenue",
                markers=True,
                labels={
                    "date": "Ngày",
                    "revenue": "Doanh thu",
                },
            )
            fig.update_traces(
                hovertemplate=(
                    "Ngày: %{x|%d/%m/%Y}<br>"
                    "Doanh thu: %{y:,.0f}<extra></extra>"
                )
            )
            fig = make_chart_layout(fig, "Xu hướng doanh thu theo ngày")
            st.plotly_chart(fig, use_container_width=True)

            highest = daily_revenue.loc[
                daily_revenue["revenue"].idxmax()
            ]
            lowest = daily_revenue.loc[
                daily_revenue["revenue"].idxmin()
            ]

            d1, d2 = st.columns(2)
            d1.metric(
                "Ngày doanh thu cao nhất",
                highest["date"].strftime("%d/%m/%Y"),
                help=f"Doanh thu: {format_number(highest['revenue'])}",
            )
            d2.metric(
                "Ngày doanh thu thấp nhất",
                lowest["date"].strftime("%d/%m/%Y"),
                help=f"Doanh thu: {format_number(lowest['revenue'])}",
            )
        else:
            st.info(
                "Chưa tạo được biểu đồ theo ngày. "
                "Cần có cột ngày và cột doanh thu được nhận diện."
            )

        # ROBUST ANOMALY SCREENING. A flagged date is a review candidate,
        # not proof of an error or an explanation for the business movement.
        st.divider()
        section_heading(
            "🚨 Cảnh báo ngày doanh thu bất thường",
            "Sàng lọc ngày có doanh thu khác biệt đáng kể so với lịch sử trong phạm vi lọc. Cần xác minh với dữ liệu khuyến mãi, tồn kho, hoàn trả và vận hành.",
        )
        if daily_revenue is not None and not daily_revenue.empty:
            anomaly_df = daily_revenue[["date", "revenue"]].copy().sort_values("date")
            anomaly_df["revenue"] = pd.to_numeric(anomaly_df["revenue"], errors="coerce")
            anomaly_df = anomaly_df.dropna(subset=["revenue"])
            if len(anomaly_df) >= 7:
                values = anomaly_df["revenue"].astype(float)
                median_value = float(values.median())
                abs_dev = (values - median_value).abs()
                mad = float(abs_dev.median())
                if mad > 0:
                    robust_z = 0.6745 * (values - median_value) / mad
                    anomaly_df["robust_score"] = robust_z
                    anomaly_df["reason"] = robust_z.map(lambda z: "Cao bất thường" if z > 3.5 else ("Thấp bất thường" if z < -3.5 else "Trong ngưỡng"))
                    flagged = anomaly_df[robust_z.abs() > 3.5].copy()
                    method_text = "Median Absolute Deviation (robust z-score > 3.5)"
                else:
                    q1v, q3v = float(values.quantile(0.25)), float(values.quantile(0.75))
                    iqr = q3v - q1v
                    lower_fence, upper_fence = q1v - 1.5 * iqr, q3v + 1.5 * iqr
                    anomaly_df["robust_score"] = float("nan")
                    anomaly_df["reason"] = values.map(lambda v: "Cao bất thường" if v > upper_fence else ("Thấp bất thường" if v < lower_fence else "Trong ngưỡng"))
                    flagged = anomaly_df[anomaly_df["reason"] != "Trong ngưỡng"].copy()
                    method_text = "Quy tắc IQR (ngoài Q1 − 1,5×IQR hoặc Q3 + 1,5×IQR)"
                if flagged.empty:
                    st.success("Chưa phát hiện ngày vượt ngưỡng sàng lọc trong dữ liệu hiện tại.")
                else:
                    st.warning(f"Phát hiện {len(flagged)} ngày cần kiểm tra. Đây là cảnh báo thống kê, không tự động có nghĩa dữ liệu sai.")
                    show_flagged = flagged.copy()
                    show_flagged["date"] = pd.to_datetime(show_flagged["date"]).dt.strftime("%d/%m/%Y")
                    show_flagged["revenue"] = show_flagged["revenue"].map(format_number)
                    show_flagged["robust_score"] = show_flagged["robust_score"].map(lambda v: f"{v:.2f}" if pd.notna(v) else "N/A")
                    st.dataframe(show_flagged.rename(columns={"date":"Ngày", "revenue":"Doanh thu", "robust_score":"Điểm bất thường", "reason":"Phân loại"}), use_container_width=True, hide_index=True)
                st.caption(f"Phương pháp: {method_text}. Chỉ chạy khi có ít nhất 7 ngày có dữ liệu. Các ngày không xuất hiện trong CSV không được tự xem là doanh thu bằng 0.")
            else:
                st.info(f"Cần tối thiểu 7 ngày có doanh thu để sàng lọc bất thường; hiện có {len(anomaly_df)} ngày.")
        else:
            st.info("Cần có cột ngày và doanh thu hợp lệ để sàng lọc bất thường.")

    with dashboard_tab_trend:
        if daily_revenue is not None and len(daily_revenue) >= 3:
            with st.expander("Phân tích xu hướng nâng cao", expanded=False):
                trend_df = daily_revenue.copy().sort_values("date")
                trend_df["rolling_avg"] = trend_df["revenue"].rolling(window=3, min_periods=1).mean()
                fig_trend = px.line(
                    trend_df, x="date", y=["revenue", "rolling_avg"], markers=True,
                    labels={"date": "Ngày", "value": "Doanh thu", "variable": "Chỉ số"},
                )
                fig_trend = make_chart_layout(fig_trend, "Doanh thu thực tế và trung bình trượt 3 ngày có dữ liệu")
                st.plotly_chart(fig_trend, use_container_width=True)
                first_value = float(trend_df.iloc[0]["revenue"])
                last_value = float(trend_df.iloc[-1]["revenue"])
                if first_value != 0:
                    change_pct = (last_value - first_value) / abs(first_value) * 100
                    st.write(f"Thay đổi giữa ngày đầu và ngày cuối trong phạm vi lọc: **{change_pct:+.2f}%**.")
                else:
                    st.write("Không tính phần trăm thay đổi vì doanh thu ngày đầu bằng 0.")
                st.caption("Đây là so sánh giữa hai điểm đầu/cuối, không phải tăng trưởng tháng hoặc năm.")

    # -----------------------------------------------------
    # PERIOD-OVER-PERIOD GROWTH & PORTFOLIO REPORT
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "📊 So sánh kỳ trước & phân tích tăng trưởng",
        "So sánh kỳ đang lọc với kỳ liền trước có cùng số ngày; giữ nguyên bộ lọc nhân viên. Số liệu được tính trực tiếp từ CSV.",
    )

    if date_col and start_date is not None and end_date is not None and start_date <= end_date:
        period_days = (end_date - start_date).days + 1
        if date_col and st.session_state.get("period_filter_mode") == "Theo tháng":
            previous_end_ts = pd.Timestamp(start_date) - pd.Timedelta(days=1)
            previous_start = previous_end_ts.replace(day=1).date()
            previous_end = previous_end_ts.date()
            previous_period_label = "tháng liền trước"
        elif date_col and st.session_state.get("period_filter_mode") == "Theo quý":
            previous_end_ts = pd.Timestamp(start_date) - pd.Timedelta(days=1)
            previous_end = previous_end_ts.date()
            previous_quarter = ((previous_end_ts.month - 1) // 3) + 1
            previous_start = pd.Timestamp(previous_end_ts.year, (previous_quarter - 1) * 3 + 1, 1).date()
            previous_period_label = "quý liền trước"
        else:
            previous_end = (pd.Timestamp(start_date) - pd.Timedelta(days=1)).date()
            previous_start = (pd.Timestamp(previous_end) - pd.Timedelta(days=period_days - 1)).date()
            previous_period_label = "kỳ liền trước cùng số ngày"
        previous_df = filter_business_data(
            source_df,
            date_col=date_col,
            employee_col=employee_col,
            start_date=previous_start,
            end_date=previous_end,
            selected_employees=selected_employees,
        )
        current_summary = summarize_business_period(filtered_df)
        previous_summary = summarize_business_period(previous_df)
        revenue_change = (current_summary["revenue"] - previous_summary["revenue"]) if current_summary["revenue"] is not None and previous_summary["revenue"] is not None else None
        revenue_growth = growth_pct(current_summary["revenue"], previous_summary["revenue"])
        orders_change = (current_summary["orders"] - previous_summary["orders"]) if current_summary["orders"] is not None and previous_summary["orders"] is not None else None
        orders_growth = growth_pct(current_summary["orders"], previous_summary["orders"])
        aov_change = (current_summary["aov"] - previous_summary["aov"]) if current_summary["aov"] is not None and previous_summary["aov"] is not None else None
        aov_growth = growth_pct(current_summary["aov"], previous_summary["aov"])

        st.caption(f"Kỳ hiện tại: {start_date:%d/%m/%Y} – {end_date:%d/%m/%Y} · So sánh với {previous_period_label}: {previous_start:%d/%m/%Y} – {previous_end:%d/%m/%Y}.")

        # Targets are configurable assumptions supplied by the analyst, not company-approved targets.
        st.markdown("#### 🎯 KPI mục tiêu so với thực tế")
        st.caption("Nhập mục tiêu theo kỳ đang chọn. Đây là mục tiêu phân tích do người dùng đặt, không phải số liệu mục tiêu chính thức của doanh nghiệp.")
        t1, t2, t3 = st.columns(3)
        target_revenue = t1.number_input(
            "Mục tiêu doanh thu (VND)", min_value=0, step=5_000_000,
            key="target_revenue_vnd",
        )
        target_orders = t2.number_input(
            "Mục tiêu số đơn", min_value=0, step=5,
            key="target_order_count",
        )
        target_aov = t3.number_input(
            "Mục tiêu AOV (VND/đơn)", min_value=0, step=100_000,
            key="target_aov_vnd",
        )

        target_metrics = [
            ("Doanh thu", current_summary.get("revenue"), float(target_revenue)),
            ("Số đơn", current_summary.get("orders"), float(target_orders)),
            ("AOV", current_summary.get("aov"), float(target_aov)),
        ]
        target_rows = []
        for target_label, actual, target in target_metrics:
            attainment = (float(actual) / target * 100) if actual is not None and target > 0 else None
            gap = (float(actual) - target) if actual is not None else None
            target_rows.append({
                "KPI": target_label,
                "Mục tiêu": target,
                "Thực tế": actual,
                "Chênh lệch so mục tiêu": gap,
                "Hoàn thành (%)": attainment,
                "Trạng thái": ("Đạt/vượt" if attainment is not None and attainment >= 100 else "Chưa đạt" if attainment is not None else "Chưa xác định"),
            })
        target_df = pd.DataFrame(target_rows)
        target_display = target_df.copy()
        for c in ["Mục tiêu", "Thực tế", "Chênh lệch so mục tiêu"]:
            target_display[c] = target_display[c].map(lambda v: "N/A" if v is None or pd.isna(v) else f"{v:,.0f}")
        target_display["Hoàn thành (%)"] = target_display["Hoàn thành (%)"].map(lambda v: "N/A" if v is None or pd.isna(v) else f"{v:.1f}%")
        st.dataframe(target_display, use_container_width=True, hide_index=True)
        target_cols = st.columns(3)
        for col, row in zip(target_cols, target_rows):
            col.metric(f"{row['KPI']} — hoàn thành", f"{row['Hoàn thành (%)']:.1f}%" if row["Hoàn thành (%)"] is not None else "N/A", delta=f"{row['Chênh lệch so mục tiêu']:+,.0f}" if row["Chênh lệch so mục tiêu"] is not None else None)

        # Revenue pace / run-rate estimate.
        # Only include revenue dated on or before today; future-dated CSV rows must not
        # inflate the numerator while elapsed days are capped at today.
        today_local = datetime.now().date()
        pace_revenue = None
        last_observed_date = None
        revenue_col_for_pace = current_summary.get("revenue_col")
        observed_end_date = min(end_date, today_local)

        if (
            date_col
            and date_col in filtered_df.columns
            and revenue_col_for_pace
            and revenue_col_for_pace in filtered_df.columns
            and observed_end_date >= start_date
        ):
            parsed_dates = parse_date_series(filtered_df[date_col])
            observed_mask = (
                parsed_dates.notna()
                & (parsed_dates.dt.date >= start_date)
                & (parsed_dates.dt.date <= observed_end_date)
            )
            observed_df = filtered_df.loc[observed_mask]

            if not observed_df.empty:
                observed_revenue = to_numeric_series(
                    observed_df[revenue_col_for_pace]
                ).dropna()
                if not observed_revenue.empty:
                    pace_revenue = float(observed_revenue.sum())
                    last_observed_date = parsed_dates.loc[observed_mask].max().date()

        # Use elapsed calendar days through today (or period end), not future rows.
        elapsed_days = (
            max(0, (observed_end_date - start_date).days + 1)
            if pace_revenue is not None and observed_end_date >= start_date
            else 0
        )
        remaining_days = (
            max(0, (end_date - observed_end_date).days)
            if pace_revenue is not None and observed_end_date >= start_date
            else 0
        )
        pace_projection = (
            pace_revenue / elapsed_days * period_days
            if pace_revenue is not None and elapsed_days > 0
            else None
        )
        pace_target_gap = (
            pace_projection - float(target_revenue)
            if pace_projection is not None and target_revenue > 0
            else None
        )
        daily_revenue_needed = (
            max(0.0, float(target_revenue) - pace_revenue) / remaining_days
            if (
                target_revenue > 0
                and remaining_days > 0
                and pace_revenue is not None
            )
            else None
        )

        st.markdown("#### 🏁 Tốc độ đạt mục tiêu doanh thu")
        pace_cols = st.columns(4)
        pace_cols[0].metric("Ngày dữ liệu đã ghi nhận", f"{elapsed_days}/{period_days}" if elapsed_days else "Chưa có dữ liệu")
        pace_cols[1].metric(
            "Doanh thu/ngày bình quân",
            money_text(pace_revenue / elapsed_days)
            if pace_revenue is not None and elapsed_days > 0
            else "N/A",
        )
        pace_cols[2].metric("Ước tính cuối kỳ", money_text(pace_projection) if pace_projection is not None else "N/A", delta=(f"{pace_target_gap:+,.0f} đ so mục tiêu" if pace_target_gap is not None else None))
        pace_cols[3].metric(
            "Cần đạt mỗi ngày còn lại",
            money_text(daily_revenue_needed)
            if daily_revenue_needed is not None
            else ("Đã hết kỳ" if end_date <= today_local else "N/A"),
        )
        st.caption(
            "Ước tính cuối kỳ = doanh thu ghi nhận đến hôm nay (hoặc cuối kỳ nếu kỳ đã kết thúc) "
            "/ số ngày lịch đã trôi qua × tổng số ngày của kỳ. Dòng CSV có ngày tương lai "
            "không được dùng để tính tốc độ. Đây là phép ngoại suy tuyến tính đơn giản, "
            "không tính mùa vụ, khuyến mãi hoặc độ trễ cập nhật dữ liệu; chỉ dùng để tham khảo."
        )

        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Doanh thu kỳ này", money_text(current_summary["revenue"]), delta=(f"{revenue_change:+,.0f} đ" if revenue_change is not None else None), help="Delta là chênh lệch tuyệt đối so với kỳ trước.")
        g2.metric("Tăng trưởng doanh thu", f"{revenue_growth:+.2f}%" if revenue_growth is not None else "N/A", help="Không tính % nếu kỳ trước không có doanh thu hoặc bằng 0.")
        g3.metric("Số đơn kỳ này", format_number(current_summary["orders"]), delta=(f"{orders_change:+,.0f} đơn" if orders_change is not None else None))
        g4.metric("Giá trị đơn TB (AOV)", money_text(current_summary["aov"]), delta=(f"{aov_growth:+.2f}%" if aov_growth is not None else None))

        compare_rows = []
        for label, key, change, pct in [
            ("Doanh thu", "revenue", revenue_change, revenue_growth),
            ("Số đơn hàng", "orders", orders_change, orders_growth),
            ("Giá trị đơn trung bình (AOV)", "aov", aov_change, aov_growth),
            ("Số nhân viên hoạt động", "active_employees", None, None),
            ("Số dòng dữ liệu", "rows", current_summary["rows"] - previous_summary["rows"], growth_pct(current_summary["rows"], previous_summary["rows"])),
        ]:
            cur, prev = current_summary.get(key), previous_summary.get(key)
            compare_rows.append({
                "Chỉ số": label,
                "Kỳ hiện tại": cur,
                "Kỳ trước": prev,
                "Chênh lệch": change if change is not None else (cur - prev if isinstance(cur, (int, float)) and isinstance(prev, (int, float)) else None),
                "Tăng trưởng (%)": pct,
            })
        compare_df = pd.DataFrame(compare_rows)
        display_compare = compare_df.copy()
        for col in ["Kỳ hiện tại", "Kỳ trước", "Chênh lệch"]:
            display_compare[col] = display_compare[col].map(lambda v: "N/A" if v is None or pd.isna(v) else f"{v:,.2f}" if isinstance(v, (int, float)) else str(v))
        display_compare["Tăng trưởng (%)"] = display_compare["Tăng trưởng (%)"].map(lambda v: "N/A" if v is None or pd.isna(v) else f"{v:+.2f}%")
        st.dataframe(display_compare, use_container_width=True, hide_index=True)

        chart_rows = []
        for period_label, summary in [("Kỳ trước", previous_summary), ("Kỳ hiện tại", current_summary)]:
            if summary["revenue"] is not None:
                chart_rows.append({"Kỳ": period_label, "Doanh thu": summary["revenue"]})
        if chart_rows:
            fig_compare = px.bar(pd.DataFrame(chart_rows), x="Kỳ", y="Doanh thu", text="Doanh thu", labels={"Doanh thu": "Doanh thu (VND)"})
            fig_compare.update_traces(texttemplate="%{y:,.0f}", textposition="outside", cliponaxis=False)
            fig_compare = make_chart_layout(fig_compare, "So sánh doanh thu kỳ hiện tại và kỳ trước")
            st.plotly_chart(fig_compare, use_container_width=True)

        # Explain drivers using comparable employee/product revenue, without inventing causal claims.
        def top_revenue_delta(current_map, previous_map, label_key):
            all_keys = set(current_map) | set(previous_map)
            values = [(name, float(current_map.get(name, 0) - previous_map.get(name, 0))) for name in all_keys]
            values.sort(key=lambda item: abs(item[1]), reverse=True)
            return values[:5]

        driver_cols = st.columns(2)
        for slot, title, map_key, entity_label in [
            (driver_cols[0], "Thay đổi doanh thu theo nhân viên", "employee_revenue", "Nhân viên"),
            (driver_cols[1], "Thay đổi doanh thu theo sản phẩm", "product_revenue", "Sản phẩm"),
        ]:
            with slot:
                st.markdown(f"**{title}**")
                current_map = current_summary.get(map_key, {})
                previous_map = previous_summary.get(map_key, {})
                delta_rows = top_revenue_delta(current_map, previous_map, entity_label)
                if delta_rows:
                    delta_df = pd.DataFrame(delta_rows, columns=[entity_label, "Chênh lệch doanh thu"])
                    delta_df["Chênh lệch doanh thu"] = delta_df["Chênh lệch doanh thu"].map(lambda v: f"{v:+,.0f} đ")
                    st.dataframe(delta_df, use_container_width=True, hide_index=True)
                else:
                    st.caption(f"Không đủ cột {entity_label.lower()} và doanh thu để phân tích.")

        if revenue_growth is not None:
            if revenue_growth > 0:
                st.success(f"Doanh thu tăng {revenue_growth:.2f}% so với kỳ liền trước. Đây là thay đổi quan sát được trong dữ liệu, không tự chứng minh nguyên nhân tăng trưởng.")
            elif revenue_growth < 0:
                st.warning(f"Doanh thu giảm {abs(revenue_growth):.2f}% so với kỳ liền trước. Nên kiểm tra thêm số đơn, AOV và các nhân viên/sản phẩm có biến động lớn.")
            else:
                st.info("Doanh thu không đổi so với kỳ liền trước.")
        elif previous_summary["revenue"] == 0:
            st.info("Kỳ trước có doanh thu bằng 0 nên không tính được phần trăm tăng trưởng; hãy xem chênh lệch tuyệt đối.")
        else:
            st.info("Chưa đủ dữ liệu doanh thu hợp lệ để tính tăng trưởng.")

        # Automatic business narrative: grounded in measured metrics and explicit target inputs.
        st.markdown("#### 🧠 Nhận xét kinh doanh tự động")
        narrative = []
        if revenue_growth is not None:
            if revenue_growth > 0:
                narrative.append(f"Doanh thu tăng **{revenue_growth:.1f}%** so với kỳ trước, tương đương **{money_text(revenue_change)}**.")
            elif revenue_growth < 0:
                narrative.append(f"Doanh thu giảm **{abs(revenue_growth):.1f}%** so với kỳ trước, tương đương **{money_text(revenue_change)}**; cần kiểm tra số đơn, AOV và cơ cấu sản phẩm.")
            else:
                narrative.append("Doanh thu không đổi so với kỳ trước.")
        else:
            narrative.append("Chưa thể tính tăng trưởng doanh thu theo phần trăm vì kỳ trước không có doanh thu hợp lệ hoặc bằng 0.")
        if orders_growth is not None and aov_growth is not None:
            if orders_growth > 0 and aov_growth < 0:
                narrative.append(f"Số đơn tăng **{orders_growth:.1f}%** nhưng AOV giảm **{abs(aov_growth):.1f}%**: tăng trưởng có thể đang dựa nhiều hơn vào số lượng đơn giá trị thấp.")
            elif orders_growth < 0 and aov_growth > 0:
                narrative.append(f"Số đơn giảm **{abs(orders_growth):.1f}%** trong khi AOV tăng **{aov_growth:.1f}%**: cần xem mức tăng giá trị đơn có bù được lượng đơn giảm hay không.")
            elif orders_growth > 0 and aov_growth > 0:
                narrative.append("Cả số đơn và AOV đều tăng; hai chỉ số cùng chiều với tăng trưởng doanh thu.")
        revenue_target_row = next(r for r in target_rows if r["KPI"] == "Doanh thu")
        if revenue_target_row["Hoàn thành (%)"] is not None:
            pct = revenue_target_row["Hoàn thành (%)"]
            if pct >= 100:
                narrative.append(f"Đã đạt **{pct:.1f}%** mục tiêu doanh thu, vượt mục tiêu **{money_text(revenue_target_row['Chênh lệch so mục tiêu'])}**.")
            else:
                narrative.append(f"Đạt **{pct:.1f}%** mục tiêu doanh thu; còn thiếu **{money_text(abs(revenue_target_row['Chênh lệch so mục tiêu']))}** so với mục tiêu đã nhập.")
        if pace_projection is not None and target_revenue > 0:
            if pace_projection >= float(target_revenue):
                narrative.append(f"Theo tốc độ doanh thu bình quân hiện tại, doanh thu ngoại suy cuối kỳ khoảng **{money_text(pace_projection)}**, cao hơn mục tiêu khoảng **{money_text(pace_projection - float(target_revenue))}**; đây không phải dự báo có điều chỉnh mùa vụ.")
            else:
                narrative.append(f"Theo tốc độ hiện tại, doanh thu ngoại suy cuối kỳ khoảng **{money_text(pace_projection)}**, thấp hơn mục tiêu khoảng **{money_text(float(target_revenue) - pace_projection)}**. Nếu kỳ còn mở, cần đạt khoảng **{money_text(daily_revenue_needed)} mỗi ngày** trong {remaining_days} ngày còn lại để chạm mục tiêu." if daily_revenue_needed is not None else f"Theo tốc độ hiện tại, doanh thu ngoại suy cuối kỳ khoảng **{money_text(pace_projection)}**, thấp hơn mục tiêu khoảng **{money_text(float(target_revenue) - pace_projection)}**; kỳ đã kết thúc hoặc không còn ngày để bù.")
        employee_deltas = top_revenue_delta(current_summary.get("employee_revenue", {}), previous_summary.get("employee_revenue", {}), "Nhân viên")
        product_deltas = top_revenue_delta(current_summary.get("product_revenue", {}), previous_summary.get("product_revenue", {}), "Sản phẩm")
        if employee_deltas:
            name, delta = employee_deltas[0]
            narrative.append(f"Biến động doanh thu theo nhân viên lớn nhất trong nhóm so sánh: **{name}** ({delta:+,.0f} đ).")
        if product_deltas:
            name, delta = product_deltas[0]
            narrative.append(f"Biến động doanh thu theo sản phẩm lớn nhất trong nhóm so sánh: **{name}** ({delta:+,.0f} đ).")
        for item in narrative:
            st.markdown(f"- {item}")
        st.caption("Nhận xét được tạo theo quy tắc từ KPI đã tính; đây là tín hiệu để điều tra thêm, không phải kết luận nhân quả. Kiểm tra khuyến mãi, giá, tồn kho và chất lượng dữ liệu trước khi ra quyết định.")

        # Professional exports: Markdown for GitHub/portfolio, HTML for sharing, JSON for reuse, CSV for comparison.
        generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        report_payload = {
            "report_title": "Báo cáo phân tích doanh thu & tăng trưởng",
            "generated_at": generated_at,
            "source_file": st.session_state.last_filename or "uploaded.csv",
            "filter": {"employees": selected_employees, "current_start": str(start_date), "current_end": str(end_date), "previous_start": str(previous_start), "previous_end": str(previous_end), "period_days": period_days},
            "current_period": current_summary,
            "previous_period": previous_summary,
            "comparison": compare_rows,
            "targets": target_rows,
            "business_narrative": [re.sub(r"\*\*", "", item) for item in narrative],
            "interpretation": "Các chỉ số được tính từ dữ liệu CSV đã lọc. Biến động mô tả tương quan, không khẳng định nguyên nhân nhân quả. Kỳ trước không có doanh thu thì phần trăm tăng trưởng không xác định.",
        }
        def fmt(v):
            return "N/A" if v is None or pd.isna(v) else f"{v:,.2f}" if isinstance(v, (int, float)) else str(v)

        report_lines = [
            "# Báo cáo phân tích doanh thu & tăng trưởng", "",
            f"- **Tệp dữ liệu:** {st.session_state.last_filename or 'uploaded.csv'}",
            f"- **Thời gian xuất:** {generated_at}",
            f"- **Kỳ hiện tại:** {start_date:%d/%m/%Y} – {end_date:%d/%m/%Y}",
            f"- **Kỳ so sánh:** {previous_start:%d/%m/%Y} – {previous_end:%d/%m/%Y}",
            f"- **Nhân viên lọc:** {', '.join(selected_employees) if selected_employees is not None else 'Tất cả'}", "",
            "## Tóm tắt điều hành", "",
            f"- Doanh thu kỳ hiện tại: **{money_text(current_summary['revenue'])}**.",
            f"- Doanh thu kỳ trước: **{money_text(previous_summary['revenue'])}**.",
            f"- Chênh lệch doanh thu: **{money_text(revenue_change)}**.",
            f"- Tăng trưởng doanh thu: **{f'{revenue_growth:+.2f}%' if revenue_growth is not None else 'Không xác định'}**.",
            f"- Số đơn kỳ hiện tại: **{format_number(current_summary['orders'])}**; kỳ trước: **{format_number(previous_summary['orders'])}**.",
            f"- AOV kỳ hiện tại: **{money_text(current_summary['aov'])}**; kỳ trước: **{money_text(previous_summary['aov'])}**.", "",
            "## KPI mục tiêu so với thực tế", "",
            "| KPI | Mục tiêu | Thực tế | Chênh lệch | Hoàn thành (%) | Trạng thái |", "|---|---:|---:|---:|---:|---|",
            *[f"| {r['KPI']} | {fmt(r['Mục tiêu'])} | {fmt(r['Thực tế'])} | {fmt(r['Chênh lệch so mục tiêu'])} | {fmt(r['Hoàn thành (%)'])} | {r['Trạng thái']} |" for r in target_rows],
            "", "## Nhận xét kinh doanh tự động", "",
            *[f"- {re.sub(r'\*\*', '', item)}" for item in narrative],
            "", "## Bảng KPI so sánh", "",
            "| Chỉ số | Kỳ hiện tại | Kỳ trước | Chênh lệch | Tăng trưởng (%) |", "|---|---:|---:|---:|---:|",
        ]
        for row in compare_rows:
            report_lines.append(f"| {row['Chỉ số']} | {fmt(row['Kỳ hiện tại'])} | {fmt(row['Kỳ trước'])} | {fmt(row['Chênh lệch'])} | {fmt(row['Tăng trưởng (%)'])} |")
        report_lines.extend(["", "## Biến động theo nhân viên", ""])
        for name, delta in top_revenue_delta(current_summary.get("employee_revenue", {}), previous_summary.get("employee_revenue", {}), "Nhân viên"):
            report_lines.append(f"- {name}: {delta:+,.0f} đ")
        report_lines.extend(["", "## Biến động theo sản phẩm", ""])
        for name, delta in top_revenue_delta(current_summary.get("product_revenue", {}), previous_summary.get("product_revenue", {}), "Sản phẩm"):
            report_lines.append(f"- {name}: {delta:+,.0f} đ")
        report_lines.extend(["", "## Phương pháp & giới hạn", "", "- Kỳ so sánh là tháng/quý liền trước khi chọn chế độ tháng/quý; với ngày tùy chỉnh, so sánh khoảng liền trước có cùng số ngày.", "- Bộ lọc nhân viên hiện tại được áp dụng cho cả hai kỳ.", "- Mã đơn hàng được đếm distinct khi nhận diện được cột mã đơn; nếu không, dùng số lượng số học hoặc số dòng làm chỉ báo thay thế.", "- Phần trăm tăng trưởng không xác định khi kỳ trước bằng 0 hoặc thiếu dữ liệu.", "- Biến động không chứng minh quan hệ nhân quả; cần xác minh chương trình khuyến mãi, tồn kho và dữ liệu vận hành trước khi kết luận.", ""])
        report_md = "\n".join(report_lines)
        html_rows = "".join(f"<tr><td>{row['Chỉ số']}</td><td>{fmt(row['Kỳ hiện tại'])}</td><td>{fmt(row['Kỳ trước'])}</td><td>{fmt(row['Chênh lệch'])}</td><td>{fmt(row['Tăng trưởng (%)'])}</td></tr>" for row in compare_rows)
        html_target_rows = "".join(f"<tr><td>{r['KPI']}</td><td>{fmt(r['Mục tiêu'])}</td><td>{fmt(r['Thực tế'])}</td><td>{fmt(r['Chênh lệch so mục tiêu'])}</td><td>{fmt(r['Hoàn thành (%)'])}</td><td>{r['Trạng thái']}</td></tr>" for r in target_rows)
        html_narrative = "".join(f"<li>{re.sub(r'\*\*', '', item)}</li>" for item in narrative)
        html_report = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Báo cáo doanh thu & tăng trưởng</title><style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:40px auto;padding:0 22px;color:#172033;line-height:1.65}}header{{background:#10213e;color:white;padding:28px;border-radius:16px}}header p{{color:#d6e4fa}}.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:22px 0}}.kpi{{border:1px solid #d9e2f0;border-radius:12px;padding:16px}}.kpi b{{display:block;color:#53657f;font-size:12px;text-transform:uppercase}}.kpi strong{{font-size:21px;display:block;margin-top:8px}}table{{border-collapse:collapse;width:100%;margin:14px 0}}th,td{{border:1px solid #d9e2f0;padding:10px;text-align:left}}th{{background:#edf3fb}}.note{{background:#f2f6fb;padding:14px;border-left:4px solid #477bd1}}</style></head><body><header><p>DATA ANALYST PORTFOLIO · BUSINESS INTELLIGENCE</p><h1>Báo cáo phân tích doanh thu & tăng trưởng</h1><p>Nguồn: {st.session_state.last_filename or 'uploaded.csv'} · Xuất lúc {generated_at}</p><p>Kỳ hiện tại: {start_date:%d/%m/%Y} – {end_date:%d/%m/%Y} · Kỳ trước: {previous_start:%d/%m/%Y} – {previous_end:%d/%m/%Y}</p></header><section class="kpis"><div class="kpi"><b>Doanh thu kỳ này</b><strong>{money_text(current_summary['revenue'])}</strong></div><div class="kpi"><b>Doanh thu kỳ trước</b><strong>{money_text(previous_summary['revenue'])}</strong></div><div class="kpi"><b>Tăng trưởng doanh thu</b><strong>{f'{revenue_growth:+.2f}%' if revenue_growth is not None else 'N/A'}</strong></div><div class="kpi"><b>AOV kỳ này</b><strong>{money_text(current_summary['aov'])}</strong></div></section><h2>KPI mục tiêu so với thực tế</h2><table><thead><tr><th>KPI</th><th>Mục tiêu</th><th>Thực tế</th><th>Chênh lệch</th><th>Hoàn thành (%)</th><th>Trạng thái</th></tr></thead><tbody>{html_target_rows}</tbody></table><h2>Nhận xét kinh doanh tự động</h2><ul>{html_narrative}</ul><h2>So sánh KPI</h2><table><thead><tr><th>Chỉ số</th><th>Kỳ hiện tại</th><th>Kỳ trước</th><th>Chênh lệch</th><th>Tăng trưởng (%)</th></tr></thead><tbody>{html_rows}</tbody></table><h2>Biến động theo nhân viên</h2><ul>{''.join(f'<li>{name}: {delta:+,.0f} đ</li>' for name,delta in top_revenue_delta(current_summary.get('employee_revenue',{}),previous_summary.get('employee_revenue',{}),'Nhân viên')) or '<li>Không đủ dữ liệu</li>'}</ul><h2>Biến động theo sản phẩm</h2><ul>{''.join(f'<li>{name}: {delta:+,.0f} đ</li>' for name,delta in top_revenue_delta(current_summary.get('product_revenue',{}),previous_summary.get('product_revenue',{}),'Sản phẩm')) or '<li>Không đủ dữ liệu</li>'}</ul><div class="note"><b>Phương pháp:</b> Kỳ liền trước có cùng số ngày; bộ lọc nhân viên được áp dụng cho cả hai kỳ. Tăng trưởng phần trăm không xác định nếu kỳ trước bằng 0. Biến động là mô tả dữ liệu, không tự chứng minh nguyên nhân.</div></body></html>'''
        report_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", re.sub(r"\.csv$", "", str(st.session_state.last_filename or "sales"), flags=re.IGNORECASE)).strip("_") or "sales"
        e1, e2, e3, e4 = st.columns(4)
        with e1:
            st.download_button("⬇️ Báo cáo Markdown", report_md.encode("utf-8-sig"), file_name=f"{report_stem}_growth_report.md", mime="text/markdown", use_container_width=True)
        with e2:
            st.download_button("⬇️ Báo cáo HTML", html_report.encode("utf-8"), file_name=f"{report_stem}_growth_report.html", mime="text/html", use_container_width=True)
        with e3:
            st.download_button("⬇️ Dữ liệu JSON", json.dumps(report_payload, ensure_ascii=False, indent=2, default=str).encode("utf-8-sig"), file_name=f"{report_stem}_growth_report.json", mime="application/json", use_container_width=True)
        with e4:
            st.download_button("⬇️ Bảng KPI CSV", compare_df.to_csv(index=False).encode("utf-8-sig"), file_name=f"{report_stem}_kpi_comparison.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("Để so sánh tăng trưởng, hãy chọn khoảng ngày hợp lệ và đảm bảo CSV có cột ngày. Nếu kỳ trước nằm ngoài dữ liệu, báo cáo sẽ thể hiện kỳ trước bằng 0 dòng thay vì tự tạo số liệu.")

    with dashboard_tab_overview:
        # STATISTICS FROM BACKEND
        # -----------------------------------------------------
        st.divider()
        section_heading(
            "🔢 Thống kê mô tả",
            "Kết quả thống kê do backend Pandas trả về.",
        )

        numeric_summary = report.get("numeric_summary") or {}
        if numeric_summary:
            numeric_df = pd.DataFrame.from_dict(
                numeric_summary,
                orient="index",
            )
            numeric_df.index.name = "Tên cột"
            st.dataframe(numeric_df, use_container_width=True)
        else:
            st.info("Backend chưa trả về thống kê mô tả.")

    with dashboard_tab_quality:
        # -----------------------------------------------------
        # DATA QUALITY — deterministic checks on the uploaded data
        # -----------------------------------------------------
        st.divider()
        section_heading(
            "🧹 Chất lượng dữ liệu",
            "Kiểm tra trên dữ liệu đang được lọc. Báo cáo chỉ phát hiện vấn đề và đề xuất; không tự sửa hay xóa dữ liệu gốc.",
        )

        quality = build_data_quality_report(filtered_df)
        quality_summary = quality["summary"]
        q1, q2, q3, q4, q5 = st.columns(5)
        q1.metric("Ô dữ liệu thiếu", format_number(quality_summary["missing_cells"]))
        q2.metric("Dòng trùng lặp", format_number(quality_summary["duplicate_rows"]))
        q3.metric("Giá trị số lỗi", format_number(quality_summary["invalid_numeric_cells"]))
        q4.metric("Ngày không hợp lệ", format_number(quality_summary["invalid_date_cells"]))
        q5.metric("Tổng ô dữ liệu", format_number(quality_summary["total_cells"]))

        if quality["issues"].empty:
            st.success("Chưa phát hiện giá trị thiếu, dòng trùng, số sai định dạng hoặc ngày sai trong phạm vi dữ liệu đang lọc.")
        else:
            st.warning(f"Phát hiện {len(quality['issues']):,} nhóm vấn đề cần xem xét. Hãy kiểm tra trước khi dùng dữ liệu cho báo cáo chính thức.")
            st.subheader("Bảng tổng hợp vấn đề")
            st.dataframe(quality["issues"], use_container_width=True, hide_index=True)

        st.subheader("🔎 Bảng chi tiết lỗi theo dòng và cột")
        st.caption("Số dòng tính theo file CSV gốc (dòng 1 là tiêu đề). Dữ liệu chỉ được kiểm tra; không tự sửa hoặc xóa.")
        issue_details = quality["issue_details"]
        if issue_details.empty:
            st.success("Không có lỗi chi tiết cần hiển thị trong phạm vi dữ liệu hiện tại.")
        else:
            detail_filters = st.columns(2)
            issue_type_options = sorted(issue_details["Loại vấn đề"].dropna().unique().tolist())
            selected_issue_types = detail_filters[0].multiselect(
                "Lọc loại vấn đề", options=issue_type_options,
                default=issue_type_options, key="dq_detail_issue_types",
            )
            column_options = sorted(issue_details["Cột"].dropna().astype(str).unique().tolist())
            selected_issue_columns = detail_filters[1].multiselect(
                "Lọc cột", options=column_options,
                default=column_options, key="dq_detail_columns",
            )
            visible_details = issue_details[
                issue_details["Loại vấn đề"].isin(selected_issue_types)
                & issue_details["Cột"].astype(str).isin(selected_issue_columns)
            ]
            st.dataframe(visible_details, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Tải bảng chi tiết lỗi (CSV)",
                data=issue_details.to_csv(index=False).encode("utf-8-sig"),
                file_name="data_quality_issue_details.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with st.expander("Chi tiết chất lượng theo từng cột", expanded=True):
            st.dataframe(quality["columns"], use_container_width=True, hide_index=True)

        quality_csv = quality["issues"].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Tải danh sách vấn đề chất lượng dữ liệu (CSV)",
            data=quality_csv,
            file_name="data_quality_issues.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=quality["issues"].empty,
        )

    # -----------------------------------------------------
    # DATA CLEANING ASSISTANT — explicit confirmation and separate export
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "🧽 Làm sạch dữ liệu có xác nhận",
        "Tạo bản sao để làm sạch và xuất CSV mới. File gốc không bị ghi đè; giá trị lỗi không bị tự đổi thành 0.",
    )
    st.caption("Quy trình áp dụng trên toàn bộ CSV đã tải lên, không chỉ phần đang lọc trên Dashboard.")

    numeric_clean_options, date_clean_options = detect_cleaning_columns(source_df)
    clean_col1, clean_col2 = st.columns(2)
    with clean_col1:
        selected_numeric_clean = st.multiselect(
            "Cột số muốn chuẩn hóa",
            options=numeric_clean_options,
            default=numeric_clean_options,
            key="clean_numeric_columns",
            help="Chỉ chuyển các giá trị đọc được thành số; giá trị sai và ô trống được giữ nguyên.",
        )
    with clean_col2:
        selected_date_clean = st.multiselect(
            "Cột ngày muốn chuẩn hóa",
            options=date_clean_options,
            default=date_clean_options,
            key="clean_date_columns",
            help="Ngày hợp lệ chuyển thành YYYY-MM-DD; ngày không hợp lệ được giữ nguyên.",
        )

    source_duplicate_count = int(source_df.duplicated(keep="first").sum())
    remove_duplicates_choice = st.checkbox(
        f"Xóa các dòng trùng hoàn toàn sau khi xác nhận ({source_duplicate_count} dòng phát hiện)",
        value=False,
        key="clean_remove_duplicates",
        disabled=source_duplicate_count == 0,
    )
    duplicate_confirmed = False
    if remove_duplicates_choice:
        duplicate_confirmed = st.checkbox(
            "Tôi xác nhận xóa các dòng trùng hoàn toàn khỏi BẢN SAO xuất ra (file gốc không thay đổi).",
            value=False,
            key="clean_duplicate_confirmation",
        )

    if st.button("🔍 Tạo bản xem trước dữ liệu đã làm sạch", type="primary", use_container_width=True):
        if remove_duplicates_choice and not duplicate_confirmed:
            st.error("Fen cần xác nhận rõ việc loại dòng trùng trước khi tạo bản xem trước.")
        else:
            cleaned_candidate, cleaning_log, cleaning_summary = build_cleaned_candidate(
                source_df,
                selected_numeric_clean,
                selected_date_clean,
                remove_duplicates=bool(remove_duplicates_choice and duplicate_confirmed),
            )
            st.session_state.cleaned_df = cleaned_candidate
            st.session_state.cleaning_log = {
                "log": cleaning_log,
                "summary": cleaning_summary,
                "source_name": st.session_state.last_filename or "data.csv",
            }
            st.session_state.cleaned_source_signature = (
                st.session_state.last_filename,
                int(len(source_df)),
                int(len(source_df.columns)),
            )

    cleaned_df = st.session_state.get("cleaned_df")
    cleaning_state = st.session_state.get("cleaning_log")
    current_signature = (
        st.session_state.last_filename,
        int(len(source_df)),
        int(len(source_df.columns)),
    )
    if cleaned_df is not None and cleaning_state is not None and st.session_state.get("cleaned_source_signature") == current_signature:
        cleaning_summary = cleaning_state["summary"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Số dòng trước", format_number(cleaning_summary["rows_before"]))
        c2.metric("Số dòng sau", format_number(cleaning_summary["rows_after"]))
        c3.metric("Dòng trùng đã loại", format_number(cleaning_summary["duplicate_rows_removed"]))
        st.subheader("👀 Xem trước bản dữ liệu mới")
        st.dataframe(cleaned_df.head(200), use_container_width=True, hide_index=True)
        st.caption("Đây là bản sao đã xử lý. Chỉ khi fen tải file xuống thì mới có file CSV mới trên máy.")
        st.subheader("🧾 Nhật ký làm sạch")
        st.dataframe(cleaning_state["log"], use_container_width=True, hide_index=True)
        cleaned_csv = cleaned_df.to_csv(index=False).encode("utf-8-sig")
        original_stem = re.sub(r"\.csv$", "", str(cleaning_state["source_name"]), flags=re.IGNORECASE) or "data"
        st.download_button(
            "⬇️ Tải CSV đã làm sạch (không ghi đè file gốc)",
            data=cleaned_csv,
            file_name=f"{original_stem}_cleaned.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Tải nhật ký làm sạch (CSV)",
            data=cleaning_state["log"].to_csv(index=False).encode("utf-8-sig"),
            file_name="data_cleaning_log.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Chọn quy tắc ở trên rồi bấm ‘Tạo bản xem trước dữ liệu đã làm sạch’. Chỉ xuất file sau khi fen đã kiểm tra bản xem trước.")

    # -----------------------------------------------------
    # BEFORE / AFTER COMPARISON + AUTOMATED REPORT EXPORT
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "📈 So sánh trước – sau làm sạch & báo cáo tự động",
        "So sánh trên toàn bộ CSV gốc và bản xem trước đã làm sạch; xuất báo cáo Markdown, JSON và bảng so sánh CSV.",
    )

    cleaned_df_for_report = st.session_state.get("cleaned_df")
    cleaning_state_for_report = st.session_state.get("cleaning_log")
    report_signature = (
        st.session_state.last_filename,
        int(len(source_df)),
        int(len(source_df.columns)),
    )
    has_current_cleaning = (
        isinstance(cleaned_df_for_report, pd.DataFrame)
        and cleaning_state_for_report is not None
        and st.session_state.get("cleaned_source_signature") == report_signature
    )

    if not has_current_cleaning:
        # Avoid accidentally attaching comparison metrics from a previous uploaded file.
        st.session_state.before_after_report_data = None
        st.info("Tạo bản xem trước trong mục ‘Làm sạch dữ liệu có xác nhận’ trước để xem so sánh và xuất báo cáo.")
    else:
        before_quality = build_data_quality_report(source_df)
        after_quality = build_data_quality_report(cleaned_df_for_report)
        before_summary = before_quality["summary"]
        after_summary = after_quality["summary"]

        metric_definitions = [
            ("Số dòng", "row_count", "lower"),
            ("Số ô thiếu", "missing_cells", "lower"),
            ("Dòng trùng lặp", "duplicate_rows", "lower"),
            ("Giá trị số không hợp lệ", "invalid_numeric_cells", "lower"),
            ("Ngày không hợp lệ", "invalid_date_cells", "lower"),
            ("Tổng số ô", "total_cells", "neutral"),
        ]
        comparison_rows = []
        for label, key, direction in metric_definitions:
            before_value = int(before_summary.get(key, 0))
            after_value = int(after_summary.get(key, 0))
            delta = after_value - before_value
            if direction == "lower":
                if delta < 0:
                    status = "Giảm"
                elif delta > 0:
                    status = "Tăng — cần xem xét"
                else:
                    status = "Không đổi"
            else:
                status = "Thay đổi do số dòng/cột"
            comparison_rows.append({
                "Chỉ số": label,
                "Trước làm sạch": before_value,
                "Sau làm sạch": after_value,
                "Chênh lệch (sau - trước)": delta,
                "Đánh giá": status,
            })
        comparison_df = pd.DataFrame(comparison_rows)

        st.markdown("#### Tổng quan trước và sau")
        before_col, after_col = st.columns(2)
        with before_col:
            st.markdown("**Trước làm sạch · CSV gốc**")
            st.metric("Số dòng", format_number(before_summary["row_count"]))
            st.metric("Ô thiếu", format_number(before_summary["missing_cells"]))
            st.metric("Dòng trùng", format_number(before_summary["duplicate_rows"]))
            st.metric("Giá trị số lỗi", format_number(before_summary["invalid_numeric_cells"]))
            st.metric("Ngày lỗi", format_number(before_summary["invalid_date_cells"]))
        with after_col:
            st.markdown("**Sau làm sạch · Bản xem trước**")
            st.metric("Số dòng", format_number(after_summary["row_count"]), delta=after_summary["row_count"] - before_summary["row_count"])
            st.metric("Ô thiếu", format_number(after_summary["missing_cells"]), delta=after_summary["missing_cells"] - before_summary["missing_cells"], delta_color="inverse")
            st.metric("Dòng trùng", format_number(after_summary["duplicate_rows"]), delta=after_summary["duplicate_rows"] - before_summary["duplicate_rows"], delta_color="inverse")
            st.metric("Giá trị số lỗi", format_number(after_summary["invalid_numeric_cells"]), delta=after_summary["invalid_numeric_cells"] - before_summary["invalid_numeric_cells"], delta_color="inverse")
            st.metric("Ngày lỗi", format_number(after_summary["invalid_date_cells"]), delta=after_summary["invalid_date_cells"] - before_summary["invalid_date_cells"], delta_color="inverse")

        st.markdown("#### Bảng chênh lệch chi tiết")
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        remaining_errors = (
            int(after_summary["missing_cells"])
            + int(after_summary["duplicate_rows"])
            + int(after_summary["invalid_numeric_cells"])
            + int(after_summary["invalid_date_cells"])
        )
        removed_rows = int(cleaning_state_for_report["summary"].get("duplicate_rows_removed", 0))
        if remaining_errors:
            st.warning(
                f"Sau các thao tác đã chọn, vẫn còn {remaining_errors:,} lượt vấn đề theo các nhóm kiểm tra. "
                "Hãy xem bảng chi tiết; một ô có thể được tính trong nhiều nhóm kiểm tra."
            )
        else:
            st.success("Các kiểm tra Data Quality hiện có không phát hiện vấn đề còn lại trong bản xem trước.")

        # Build deterministic exportable report. No AI claims are added unless separately generated.
        generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
        source_name = str(cleaning_state_for_report.get("source_name") or "uploaded.csv")
        log_df_for_report = cleaning_state_for_report.get("log")
        if not isinstance(log_df_for_report, pd.DataFrame):
            log_df_for_report = pd.DataFrame(columns=["Hành động", "Cột", "Số ô thay đổi", "Quy tắc"])

        report_lines = [
            "# Báo cáo chất lượng dữ liệu — trước và sau làm sạch",
            "",
            f"- Tệp nguồn: `{source_name}`",
            f"- Thời gian tạo báo cáo: {generated_at}",
            "- Phạm vi: toàn bộ CSV đã tải lên; bản sau làm sạch là bản xem trước, file gốc không bị ghi đè.",
            "",
            "## So sánh chỉ số",
            "",
            "| Chỉ số | Trước làm sạch | Sau làm sạch | Chênh lệch (sau - trước) | Đánh giá |",
            "|---|---:|---:|---:|---|",
        ]
        for row in comparison_rows:
            report_lines.append(
                f"| {row['Chỉ số']} | {row['Trước làm sạch']} | {row['Sau làm sạch']} | "
                f"{row['Chênh lệch (sau - trước)']} | {row['Đánh giá']} |"
            )
        report_lines.extend([
            "",
            "## Thao tác làm sạch đã ghi nhận",
            "",
        ])
        for _, log_row in log_df_for_report.iterrows():
            report_lines.append(
                f"- **{log_row.get('Hành động', '')}** — cột: {log_row.get('Cột', '')}; "
                f"số ô/dòng thay đổi: {log_row.get('Số ô thay đổi', 0)}; "
                f"quy tắc: {log_row.get('Quy tắc', '')}"
            )
        report_lines.extend([
            "",
            "## Kết luận kiểm tra",
            "",
            f"- Số dòng trùng đã loại theo xác nhận: {removed_rows}.",
            f"- Số lượt vấn đề còn lại theo các kiểm tra hiện có: {remaining_errors}.",
            "- Giá trị lỗi chưa có quy tắc xử lý vẫn được giữ nguyên; báo cáo không khẳng định chúng đã được sửa.",
            "- Báo cáo này được tạo bằng thống kê xác định từ Python/Pandas; không cần API trả phí.",
            "",
        ])
        report_markdown = "\n".join(report_lines)
        report_json = {
            "report_type": "data_quality_before_after",
            "generated_at": generated_at,
            "source_file": source_name,
            "scope": "full_uploaded_csv",
            "source_file_overwritten": False,
            "before": before_summary,
            "after": after_summary,
            "comparison": comparison_rows,
            "cleaning_summary": cleaning_state_for_report["summary"],
            "cleaning_log": log_df_for_report.to_dict(orient="records"),
            "remaining_issue_occurrences": remaining_errors,
            "note": "Giá trị lỗi không được tự đổi thành 0; kiểm tra và khuyến nghị không thay thế xác nhận của người dùng.",
        }
        report_stem = re.sub(r"\.csv$", "", source_name, flags=re.IGNORECASE) or "data"
        # Keep verified before/after metrics available to the AI summary section below.
        st.session_state.before_after_report_data = {
            "generated_at": generated_at,
            "source_file": source_name,
            "before": before_summary,
            "after": after_summary,
            "comparison": comparison_rows,
            "cleaning_summary": cleaning_state_for_report["summary"],
            "cleaning_log": log_df_for_report.to_dict(orient="records"),
            "remaining_issue_occurrences": remaining_errors,
            "source_file_overwritten": False,
        }
        st.markdown("#### Xuất báo cáo tự động")
        st.caption("Báo cáo chỉ phản ánh thống kê kiểm tra được. Tải file CSV đã làm sạch riêng nếu muốn dùng dữ liệu sau xử lý.")
        export_col1, export_col2, export_col3 = st.columns(3)
        with export_col1:
            st.download_button(
                "⬇️ Báo cáo Markdown",
                data=report_markdown.encode("utf-8-sig"),
                file_name=f"{report_stem}_data_quality_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with export_col2:
            st.download_button(
                "⬇️ Báo cáo JSON",
                data=json.dumps(report_json, ensure_ascii=False, indent=2, default=str).encode("utf-8-sig"),
                file_name=f"{report_stem}_data_quality_report.json",
                mime="application/json",
                use_container_width=True,
            )
        with export_col3:
            st.download_button(
                "⬇️ Bảng so sánh CSV",
                data=comparison_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{report_stem}_before_after_comparison.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # -----------------------------------------------------
    # LOCAL OLLAMA — AI EXPLANATION OF DATA QUALITY / CLEANING
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "🧠 AI giải thích chất lượng dữ liệu",
        "Ollama chạy ngay trên máy của bạn. Chỉ gửi thống kê tổng hợp và nhật ký làm sạch, không gửi toàn bộ dòng dữ liệu; không cần API key trả phí.",
    )

    quality_summary_for_ai = quality.get("summary", {})
    issue_rows_for_ai = quality.get("issues")
    issue_records_for_ai = (
        issue_rows_for_ai.head(30).to_dict(orient="records")
        if isinstance(issue_rows_for_ai, pd.DataFrame) and not issue_rows_for_ai.empty
        else []
    )
    cleaning_state_for_ai = st.session_state.get("cleaning_log")
    cleaning_summary_for_ai = None
    cleaning_log_for_ai = []
    if cleaning_state_for_ai:
        cleaning_summary_for_ai = cleaning_state_for_ai.get("summary")
        log_frame_for_ai = cleaning_state_for_ai.get("log")
        if isinstance(log_frame_for_ai, pd.DataFrame) and not log_frame_for_ai.empty:
            cleaning_log_for_ai = log_frame_for_ai.head(30).to_dict(orient="records")

    quality_ai_payload = {
        "file_name": st.session_state.get("last_filename") or "uploaded.csv",
        "quality_summary": quality_summary_for_ai,
        "issue_groups": issue_records_for_ai,
        "cleaning_summary": cleaning_summary_for_ai,
        "cleaning_log": cleaning_log_for_ai,
        "before_after_comparison": st.session_state.get("before_after_report_data"),
    }
    # Stable signature: generated_at changes on every Streamlit rerun and
    # must not invalidate a successful AI response.
    quality_ai_signature_payload = dict(quality_ai_payload)
    before_after_signature_data = quality_ai_signature_payload.get("before_after_comparison")
    if isinstance(before_after_signature_data, dict):
        before_after_signature_data = dict(before_after_signature_data)
        before_after_signature_data.pop("generated_at", None)
        quality_ai_signature_payload["before_after_comparison"] = before_after_signature_data

    quality_ai_signature = hashlib.sha256(
        json.dumps(
            quality_ai_signature_payload,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()

    with st.container(border=True):
        ollama_model = st.text_input(
            "Mô hình Ollama local",
            value="qwen2.5:3b",
            help="Phải là tên model đang có trong `ollama list`. Mặc định dùng qwen2.5:3b.",
            key="quality_ai_ollama_model",
        ).strip() or "qwen2.5:3b"
        ollama_url = st.text_input(
            "Địa chỉ Ollama",
            value="http://localhost:11434",
            help="Mặc định Ollama chạy tại http://localhost:11434 trên máy của bạn.",
            key="quality_ai_ollama_url",
        ).strip().rstrip("/") or "http://localhost:11434"

        st.caption(
            f"Tóm tắt gửi AI: {quality_summary_for_ai.get('row_count', 0)} dòng, "
            f"{quality_summary_for_ai.get('missing_cells', 0)} ô thiếu, "
            f"{quality_summary_for_ai.get('duplicate_rows', 0)} dòng trùng, "
            f"{quality_summary_for_ai.get('invalid_numeric_cells', 0)} giá trị số lỗi, "
            f"{quality_summary_for_ai.get('invalid_date_cells', 0)} ngày lỗi."
        )
        st.caption("AI nhận số liệu tổng hợp và nhóm vấn đề; không nhận toàn bộ dữ liệu CSV hay giá trị từng dòng.")

        if st.button(
            "🤖 Giải thích lỗi và đề xuất thứ tự xử lý bằng Ollama",
            type="primary",
            use_container_width=True,
            key="run_local_quality_ai",
        ):
            if not ollama_model:
                st.warning("Nhập tên model Ollama trước khi chạy.")
            else:
                system_prompt = (
                    "Bạn là trợ lý Data Quality cho người mới học Data Analyst. "
                    "Chỉ dựa trên JSON thống kê được cung cấp; không bịa dữ liệu, không tự suy ra giá trị chưa có. "
                    "Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu, có các mục: "
                    "1) Tóm tắt chất lượng dữ liệu; 2) Lỗi quan trọng và tác động; "
                    "3) Thứ tự xử lý đề xuất; 4) Việc cần người dùng xác nhận; "
                    "5) So sánh trước và sau làm sạch dựa đúng các chỉ số trong JSON; "
                    "6) Kiểm tra sau làm sạch. Không đề nghị tự đổi giá trị lỗi thành 0; "
                    "không khẳng định dữ liệu đã được sửa nếu nhật ký không cho thấy điều đó. "
                    "Nhắc rằng thống kê có thể phản ánh dữ liệu đang lọc ở phần Data Quality, "
                    "trong khi quy trình làm sạch chạy trên toàn bộ CSV đã tải lên."
                )
                user_prompt = (
                    "Hãy giải thích chất lượng dữ liệu dựa trên JSON sau. "
                    "Phân biệt rõ lỗi đã phát hiện, thao tác đã ghi trong nhật ký và khuyến nghị chưa thực hiện.\n\n"
                    + json.dumps(quality_ai_payload, ensure_ascii=False, indent=2, default=str)
                )
                try:
                    with st.spinner("Đang yêu cầu Ollama local giải thích chất lượng dữ liệu..."):
                        ai_response = requests.post(
                            f"{ollama_url}/api/chat",
                            json={
                                "model": ollama_model,
                                "stream": False,
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt},
                                ],
                                "options": {"temperature": 0.2},
                            },
                            timeout=180,
                        )
                    if ai_response.status_code != 200:
                        detail = ai_response.text[:1000]
                        st.error(
                            f"Ollama trả về HTTP {ai_response.status_code}. "
                            f"Kiểm tra tên model bằng `ollama list`. Chi tiết: {detail}"
                        )
                    else:
                        ai_json = ai_response.json()
                        ai_content = (ai_json.get("message") or {}).get("content", "").strip()
                        if not ai_content:
                            st.error("Ollama phản hồi thành công nhưng không có nội dung. Thử lại hoặc kiểm tra log Ollama.")
                        else:
                            st.session_state.quality_ai_result = ai_content
                            st.session_state.quality_ai_signature = quality_ai_signature
                            st.success("Đã nhận giải thích từ Ollama local.")
                            st.rerun()
                except requests.Timeout:
                    st.error("Ollama hết thời gian chờ. Kiểm tra Ollama đang chạy và model đã được tải.")
                except requests.ConnectionError:
                    st.error(
                        "Không kết nối được Ollama tại địa chỉ đã nhập. Mở PowerShell và chạy `ollama list`; "
                        "nếu Ollama chưa chạy, khởi động Ollama rồi thử lại."
                    )
                except (requests.RequestException, ValueError) as exc:
                    st.error(f"Không thể gọi Ollama hoặc đọc phản hồi: {exc}")

    saved_quality_ai = st.session_state.get("quality_ai_result")
    saved_quality_ai_signature = st.session_state.get("quality_ai_signature")
    if saved_quality_ai and saved_quality_ai_signature == quality_ai_signature:
        st.markdown("#### Kết quả giải thích từ Ollama")
        st.markdown(saved_quality_ai)
        st.caption("Nội dung AI là khuyến nghị. Hãy kiểm tra dữ liệu và xác nhận trước khi thực hiện thay đổi.")
    elif saved_quality_ai:
        st.info("Thống kê hoặc nhật ký đã thay đổi. Hãy chạy lại Ollama để tạo lời giải thích khớp với trạng thái hiện tại.")

    # Combined report: deterministic Python metrics + AI narrative from the same payload signature.
    current_before_after = st.session_state.get("before_after_report_data")
    if (
        saved_quality_ai
        and saved_quality_ai_signature == quality_ai_signature
        and isinstance(current_before_after, dict)
    ):
        st.markdown("#### 📄 Xuất báo cáo tổng kết có AI")
        st.caption("Báo cáo gộp số liệu trước–sau do Python tính toán với phần giải thích Ollama. AI chỉ đưa ra nhận xét, không thay đổi dữ liệu.")
        ai_report_generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
        ai_report_md_lines = [
            "# Báo cáo Data Quality có giải thích AI",
            "",
            f"- Tệp nguồn: `{current_before_after.get('source_file', 'uploaded.csv')}`",
            f"- Thời gian xuất báo cáo: {ai_report_generated_at}",
            "- File CSV gốc không bị ghi đè.",
            "",
            "## So sánh trước và sau làm sạch",
            "",
            "| Chỉ số | Trước | Sau | Chênh lệch | Đánh giá |",
            "|---|---:|---:|---:|---|",
        ]
        for row in current_before_after.get("comparison", []):
            ai_report_md_lines.append(
                f"| {row.get('Chỉ số', '')} | {row.get('Trước làm sạch', '')} | "
                f"{row.get('Sau làm sạch', '')} | {row.get('Chênh lệch (sau - trước)', '')} | {row.get('Đánh giá', '')} |"
            )
        ai_report_md_lines.extend([
            "",
            "## Giải thích và khuyến nghị từ Ollama local",
            "",
            saved_quality_ai,
            "",
            "## Lưu ý",
            "",
            "- Các chỉ số được tính bằng Python/Pandas; phần AI là diễn giải dựa trên dữ liệu tổng hợp.",
            "- Khuyến nghị của AI không tự thực hiện thay đổi dữ liệu.",
            "- Giá trị lỗi chưa được xử lý vẫn cần người dùng kiểm tra.",
            "",
        ])
        ai_report_md = "\n".join(ai_report_md_lines)
        ai_report_json = {
            "report_type": "data_quality_before_after_with_ai",
            "generated_at": ai_report_generated_at,
            "source_file": current_before_after.get("source_file", "uploaded.csv"),
            "source_file_overwritten": False,
            "before": current_before_after.get("before", {}),
            "after": current_before_after.get("after", {}),
            "comparison": current_before_after.get("comparison", []),
            "cleaning_summary": current_before_after.get("cleaning_summary", {}),
            "cleaning_log": current_before_after.get("cleaning_log", []),
            "remaining_issue_occurrences": current_before_after.get("remaining_issue_occurrences"),
            "ai_provider": "ollama_local",
            "ai_model": ollama_model,
            "ai_explanation": saved_quality_ai,
            "note": "Python/Pandas tạo số liệu; Ollama giải thích; không cần API trả phí.",
        }
        ai_report_stem = re.sub(
            r"\.csv$", "", str(current_before_after.get("source_file") or "data"), flags=re.IGNORECASE
        ) or "data"
        ai_export_md, ai_export_json = st.columns(2)
        with ai_export_md:
            st.download_button(
                "⬇️ Báo cáo tổng kết AI (Markdown)",
                data=ai_report_md.encode("utf-8-sig"),
                file_name=f"{ai_report_stem}_data_quality_ai_report.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_combined_ai_report_md",
            )
        with ai_export_json:
            st.download_button(
                "⬇️ Báo cáo tổng kết AI (JSON)",
                data=json.dumps(ai_report_json, ensure_ascii=False, indent=2, default=str).encode("utf-8-sig"),
                file_name=f"{ai_report_stem}_data_quality_ai_report.json",
                mime="application/json",
                use_container_width=True,
                key="download_combined_ai_report_json",
            )

    # -----------------------------------------------------
    # SQLITE HISTORY — SAVE AND REVIEW ANALYSIS RUNS
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "🗃️ Lịch sử phân tích (SQLite)",
        "Lưu thủ công từng lần chạy để xem lại chỉ số, nhật ký làm sạch và giải thích AI. Lịch sử được lưu cục bộ trong project.",
    )

    current_cleaned_for_history = st.session_state.get("cleaned_df")
    current_cleaning_for_history = st.session_state.get("cleaning_log")
    current_signature_for_history = (
        st.session_state.get("last_filename"),
        int(len(source_df)) if isinstance(source_df, pd.DataFrame) else 0,
        int(len(source_df.columns)) if isinstance(source_df, pd.DataFrame) else 0,
    )
    valid_cleaning_for_history = (
        isinstance(current_cleaned_for_history, pd.DataFrame)
        and current_cleaning_for_history is not None
        and st.session_state.get("cleaned_source_signature") == current_signature_for_history
    )

    current_before_summary = {}
    current_after_summary = None
    current_comparison_rows = []
    current_cleaning_summary = {}
    current_cleaning_log = []
    if isinstance(source_df, pd.DataFrame):
        try:
            current_before_summary = build_data_quality_report(source_df).get("summary", {})
        except Exception as exc:
            st.warning(f"Không thể tạo thống kê gốc cho lịch sử: {exc}")

    if valid_cleaning_for_history:
        try:
            current_after_summary = build_data_quality_report(current_cleaned_for_history).get("summary", {})
            if isinstance(current_cleaning_for_history, dict):
                current_cleaning_summary = current_cleaning_for_history.get("summary", {})
                log_obj = current_cleaning_for_history.get("log")
                if isinstance(log_obj, pd.DataFrame):
                    current_cleaning_log = log_obj.to_dict(orient="records")
                elif isinstance(log_obj, list):
                    current_cleaning_log = log_obj
        except Exception as exc:
            st.warning(f"Không thể tạo thống kê sau làm sạch cho lịch sử: {exc}")

    current_report_for_history = st.session_state.get("before_after_report_data")
    if isinstance(current_report_for_history, dict):
        current_before_summary = current_report_for_history.get("before", current_before_summary)
        current_after_summary = current_report_for_history.get("after", current_after_summary)
        current_comparison_rows = current_report_for_history.get("comparison", [])
        current_cleaning_summary = current_report_for_history.get("cleaning_summary", current_cleaning_summary)
        current_cleaning_log = current_report_for_history.get("cleaning_log", current_cleaning_log)

    current_ai_for_history = st.session_state.get("quality_ai_result")
    current_ai_signature_for_history = st.session_state.get("quality_ai_signature")
    # Only attach the AI explanation if its signature still matches the current inputs.
    ai_signature_is_current = bool(
        current_ai_for_history
        and current_ai_signature_for_history
        and current_ai_signature_for_history == quality_ai_signature
    )
    current_ai_text_for_history = current_ai_for_history if ai_signature_is_current else None
    current_model_for_history = st.session_state.get("quality_ai_ollama_model", "qwen2.5:3b")

    if isinstance(source_df, pd.DataFrame):
        st.caption(
            f"Đang có dữ liệu: {st.session_state.get('last_filename') or 'uploaded.csv'} · "
            f"{len(source_df):,} dòng · {len(source_df.columns):,} cột."
        )
        if st.button(
            "💾 Lưu lần phân tích hiện tại vào SQLite",
            type="primary",
            use_container_width=True,
            key="save_current_analysis_history",
        ):
            now = datetime.now().astimezone().isoformat(timespec="seconds")
            history_status = "Đã làm sạch (bản xem trước)" if current_after_summary is not None else "Chỉ phân tích dữ liệu gốc"
            history_report = {
                "report_type": "data_quality_history_snapshot",
                "created_at": now,
                "source_file": st.session_state.get("last_filename") or "uploaded.csv",
                "before": current_before_summary,
                "after": current_after_summary,
                "comparison": current_comparison_rows,
                "cleaning_summary": current_cleaning_summary,
                "cleaning_log": current_cleaning_log,
                "ai_provider": "ollama_local" if current_ai_text_for_history else None,
                "ai_model": current_model_for_history if current_ai_text_for_history else None,
                "ai_explanation": current_ai_text_for_history,
                "source_file_overwritten": False,
            }
            history_record = {
                "created_at": now,
                "source_file": st.session_state.get("last_filename") or "uploaded.csv",
                "status": history_status,
                "rows_before": current_before_summary.get("row_count", len(source_df)),
                "rows_after": (
                    current_after_summary.get("row_count")
                    if isinstance(current_after_summary, dict)
                    else None
                ),
                "ai_model": current_model_for_history if current_ai_text_for_history else None,
                "metrics": {
                    "before": current_before_summary,
                    "after": current_after_summary,
                    "comparison": current_comparison_rows,
                    "cleaning_summary": current_cleaning_summary,
                },
                "cleaning_log": current_cleaning_log,
                "ai_explanation": current_ai_text_for_history,
                "report": history_report,
            }
            try:
                new_history_id = save_history_record(history_record)
                st.success(f"Đã lưu lần phân tích #{new_history_id} vào SQLite.")
            except (sqlite3.Error, OSError, ValueError) as exc:
                st.error(f"Không lưu được lịch sử SQLite: {exc}")

    try:
        recent_history = load_history_records(limit=50)
        if recent_history:
            history_table = pd.DataFrame([
                {
                    "ID": item["id"],
                    "Thời gian": item["created_at"],
                    "Tệp": item["source_file"],
                    "Trạng thái": item["status"],
                    "Dòng trước": item["rows_before"],
                    "Dòng sau": item["rows_after"],
                    "Model AI": item["ai_model"] or "Chưa chạy AI",
                }
                for item in recent_history
            ])
            st.markdown("#### Các lần phân tích gần đây")
            st.dataframe(history_table, use_container_width=True, hide_index=True)

            history_ids = [item["id"] for item in recent_history]
            selected_history_id = st.selectbox(
                "Chọn lần phân tích để xem chi tiết",
                options=history_ids,
                format_func=lambda value: next(
                    (
                        f"#{item['id']} · {item['created_at']} · {item['source_file']}"
                        for item in recent_history if item["id"] == value
                    ),
                    f"#{value}",
                ),
                key="selected_analysis_history_id",
            )
            selected_history = load_history_record(selected_history_id)
            if selected_history:
                detail_col1, detail_col2 = st.columns(2)
                with detail_col1:
                    st.metric("Số dòng trước", format_number(selected_history.get("rows_before")))
                with detail_col2:
                    st.metric(
                        "Số dòng sau",
                        format_number(selected_history.get("rows_after"))
                        if selected_history.get("rows_after") is not None
                        else "Chưa làm sạch",
                    )
                with st.expander("Xem chi tiết bản ghi lịch sử"):
                    st.json({
                        "id": selected_history.get("id"),
                        "created_at": selected_history.get("created_at"),
                        "source_file": selected_history.get("source_file"),
                        "status": selected_history.get("status"),
                        "metrics": selected_history.get("metrics", {}),
                        "cleaning_log": selected_history.get("cleaning_log", []),
                        "ai_model": selected_history.get("ai_model"),
                        "ai_explanation": selected_history.get("ai_explanation"),
                    })
                st.download_button(
                    "⬇️ Tải bản ghi lịch sử JSON",
                    data=json.dumps(
                        {
                            "id": selected_history.get("id"),
                            "created_at": selected_history.get("created_at"),
                            "source_file": selected_history.get("source_file"),
                            "status": selected_history.get("status"),
                            "metrics": selected_history.get("metrics", {}),
                            "cleaning_log": selected_history.get("cleaning_log", []),
                            "ai_model": selected_history.get("ai_model"),
                            "ai_explanation": selected_history.get("ai_explanation"),
                            "report": selected_history.get("report", {}),
                        },
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ).encode("utf-8-sig"),
                    file_name=f"analysis_history_{selected_history_id}.json",
                    mime="application/json",
                    key=f"download_history_json_{selected_history_id}",
                )
        else:
            st.info("Chưa có bản ghi nào. Tải CSV, kiểm tra dữ liệu rồi bấm ‘Lưu lần phân tích hiện tại vào SQLite’.")
        st.caption(f"Cơ sở dữ liệu lịch sử cục bộ: `{HISTORY_DB_PATH.name}`")
    except (sqlite3.Error, OSError, ValueError) as exc:
        st.error(f"Không đọc được lịch sử SQLite: {exc}")


    # -----------------------------------------------------
    # DETERMINISTIC INSIGHTS
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "💡 Nhận xét thống kê",
        "Nhận xét dựa trên kết quả tính toán từ backend.",
    )

    insights = result.get("deterministic_insights") or []
    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.info("Backend chưa trả về nhận xét thống kê.")

    # -----------------------------------------------------
    # AI EXPLANATION
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "🤖 Diễn giải từ AI",
        "AI chỉ hỗ trợ diễn giải; không thay thế số liệu thống kê.",
    )

    filtered_ai_result = st.session_state.get("filtered_ai_result")
    if (
        filtered_ai_result
        and st.session_state.get("filtered_ai_signature") == filtered_signature
    ):
        ai_source_result = filtered_ai_result
        st.caption("Phạm vi diễn giải: dữ liệu sau khi áp dụng bộ lọc hiện tại.")
    else:
        ai_source_result = result
        st.caption(
            "Phạm vi diễn giải hiện có: toàn bộ CSV ban đầu. "
            "Để đồng bộ với bộ lọc, hãy tạo diễn giải AI ở phần phía trên."
        )

    ai_explanation = ai_source_result.get("ai_explanation") or {}
    ai_mode = ai_explanation.get("mode", "unknown")
    ai_text = ai_explanation.get(
        "result",
        "Chưa có phần diễn giải.",
    )

    if ai_mode == "ai_reference":
        st.info("Nguồn: AI — nội dung tham khảo.")
    elif ai_mode == "deterministic":
        st.warning("Đang sử dụng nội dung dự phòng, không phải diễn giải AI.")

    # Không render chuỗi AI bằng HTML không kiểm soát.
    st.markdown(ai_text)

    if ai_explanation.get("note"):
        st.caption(ai_explanation["note"])

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------
    st.divider()
    section_heading(
        "📥 Xuất báo cáo",
        "Tải kết quả API và bảng KPI kinh doanh.",
    )

    export1, export2 = st.columns(2)

    with export1:
        show_json_download(result)

    with export2:
        export_metrics = {
            "file": st.session_state.last_filename,
            "row_count": report.get("row_count"),
            "column_count": report.get("column_count"),
            "duplicate_rows": report.get("duplicate_rows"),
            "missing_count": missing_count,
            "revenue_column": revenue_col,
            "total_revenue": metrics["total_revenue"],
            "orders_column": orders_col,
            "total_orders": metrics["total_orders"],
            "average_order_value": metrics["average_order_value"],
            "employee_column": employee_col,
            "employee_count": metrics["employee_count"],
        }

        st.download_button(
            "⬇️ Tải KPI kinh doanh CSV",
            data=pd.DataFrame([export_metrics]).to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="business_kpis.csv",
            mime="text/csv",
            use_container_width=True,
        )


# =========================================================
# 9. FOOTER
# =========================================================
st.divider()
st.caption(
    "AI Data Analyst Dashboard · Python · Pandas · "
    "Streamlit · FastAPI · Ollama"
)
st.caption(
    "Các KPI được tính từ dữ liệu CSV đã tải lên. "
    "Không suy diễn tỷ lệ tăng trưởng nếu thiếu dữ liệu theo kỳ."
)
