import ast
import re
import unicodedata
from pathlib import Path

import pandas as pd


def load_dashboard_functions():
    """Load only selected functions; do not launch the Streamlit UI."""
    dashboard_path = Path(__file__).resolve().parents[1] / "dashboard.py"
    source = dashboard_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    wanted_functions = {
        "normalize_name",
        "find_column",
        "to_numeric_series",
        "parse_date_series",
        "build_data_quality_report",
        "detect_cleaning_columns",
        "build_cleaned_candidate",
    }
    wanted_constants = {
        "REVENUE_ALIASES",
        "ORDER_ALIASES",
        "EMPLOYEE_ALIASES",
        "DATE_ALIASES",
        
    }

    selected_nodes = []
    found_functions = set()
    found_constants = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in wanted_functions:
                selected_nodes.append(node)
                found_functions.add(node.name)

        elif isinstance(node, ast.Assign):
            assigned_names = {
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            }
            if assigned_names & wanted_constants:
                selected_nodes.append(node)
                found_constants.update(assigned_names & wanted_constants)

    missing_functions = wanted_functions - found_functions
    missing_constants = wanted_constants - found_constants

    if missing_functions or missing_constants:
        raise RuntimeError(
            f"Dashboard functions/constants missing: "
            f"{missing_functions}, {missing_constants}"
        )

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {
        "pd": pd,
        "re": re,
        "unicodedata": unicodedata,
    }
    exec(compile(module, str(dashboard_path), "exec"), namespace)
    return namespace


FUNCTIONS = load_dashboard_functions()
build_data_quality_report = FUNCTIONS["build_data_quality_report"]
detect_cleaning_columns = FUNCTIONS["detect_cleaning_columns"]
build_cleaned_candidate = FUNCTIONS["build_cleaned_candidate"]
to_numeric_series = FUNCTIONS["to_numeric_series"]


def test_quality_report_detects_missing_invalid_values_and_duplicates():
    df = pd.DataFrame({
        "revenue": ["100", "abc", "", "100"],
        "date": ["2026-10-01", "bad-date", "2026-10-03", "2026-10-01"],
        "employee": ["An", "Binh", "Chi", "An"],
    })

    report = build_data_quality_report(df)
    summary = report["summary"]

    assert summary["row_count"] == 4
    assert summary["column_count"] == 3
    assert summary["missing_cells"] == 1
    assert summary["duplicate_rows"] == 1
    assert summary["invalid_numeric_cells"] == 1
    assert summary["invalid_date_cells"] == 1

    issue_types = set(report["issue_details"].iloc[:, 3])
    assert "Gi\u00e1 tr\u1ecb thi\u1ebfu" in issue_types
    assert "Gi\u00e1 tr\u1ecb s\u1ed1 kh\u00f4ng h\u1ee3p l\u1ec7" in issue_types
    assert "Ng\u00e0y kh\u00f4ng h\u1ee3p l\u1ec7" in issue_types
    assert "D\u00f2ng tr\u00f9ng l\u1eb7p" in issue_types


def test_quality_report_does_not_modify_source_dataframe():
    df = pd.DataFrame({
        "revenue": ["1,200", "invalid", ""],
        "date": ["2026-10-01", "bad-date", "2026-10-03"],
    })
    original = df.copy(deep=True)

    build_data_quality_report(df)

    pd.testing.assert_frame_equal(df, original)


def test_numeric_parser_does_not_turn_invalid_values_into_zero():
    values = pd.Series(["1,200", "1.500.000", "invalid", "", None])
    result = to_numeric_series(values)

    assert result.iloc[0] == 1200
    assert result.iloc[1] == 1500000
    assert pd.isna(result.iloc[2])
    assert pd.isna(result.iloc[3])
    assert pd.isna(result.iloc[4])


def test_detect_cleaning_columns_finds_numeric_and_date_columns():
    df = pd.DataFrame({
        "revenue": ["100", "200", "invalid"],
        "date": ["2026-10-01", "2026-10-02", "bad-date"],
        "employee": ["An", "Binh", "Chi"],
    })

    numeric_columns, date_columns = detect_cleaning_columns(df)

    assert "revenue" in numeric_columns
    assert "date" in date_columns
    assert "employee" not in date_columns


def test_cleaning_preserves_invalid_values_and_original_dataframe():
    df = pd.DataFrame({
        "revenue": ["1,200", "invalid", ""],
        "date": ["01/10/2026", "bad-date", "2026-10-03"],
    })
    original = df.copy(deep=True)

    cleaned, log, summary = build_cleaned_candidate(
        df,
        numeric_columns=["revenue"],
        date_columns=["date"],
        remove_duplicates=False,
    )

    pd.testing.assert_frame_equal(df, original)
    assert cleaned.loc[0, "revenue"] == 1200.0
    assert cleaned.loc[1, "revenue"] == "invalid"
    assert cleaned.loc[2, "revenue"] == ""
    assert cleaned.loc[1, "date"] == "bad-date"
    assert summary["rows_before"] == 3
    assert summary["rows_after"] == 3
    assert summary["duplicate_rows_removed"] == 0
    assert not log.empty


def test_duplicate_rows_are_removed_only_when_selected():
    df = pd.DataFrame({
        "revenue": ["100", "100", "200"],
        "employee": ["An", "An", "Binh"],
    })
    original = df.copy(deep=True)

    kept, _, kept_summary = build_cleaned_candidate(
        df, ["revenue"], [], False
    )
    removed, _, removed_summary = build_cleaned_candidate(
        df, ["revenue"], [], True
    )

    assert len(kept) == 3
    assert kept_summary["duplicate_rows_removed"] == 0
    assert len(removed) == 2
    assert removed_summary["duplicate_rows_removed"] == 1
    pd.testing.assert_frame_equal(df, original)



def test_filtered_dataframe_preserves_original_csv_row_numbers():
    import pandas as pd

    source = pd.DataFrame({
        "employee": ["An", "Binh", "Chi", "Dung"],
        "doanh_thu": [100, None, 300, None],
    })

    filtered = source.loc[[1, 3]].copy()
    report = build_data_quality_report(filtered)
    details = report["issue_details"]
    rows = details.loc[
        details.iloc[:, 1] == "doanh_thu", details.columns[0]
    ].tolist()

    assert sorted(rows) == [3, 5]


def test_reset_index_can_make_csv_row_numbers_inaccurate():
    import pandas as pd

    source = pd.DataFrame({
        "employee": ["An", "Binh", "Chi", "Dung"],
        "doanh_thu": [100, None, 300, None],
    })

    filtered = source.loc[[1, 3]].reset_index(drop=True)
    report = build_data_quality_report(filtered)
    details = report["issue_details"]
    rows = details.loc[
        details.iloc[:, 1] == "doanh_thu", details.columns[0]
    ].tolist()

    # Documents current behavior when the original index is lost.
    assert sorted(rows) == [2, 3]
