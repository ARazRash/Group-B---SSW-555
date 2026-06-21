import unittest
from datetime import date

from gedcom_report import format_deceased_rows, parse_gedcom


def parse_sample(text):
    individuals, _ = parse_gedcom(text.strip().splitlines())
    return individuals


class US29ListDeceasedTests(unittest.TestCase):
    def test_lists_deceased_person_with_id_name_death_date_and_age(self):
        individuals = parse_sample("""
0 @I1@ INDI
1 NAME Mandy Willows
1 SEX F
1 BIRT
2 DATE 5 JUL 1985
1 DEAT Y
2 DATE 10 NOV 2007
""")

        rows = format_deceased_rows(individuals, today=date(2026, 6, 21))

        self.assertEqual(rows, [["I1", "Mandy Willows", "2007-11-10", "22"]])

    def test_does_not_list_living_people(self):
        individuals = parse_sample("""
0 @I1@ INDI
1 NAME Living Person
1 SEX F
1 BIRT
2 DATE 1 JAN 2000
""")

        rows = format_deceased_rows(individuals, today=date(2026, 6, 21))

        self.assertEqual(rows, [])

    def test_lists_all_deceased_people_sorted_by_individual_id(self):
        individuals = parse_sample("""
0 @I10@ INDI
1 NAME Later ID
1 SEX M
1 BIRT
2 DATE 1 JAN 1970
1 DEAT Y
2 DATE 1 JAN 2020
0 @I2@ INDI
1 NAME Earlier ID
1 SEX F
1 BIRT
2 DATE 1 JAN 1980
1 DEAT Y
2 DATE 1 JAN 2021
""")

        rows = format_deceased_rows(individuals, today=date(2026, 6, 21))

        self.assertEqual([row[0] for row in rows], ["I2", "I10"])

    def test_uses_death_date_to_calculate_age_at_death(self):
        individuals = parse_sample("""
0 @I1@ INDI
1 NAME Age Check
1 SEX M
1 BIRT
2 DATE 20 DEC 1980
1 DEAT Y
2 DATE 10 JAN 2020
""")

        rows = format_deceased_rows(individuals, today=date(2026, 6, 21))

        self.assertEqual(rows[0][3], "39")

    def test_lists_deceased_person_even_when_death_date_is_missing(self):
        individuals = parse_sample("""
0 @I1@ INDI
1 NAME Missing Death Date
1 SEX F
1 BIRT
2 DATE 1 JAN 1990
1 DEAT Y
""")

        rows = format_deceased_rows(individuals, today=date(2026, 6, 21))

        self.assertEqual(rows, [["I1", "Missing Death Date", "NA", "36"]])


if __name__ == "__main__":
    unittest.main()
