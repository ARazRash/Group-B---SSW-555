import unittest

from gedcom_report import (
    find_over_age_limit,
    format_living_married_rows,
    parse_gedcom,
)


class Sprint2Test(unittest.TestCase):
    def test_over_age_limit(self):
        sample = [
            "0 @I5@ INDI",
            "1 NAME My /Brother/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 23 OCT 2003",
        ]

        individuals, families = parse_gedcom(sample)
        rows = find_over_age_limit(individuals)
        self.assertEqual(rows, [])

    def test_living_married(self):
        other_sample = [
            "0 @I7@ INDI",
            "1 NAME Some /Dude/",
            "1 SEX M",
            "1 DEAT",
            "2 DATE 12 JAN 2010",
            "1 FAMS @F5@",
            "0 @I8@ INDI",
            "1 NAME Some /Dudette/",
            "1 SEX F",
            "1 DEAT",
            "2 DATE 12 JAN 2010",
            "1 FAMS @F5@",
            "0 @F5@ FAM",
            "1 HUSB @I7@",
            "1 WIFE @I8@",
            "1 MARR",
            "2 DATE 29 JUN 2005",
        ]

        individuals, families = parse_gedcom(other_sample)
        rows = format_living_married_rows(individuals)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()