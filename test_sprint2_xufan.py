import unittest
from datetime import date

from gedcom_report import (
    find_birth_after_death,
    find_dates_after_current_date,
    parse_gedcom,
)


def parse_sample(text):
    return parse_gedcom(text.strip().splitlines())


class Sprint2XufanTests(unittest.TestCase):
    def test_us01_reports_birth_date_after_today(self):
        lines = """
0 @I1@ INDI
1 NAME Future Person
1 BIRT
2 DATE 1 JAN 2030
""".strip().splitlines()

        rows = find_dates_after_current_date(lines, today=date(2026, 7, 6))

        self.assertEqual(rows, [["ERROR", "US01", "I1", "BIRT", "2030-01-01", "4"]])

    def test_us01_reports_family_date_after_today(self):
        lines = """
0 @F1@ FAM
1 MARR
2 DATE 1 JAN 2030
""".strip().splitlines()

        rows = find_dates_after_current_date(lines, today=date(2026, 7, 6))

        self.assertEqual(rows, [["ERROR", "US01", "F1", "MARR", "2030-01-01", "3"]])

    def test_us01_ignores_dates_before_today(self):
        lines = """
0 @I1@ INDI
1 BIRT
2 DATE 1 JAN 2000
""".strip().splitlines()

        rows = find_dates_after_current_date(lines, today=date(2026, 7, 6))

        self.assertEqual(rows, [])

    def test_us03_reports_birth_after_death(self):
        individuals, _ = parse_sample("""
0 @I1@ INDI
1 NAME Backwards Person
1 BIRT
2 DATE 1 JAN 2030
1 DEAT Y
2 DATE 1 JAN 2020
""")

        rows = find_birth_after_death(individuals)

        self.assertEqual(rows, [["ERROR", "US03", "I1", "Backwards Person", "2030-01-01", "2020-01-01"]])

    def test_us03_ignores_valid_birth_and_death_order(self):
        individuals, _ = parse_sample("""
0 @I1@ INDI
1 NAME Normal Person
1 BIRT
2 DATE 1 JAN 1980
1 DEAT Y
2 DATE 1 JAN 2020
""")

        rows = find_birth_after_death(individuals)

        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
