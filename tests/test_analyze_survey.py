import unittest
from collections import Counter

from analyze_survey import recode_alternative_name, recode_status, word_frequencies


class SurveyAnalysisTests(unittest.TestCase):
    def test_status_other_options_are_case_insensitive(self) -> None:
        self.assertEqual(recode_status("Postdoc researcher"), "Other Response Options")
        self.assertEqual(recode_status("Undergraduate student"), "Undergraduate student")

    def test_alternative_names_are_grouped_using_notebook_categories(self) -> None:
        self.assertEqual(
            recode_alternative_name("Bremen Institute of Technology and Science"),
            "Bremen Institute of Technology and Science",
        )
        self.assertEqual(
            recode_alternative_name("IUB"),
            "International University Bremen",
        )
        self.assertEqual(
            recode_alternative_name("Different unique name, please"),
            "A Unique Name",
        )
        self.assertEqual(recode_alternative_name("A new proposal"), "A new proposal")

    def test_word_frequencies_remove_notebook_brand_terms(self) -> None:
        self.assertEqual(
            word_frequencies("Jacobs University Bremen, Bremen community!"),
            Counter({"bremen": 2, "community": 1}),
        )


if __name__ == "__main__":
    unittest.main()
