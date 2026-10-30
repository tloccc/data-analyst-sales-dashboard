import unittest
import pandas as pd

from analytics_core import (
    build_pareto_table,
    detect_revenue_anomalies,
    compare_revenue_periods,
    get_top_products,
    generate_business_insights,
)

class TestPareto(unittest.TestCase):
    def test_reaches_80_percent_with_minimum_leading_products(self):
        df = pd.DataFrame({"product": ["A", "B", "C"], "revenue": [80, 15, 5]})
        table, count, share = build_pareto_table(df)
        self.assertEqual(count, 1)
        self.assertAlmostEqual(share, 80.0)
        self.assertEqual(table.iloc[0]["product"], "A")

    def test_aggregates_products_and_excludes_nonpositive_revenue(self):
        df = pd.DataFrame({"product": ["A", "A", "B", "C"], "revenue": [30, 20, -10, 0]})
        table, count, share = build_pareto_table(df)
        self.assertEqual(len(table), 1)
        self.assertEqual(table.iloc[0]["revenue"], 50)
        self.assertEqual(count, 1)
        self.assertAlmostEqual(share, 100.0)

    def test_empty_data(self):
        table, count, share = build_pareto_table(pd.DataFrame({"product": [], "revenue": []}))
        self.assertTrue(table.empty)
        self.assertEqual((count, share), (0, 0.0))

    def test_invalid_threshold_raises(self):
        with self.assertRaises(ValueError):
            build_pareto_table(pd.DataFrame({"product": ["A"], "revenue": [1]}), threshold_pct=0)


class TestAnomalyDetection(unittest.TestCase):
    def test_detects_extreme_high_day(self):
        df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=8), "revenue": [90, 95, 100, 105, 110, 115, 120, 10000]})
        full, flagged, method = detect_revenue_anomalies(df)
        self.assertEqual(len(full), 8)
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged.iloc[0]["reason"], "Cao bất thường")
        self.assertIn("Median Absolute Deviation", method)

    def test_requires_minimum_points(self):
        df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=4), "revenue": [1, 2, 3, 4]})
        full, flagged, method = detect_revenue_anomalies(df)
        self.assertEqual(len(full), 4)
        self.assertTrue(flagged.empty)
        self.assertIn("tối thiểu", method)

    def test_iqr_fallback_when_mad_is_zero(self):
        df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=9), "revenue": [100] * 8 + [10000]})
        # MAD is zero for this distribution; IQR fallback should still flag the outlier.
        full, flagged, method = detect_revenue_anomalies(df)
        self.assertEqual(len(flagged), 1)
        self.assertIn("IQR", method)

    def test_bad_dates_and_revenue_are_removed(self):
        df = pd.DataFrame({"date": ["2026-01-01", "not-a-date"], "revenue": [100, "oops"]})
        full, flagged, method = detect_revenue_anomalies(df, min_points=1)
        self.assertEqual(len(full), 1)
        self.assertTrue(flagged.empty)


class TestRevenueComparison(unittest.TestCase):
    def test_revenue_increases(self):
        current = pd.DataFrame({"revenue": [120, 180]})
        previous = pd.DataFrame({"revenue": [100, 100]})

        result = compare_revenue_periods(current, previous)

        self.assertEqual(result["status"], "increase")
        self.assertEqual(result["current_revenue"], 300)
        self.assertEqual(result["previous_revenue"], 200)
        self.assertAlmostEqual(result["change_pct"], 50.0)

    def test_previous_revenue_zero(self):
        current = pd.DataFrame({"revenue": [100]})
        previous = pd.DataFrame({"revenue": [0]})

        result = compare_revenue_periods(current, previous)

        self.assertEqual(result["status"], "increase_from_zero")
        self.assertIsNone(result["change_pct"])

    def test_missing_column(self):
        current = pd.DataFrame({"sales": [100]})
        previous = pd.DataFrame({"revenue": [50]})

        result = compare_revenue_periods(current, previous)

        self.assertEqual(result["status"], "missing_column")

    def test_invalid_values(self):
        current = pd.DataFrame({"revenue": ["invalid"]})
        previous = pd.DataFrame({"revenue": [100]})

        result = compare_revenue_periods(current, previous)

        self.assertEqual(result["status"], "insufficient_data")


class TestTopProductsAndInsights(unittest.TestCase):
    def test_top_products_aggregate_and_rank(self):
        df = pd.DataFrame({
            "product": ["A", "A", "B", "C"],
            "revenue": [100, 50, 200, -10],
    })

        result = get_top_products(df, top_n=2)

        self.assertEqual(result.iloc[0]["product"], "B")
        self.assertEqual(result.iloc[0]["revenue"], 200)
        self.assertEqual(result.iloc[1]["product"], "A")
        self.assertEqual(result.iloc[1]["revenue"], 150)
        self.assertAlmostEqual(
        result["contribution_pct"].sum(), 100.0
    )

    def test_empty_data_returns_empty_table(self):
        df = pd.DataFrame({
            "product": [],
            "revenue": [],
        })

        result = get_top_products(df)

        self.assertTrue(result.empty)

    def test_insights_are_generated_from_data(self):
        current = pd.DataFrame({
            "product": ["A", "B"],
            "revenue": [300, 100],
    })
        previous = pd.DataFrame({"revenue": [150, 150]})

        insights = generate_business_insights(current, previous)

        self.assertTrue(any("400" in item for item in insights))
        self.assertTrue(any("tăng" in item for item in insights))
        self.assertTrue(any("A" in item for item in insights))


    def test_missing_revenue_column(self):
        df = pd.DataFrame({"product": ["A"]})

        insights = generate_business_insights(df)

        self.assertTrue(any("thiếu cột" in item for item in insights))

if __name__ == "__main__":
    unittest.main()
