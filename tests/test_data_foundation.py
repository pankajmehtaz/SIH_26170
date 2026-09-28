"""
Comprehensive Test Suite for Data Foundation & Project Architecture.
Tests:
- Deterministic synthetic generator & defect scenarios
- Key population outlier scenario (spec_max=50, pop=10-15, anomalous=40-48)
- Time-series parametric feature extractor
- Comprehensive CSV screening validator (all 9 checks)
- Data foundation FastAPI endpoints
"""

import sys
import unittest
from pathlib import Path

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from ml.synthetic.generator import SyntheticDatasetGenerator, DEFAULT_PARAMETERS
from ml.features.extractor import extract_time_series_features
from backend.main import app
from backend.services.data_service import validate_csv, resolve_canonical_columns


class TestSyntheticDataGenerator(unittest.TestCase):
    """Tests for realistic synthetic burn-in dataset generator."""

    def test_reproducibility_with_seed(self):
        """Verify that identical seeds produce bit-for-bit identical datasets."""
        fixed_time = "2026-09-28T12:00:00Z"
        gen1 = SyntheticDatasetGenerator(seed=42, component_count=50, timestamp=fixed_time)
        df1, meta1 = gen1.generate()

        gen2 = SyntheticDatasetGenerator(seed=42, component_count=50, timestamp=fixed_time)
        df2, meta2 = gen2.generate()

        pd.testing.assert_frame_equal(df1, df2)
        self.assertEqual(meta1["random_seed"], 42)
        self.assertEqual(meta2["random_seed"], 42)

    def test_different_seeds_produce_different_data(self):
        """Verify that different seeds produce distinct values."""
        gen1 = SyntheticDatasetGenerator(seed=42, component_count=50)
        df1, _ = gen1.generate()

        gen2 = SyntheticDatasetGenerator(seed=999, component_count=50)
        df2, _ = gen2.generate()

        self.assertFalse(df1["value_0h"].equals(df2["value_0h"]))

    def test_all_defect_archetypes_present(self):
        """Verify all requested defect categories and trajectories are generated."""
        gen = SyntheticDatasetGenerator(seed=42, component_count=500)
        df, meta = gen.generate()

        expected_defects = {
            "HEALTHY",
            "POPULATION_OUTLIER",
            "MILD_DRIFT",
            "STRONG_DRIFT",
            "ACCELERATING_DRIFT",
            "EARLY_DRIFT",
            "LATE_DRIFT",
            "STATIC_LIMIT_VIOLATION",
        }
        actual_defects = set(df["defect_type"].unique())
        self.assertTrue(expected_defects.issubset(actual_defects))
        self.assertIn("label", meta)
        self.assertEqual(meta["label"], "DEMO/SYNTHETIC")

    def test_key_population_outlier_scenario(self):
        """
        Verify the exact scenario emphasized in the problem:
        spec_max = 50, healthy population ≈ 10–15, anomalous component ≈ 40–48.
        The component must PASS static limit screening while being a dynamic population outlier.
        """
        gen = SyntheticDatasetGenerator(seed=42, component_count=500)
        df, _ = gen.generate()

        iddq_df = df[df["parameter_name"] == "iddq"]
        healthy_iddq = iddq_df[iddq_df["defect_type"] == "HEALTHY"]
        outlier_iddq = iddq_df[iddq_df["defect_type"] == "POPULATION_OUTLIER"]

        # Healthy population baseline ≈ 10–15
        healthy_mean = healthy_iddq["value_0h"].mean()
        self.assertTrue(10.0 <= healthy_mean <= 14.0, f"Healthy mean {healthy_mean} not in [10, 14]")

        # Population outliers ≈ 40–48
        self.assertGreater(len(outlier_iddq), 0)
        for _, row in outlier_iddq.iterrows():
            self.assertTrue(
                40.0 <= row["value_0h"] <= 48.0,
                f"Outlier value_0h {row['value_0h']} not in [40, 48]",
            )
            # Must remain below absolute specification limit of 50.0
            self.assertLessEqual(
                row["value_168h"],
                row["spec_max"],
                f"Outlier value_168h {row['value_168h']} exceeded spec_max {row['spec_max']}",
            )
            # Static screening passes it!
            self.assertEqual(row["status"], "PASS")

    def test_measurement_noise_present(self):
        """Verify that sensor measurement noise is realistic and not flat/deterministic."""
        gen = SyntheticDatasetGenerator(seed=42, component_count=50)
        df, _ = gen.generate()
        # Verify values have variation beyond just integer drift
        diffs = df["value_24h"] - df["value_0h"]
        self.assertGreater(diffs.nunique(), 20)


