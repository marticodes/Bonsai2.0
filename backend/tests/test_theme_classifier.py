import tempfile
import unittest
from pathlib import Path

from app.services.theme_classifier import (
    CATEGORIES,
    classify_themes,
    is_understandable,
    load_classification,
)


class ThemeClassifierTests(unittest.TestCase):
    def test_unreadable_ocr_is_other_and_skips_the_model(self):
        called = []

        def fake_batch(items):
            called.append(items)
            return {index: "Gaming" for index, _text in items}

        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory) / "themes.json"
            result = classify_themes(
                [
                    {
                        "cluster_id": 1,
                        "screenshots": [
                            {
                                "normalized_text": "",
                                "ocr_text": "Like\n12.4K\n|||",
                            }
                        ],
                    },
                    {
                        "cluster_id": 2,
                        "screenshots": [
                            {
                                "normalized_text": "ranked grind on valorant tonight",
                                "ocr_text": "Like\nranked grind on valorant tonight",
                            }
                        ],
                    },
                ],
                classify_batch=fake_batch,
                store_path=stored,
            )

        self.assertEqual(result["posts"][0]["category"], "Other")
        self.assertEqual(result["posts"][1]["category"], "Gaming")
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0], [(1, "ranked grind on valorant tonight")])
        self.assertFalse(is_understandable(""))
        self.assertFalse(is_understandable("12.4K |||"))

    def test_unknown_model_category_becomes_other(self):
        def fake_batch(items):
            return {items[0][0]: "Politics"}

        with tempfile.TemporaryDirectory() as directory:
            result = classify_themes(
                [
                    {
                        "cluster_id": 7,
                        "normalized_text": "senate vote on the climate bill today",
                    }
                ],
                classify_batch=fake_batch,
                store_path=Path(directory) / "themes.json",
            )
        self.assertEqual(result["posts"][0]["category"], "Other")

    def test_percentages_are_counted_in_the_summary_and_stored(self):
        themes = ["Beauty", "Gaming", "Sports"]

        def fake_batch(items):
            return {index: themes[index] for index, _text in items}

        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory) / "themes.json"
            result = classify_themes(
                [
                    {"cluster_id": 1, "normalized_text": "new nail set for prom"},
                    {"cluster_id": 2, "normalized_text": "clutch round in valorant"},
                    {"cluster_id": 3, "normalized_text": "match winning goal tonight"},
                ],
                classify_batch=fake_batch,
                store_path=stored,
            )
            loaded = load_classification(stored)

        self.assertEqual(result["total_posts"], 3)
        self.assertEqual(loaded["total_posts"], 3)
        by_name = {item["category"]: item for item in result["categories"]}
        self.assertEqual([item["category"] for item in result["categories"]], CATEGORIES)
        self.assertEqual(by_name["Beauty"]["count"], 1)
        self.assertEqual(by_name["Beauty"]["percentage"], 33.4)
        self.assertEqual(by_name["Gaming"]["percentage"], 33.3)
        self.assertEqual(by_name["Sports"]["percentage"], 33.3)
        self.assertEqual(by_name["Other"]["count"], 0)
        self.assertEqual(
            round(sum(item["percentage"] for item in result["categories"]), 1),
            100.0,
        )
        self.assertEqual(loaded["posts"][2]["category"], "Sports")

    def test_missing_model_id_is_other(self):
        def fake_batch(_items):
            return {}

        with tempfile.TemporaryDirectory() as directory:
            result = classify_themes(
                [
                    {
                        "cluster_id": 4,
                        "normalized_text": "late night study session notes",
                    }
                ],
                classify_batch=fake_batch,
                store_path=Path(directory) / "themes.json",
            )
        self.assertEqual(result["posts"][0]["category"], "Other")


if __name__ == "__main__":
    unittest.main()
