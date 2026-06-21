import unittest
from datetime import date

from gedcom_report import (
    find_duplicate_ids,
    format_age_rows,
    format_gender_role_errors,
    parse_gedcom,
)


def parse_sample(text):
    return parse_gedcom(text.strip().splitlines())


class Sprint1StoryTests(unittest.TestCase):
    def test_us27_lists_each_individual_age(self):
        individuals, _ = parse_sample("""
0 @I1@ INDI
1 NAME Jane Sample
1 SEX F
1 BIRT
2 DATE 15 JUN 2000
""")

        rows = format_age_rows(individuals, today=date(2026, 6, 21))

        self.assertEqual(rows, [["I1", "Jane Sample", "26"]])

    def test_us21_reports_husband_with_wrong_gender(self):
        individuals, families = parse_sample("""
0 @I1@ INDI
1 NAME Jane Sample
1 SEX F
0 @I2@ INDI
1 NAME Mary Sample
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
""")

        rows = format_gender_role_errors(families, individuals)

        self.assertEqual(rows, [["ERROR", "US21", "F1", "I1", "Jane Sample", "Husband", "M", "F"]])

    def test_us21_reports_wife_with_wrong_gender(self):
        individuals, families = parse_sample("""
0 @I1@ INDI
1 NAME John Sample
1 SEX M
0 @I2@ INDI
1 NAME Mark Sample
1 SEX M
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
""")

        rows = format_gender_role_errors(families, individuals)

        self.assertEqual(rows, [["ERROR", "US21", "F1", "I2", "Mark Sample", "Wife", "F", "M"]])

    def test_us21_has_no_rows_when_roles_match_gender(self):
        individuals, families = parse_sample("""
0 @I1@ INDI
1 NAME John Sample
1 SEX M
0 @I2@ INDI
1 NAME Jane Sample
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
""")

        rows = format_gender_role_errors(families, individuals)

        self.assertEqual(rows, [])

    def test_us22_reports_duplicate_individual_and_family_ids(self):
        lines = """
0 @I1@ INDI
1 NAME John Sample
0 @I1@ INDI
1 NAME Duplicate John
0 @F1@ FAM
0 @F1@ FAM
""".strip().splitlines()

        rows = find_duplicate_ids(lines)

        self.assertEqual(rows, [
            ["ERROR", "US22", "Individual", "I1", "1", "3"],
            ["ERROR", "US22", "Family", "F1", "5", "6"],
        ])


if __name__ == "__main__":
    unittest.main()