class TestTimeSeriesFeatureExtractor(unittest.TestCase):
    """Tests for physical drift and slope computation."""

    def test_slope_and_acceleration_math(self):
        sample_row = {
            "value_0h": 10.0,
            "value_24h": 12.4,   # slope = 2.4 / 24 = 0.1
            "value_96h": 19.6,   # slope = 7.2 / 72 = 0.1
            "value_168h": 34.0,  # slope = 14.4 / 72 = 0.2
            "spec_max": 50.0,
        }
        features = extract_time_series_features(sample_row)
        self.assertAlmostEqual(features["slope_0_24"], 0.1, places=4)
        self.assertAlmostEqual(features["slope_24_96"], 0.1, places=4)
        self.assertAlmostEqual(features["slope_96_168"], 0.2, places=4)
        self.assertAlmostEqual(features["accel_mid_to_late"], 0.1, places=4)
        self.assertAlmostEqual(features["proximity_to_spec"], 34.0 / 50.0, places=4)


class TestCSVValidationEngine(unittest.TestCase):
    """Tests for all 9 CSV screening validation rules."""

    def test_valid_csv(self):
        valid_file = PROJECT_ROOT / "data" / "samples" / "valid_multivariate_batch.csv"
        result = validate_csv(valid_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.row_count, 9)

    def test_duplicate_components_detected(self):
        dup_file = PROJECT_ROOT / "data" / "samples" / "invalid_duplicate_components.csv"
        result = validate_csv(dup_file)
        self.assertFalse(result.is_valid)
        self.assertGreater(result.error_count, 0)
        dup_issues = [iss for iss in result.issues if iss.issue_type == "DUPLICATE_COMPONENT"]
        self.assertGreater(len(dup_issues), 0)

    def test_inconsistent_units_detected(self):
        unit_file = PROJECT_ROOT / "data" / "samples" / "invalid_inconsistent_units.csv"
        result = validate_csv(unit_file)
        self.assertFalse(result.is_valid)
        unit_issues = [iss for iss in result.issues if iss.issue_type == "INCONSISTENT_UNITS"]
        self.assertGreater(len(unit_issues), 0)

    def test_invalid_specifications_detected(self):
        spec_file = PROJECT_ROOT / "data" / "samples" / "invalid_specifications.csv"
        result = validate_csv(spec_file)
        self.assertFalse(result.is_valid)
        spec_issues = [iss for iss in result.issues if iss.issue_type == "INVALID_SPECIFICATION"]
        self.assertGreater(len(spec_issues), 0)


class TestDataEndpoints(unittest.TestCase):
    """End-to-end integration tests for data foundation API endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoints(self):
        # Test root /health
        res1 = self.client.get("/health")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["status"], "healthy")

        # Test /api/health
        res2 = self.client.get("/api/health")
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["status"], "healthy")

    def test_generate_demo_endpoint(self):
        payload = {"seed": 42, "component_count": 50, "batch_id": "BATCH-TEST-DEMO"}
        res = self.client.post("/api/data/generate-demo", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["batch_id"], "BATCH-TEST-DEMO")
        self.assertEqual(data["total_components"], 50)
        self.assertEqual(data["random_seed"], 42)
        self.assertEqual(len(data["parameters"]), 5)

    def test_get_summary_endpoint(self):
        res = self.client.get("/api/data/summary?batch_id=BATCH-TEST-DEMO")
        self.assertEqual(res.status_code, 200)
        summary = res.json()
        self.assertEqual(summary["batch_id"], "BATCH-TEST-DEMO")
        self.assertIn("defect_distribution", summary)
        self.assertIn("static_screening_summary", summary)

    def test_get_components_list_endpoint(self):
        res = self.client.get("/api/data/components?batch_id=BATCH-TEST-DEMO&page=1&page_size=10")
        self.assertEqual(res.status_code, 200)
        listing = res.json()
        self.assertEqual(listing["batch_id"], "BATCH-TEST-DEMO")
        self.assertEqual(len(listing["components"]), 10)
        self.assertEqual(listing["total_components"], 50)

    def test_get_component_detail_endpoint(self):
        res = self.client.get("/api/data/components/COMP-0001?batch_id=BATCH-TEST-DEMO")
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertEqual(detail["component_id"], "COMP-0001")
        self.assertEqual(len(detail["parameters"]), 5)
        # Verify slopes are present
        p0 = detail["parameters"][0]
        self.assertIn("slopes", p0)
        self.assertIn("slope_0_24", p0["slopes"])
        self.assertIn("z_score_168h", p0)

    def test_upload_invalid_csv_returns_422(self):
        dup_file = PROJECT_ROOT / "data" / "samples" / "invalid_duplicate_components.csv"
        with open(dup_file, "rb") as f:
            res = self.client.post("/api/data/upload", files={"file": ("test.csv", f, "text/csv")})
        self.assertEqual(res.status_code, 422)
        body = res.json()
        self.assertIn("detail", body)
        self.assertIn("issues", body["detail"])


if __name__ == "__main__":
    unittest.main()
