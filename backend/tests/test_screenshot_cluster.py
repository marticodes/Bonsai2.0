import unittest

from app.services.screenshot_cluster import cluster_screenshots, texts_match


def shot(timestamp, text, filename):
    return {
        "filename": filename,
        "timestamp_seconds": timestamp,
        "ocr_text": text,
    }


class ClusterTests(unittest.TestCase):
    def test_same_caption_becomes_one_cluster(self):
        clusters = cluster_screenshots([
            shot(0, "Like\nComment\njust got my nails done at the salon", "a.jpg"),
            shot(5, "1.2K\nShare\njust got my nails done at the salon", "b.jpg"),
            shot(10, "For You\njust got my nails done at the salon", "c.jpg"),
        ])

        self.assertEqual(len(clusters), 1)
        names = [item["filename"] for item in clusters[0]["screenshots"]]
        self.assertEqual(names, ["a.jpg", "b.jpg", "c.jpg"])
        self.assertEqual(clusters[0]["screenshots"][0]["timestamp_seconds"], 0)
        self.assertIn("nails", clusters[0]["screenshots"][0]["ocr_text"])
        self.assertIn("nails", clusters[0]["screenshots"][0]["normalized_text"])
        self.assertNotIn("like", clusters[0]["screenshots"][0]["normalized_text"])

    def test_interface_text_alone_does_not_merge(self):
        clusters = cluster_screenshots([
            shot(0, "For You\nLike\nComment\nShare\n12.4K", "a.jpg"),
            shot(5, "Following\nLike\nComment\nShare\n300", "b.jpg"),
        ])

        self.assertEqual(len(clusters), 2)
        self.assertEqual(clusters[0]["screenshots"][0]["normalized_text"], "")
        self.assertEqual(clusters[1]["screenshots"][0]["normalized_text"], "")

    def test_common_words_do_not_merge_different_posts(self):
        self.assertFalse(texts_match(
            "the beach was so fun today",
            "the party was so fun today",
        ))
        clusters = cluster_screenshots([
            shot(0, "the beach was so fun today", "a.jpg"),
            shot(5, "the party was so fun today", "b.jpg"),
        ])
        self.assertEqual(len(clusters), 2)

    def test_distant_similar_text_stays_separate(self):
        clusters = cluster_screenshots([
            shot(0, "summer lake trip with my closest friends", "a.jpg"),
            shot(40, "summer lake trip with my closest friends", "b.jpg"),
        ])
        self.assertEqual(len(clusters), 2)

    def test_caption_continuation_stays_together(self):
        clusters = cluster_screenshots([
            shot(0, "summer lake trip with my closest friends", "a.jpg"),
            shot(5, "summer lake trip with my closest friends and the sunset", "b.jpg"),
        ])
        self.assertEqual(len(clusters), 1)

    def test_repeated_tab_label_does_not_glue_posts(self):
        clusters = cluster_screenshots([
            shot(0, "Reels\npacking for the lake house weekend", "a.jpg"),
            shot(5, "Reels\npacking for the lake house weekend", "b.jpg"),
            shot(10, "Home\ncooking pasta with my roommates tonight", "c.jpg"),
            shot(20, "Reels\nnew skate spot behind the school", "d.jpg"),
            shot(25, "Reels\nnew skate spot behind the school", "e.jpg"),
        ])
        self.assertEqual(
            [len(cluster["screenshots"]) for cluster in clusters],
            [2, 1, 2],
        )
        self.assertNotIn("reels", clusters[0]["screenshots"][0]["normalized_text"])

    def test_short_distinctive_caption_matches(self):
        clusters = cluster_screenshots([
            shot(0, "so tired", "a.jpg"),
            shot(5, "so tired", "b.jpg"),
        ])
        self.assertEqual(len(clusters), 1)

    def test_same_creator_merges_even_when_captions_differ(self):
        clusters = cluster_screenshots([
            shot(0, "@maya.nails\njust got my nails done at the salon", "a.jpg"),
            shot(5, "@maya.nails\nso pretty\nlove this color", "b.jpg"),
            shot(10, "maya.nails\nview all 20 comments", "c.jpg"),
        ])

        self.assertEqual(len(clusters), 1)
        creators = [item["creator"] for item in clusters[0]["screenshots"]]
        self.assertEqual(creators, ["maya.nails", "maya.nails", "maya.nails"])

    def test_display_name_counts_as_the_same_creator(self):
        clusters = cluster_screenshots([
            shot(0, "Maya Nails\npacking for the lake house weekend", "a.jpg"),
            shot(5, "Maya Nails\ncooking pasta with my roommates tonight", "b.jpg"),
        ])

        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["screenshots"][0]["creator"], "Maya Nails")

    def test_different_creators_stay_separate(self):
        clusters = cluster_screenshots([
            shot(0, "@maya.nails\njust got my nails done at the salon", "a.jpg"),
            shot(5, "@jake.trips\nsummer lake trip with my closest friends", "b.jpg"),
        ])

        self.assertEqual(len(clusters), 2)
        self.assertEqual(clusters[0]["screenshots"][0]["creator"], "maya.nails")
        self.assertEqual(clusters[1]["screenshots"][0]["creator"], "jake.trips")

    def test_same_creator_far_apart_stays_separate(self):
        clusters = cluster_screenshots([
            shot(0, "@maya.nails\njust got my nails done at the salon", "a.jpg"),
            shot(40, "@maya.nails\nso pretty", "b.jpg"),
        ])

        self.assertEqual(len(clusters), 2)

    def test_liked_by_handle_is_not_the_creator(self):
        clusters = cluster_screenshots([
            shot(0, "Liked by @maya.nails\npacking for the lake house weekend", "a.jpg"),
            shot(5, "Liked by @maya.nails\ncooking pasta with my roommates tonight", "b.jpg"),
        ])

        self.assertEqual(len(clusters), 2)
        self.assertEqual(clusters[0]["screenshots"][0]["creator"], "")

    def test_preserves_fields_for_a_single_screenshot(self):
        clusters = cluster_screenshots([
            shot(3.5, "Hello THERE", "only.jpg"),
        ])
        saved = clusters[0]["screenshots"][0]
        self.assertEqual(saved["filename"], "only.jpg")
        self.assertEqual(saved["timestamp_seconds"], 3.5)
        self.assertEqual(saved["ocr_text"], "Hello THERE")
        self.assertEqual(saved["normalized_text"], "hello there")
        self.assertEqual(saved["frame_index"], 0)


if __name__ == "__main__":
    unittest.main()
