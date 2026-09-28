import os
import sys
import types
import unittest
from unittest.mock import patch

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
if "anthropic" not in sys.modules:
    sys.modules["anthropic"] = types.SimpleNamespace(Anthropic=lambda: object())

import daily_email as app


class ResearchRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = app._load_research_profile()

    def test_profile_uses_published_work_as_mainline(self):
        self.assertEqual(len(self.profile["published_works"]), 3)
        self.assertEqual(
            {topic["tier"] for topic in self.profile["strands"]},
            {"published_mainline", "emerging_extension"},
        )
        self.assertFalse(any("MICM" in topic["name"] for topic in self.profile["strands"]))

    def test_weekly_rotation_keeps_published_work_primary(self):
        tiers = [
            app._select_research_topic(f"2026-09-{day:02d}", self.profile)[0]["tier"]
            for day in range(21, 28)
        ]
        self.assertEqual(tiers.count("published_mainline"), 5)
        self.assertEqual(tiers.count("emerging_extension"), 2)

    def test_own_work_and_retired_micm_line_are_excluded(self):
        own_work = {
            "title": self.profile["published_works"][0]["title"],
            "doi": self.profile["published_works"][0]["doi"],
            "authorships": [{"author": {"display_name": "Gracie Jiaxin Shen"}}],
        }
        retired = {
            "title": "A new MICM model of CSL peer interaction",
            "abstract": "Language-related episodes and negotiation of meaning in peer work.",
            "authorships": [{"author": {"display_name": "Another Author"}}],
        }
        self.assertTrue(app._paper_is_profile_excluded(own_work, self.profile))
        self.assertTrue(app._paper_is_profile_excluded(retired, self.profile))

    def test_fetch_does_not_fall_back_to_weak_candidate(self):
        topic = self.profile["strands"][0]
        weak = {
            "title": "Student motivation in general education",
            "publication_year": 2025,
            "abstract": "A broad survey of student motivation.",
            "abstract_inverted_index": {},
            "cited_by_count": 500,
            "primary_location": {"source": {"display_name": "General Education Journal"}},
            "doi": "https://doi.org/10.0000/weak",
            "authorships": [{"author": {"display_name": "A. Author"}}],
        }
        with patch.object(app, "_select_research_topic", return_value=(topic, 1)), patch.object(
            app, "_openalex_search", return_value=[weak]
        ), patch.object(app, "_load_seen_papers", return_value={"papers": {}}):
            _, papers = app.fetch_research_papers("2026-09-28", limit=3, profile=self.profile)
        self.assertEqual(papers, [])

    def test_exceptionally_close_recent_paper_can_pass_without_citations(self):
        topic = self.profile["strands"][0]
        strong_fit = {
            "title": "Teacher vulnerability and institutional discourse in dual language immersion",
            "publication_year": 2026,
            "abstract": (
                "This critical discourse analysis examines teacher voice, institutional protection, "
                "emotional labor, and school choice in bilingual education."
            ),
            "abstract_inverted_index": {},
            "cited_by_count": 0,
            "primary_location": {"source": {"display_name": "New Qualitative Education Journal"}},
            "doi": "https://doi.org/10.0000/strong",
            "authorships": [{"author": {"display_name": "A. Author"}}],
        }
        with patch.object(app, "_select_research_topic", return_value=(topic, 1)), patch.object(
            app, "_openalex_search", return_value=[strong_fit]
        ), patch.object(app, "_load_seen_papers", return_value={"papers": {}}):
            _, papers = app.fetch_research_papers("2026-09-28", limit=3, profile=self.profile)
        self.assertEqual([paper["title"] for paper in papers], [strong_fit["title"]])


if __name__ == "__main__":
    unittest.main()
