import unittest
from datetime import date

from gedcom_report import (
    format_family_rows,
    format_deceased_rows,
    format_individual_rows,
    parse_gedcom,
    parse_gedcom_date,
)


SAMPLE_GEDCOM = """0 HEAD
0 NOTE GitHub Repository: https://github.com/ARazRash/Group-B---SSW-555
0 @I1@ INDI
1 NAME Janet Willows
1 SEX F
1 BIRT
2 DATE 5 MAY 1962
1 FAMS @F1@
0 @I2@ INDI
1 NAME Alfred Willows
1 SEX M
1 BIRT
2 DATE 2 SEP 1962
1 FAMS @F1@
0 @I3@ INDI
1 NAME Mark Willows
1 SEX M
1 BIRT
2 DATE 1 DEC 1984
1 DEAT Y
2 DATE 10 NOV 2020
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I1@
1 MARR
2 DATE 10 JUN 1983
1 CHIL @I3@
0 TRLR
"""


class GedcomReportTests(unittest.TestCase):
    def test_parse_gedcom_date_formats_day_month_year_as_iso(self):
        self.assertEqual(parse_gedcom_date("5 MAY 1962"), date(1962, 5, 5))

    def test_parse_gedcom_collects_individuals_and_families(self):
        individuals, families = parse_gedcom(SAMPLE_GEDCOM.splitlines())

        self.assertEqual(set(individuals.keys()), {"I1", "I2", "I3"})
        self.assertEqual(set(families.keys()), {"F1"})
        self.assertEqual(individuals["I1"].name, "Janet Willows")
        self.assertEqual(individuals["I3"].child_families, {"F1"})
        self.assertEqual(families["F1"].husband_id, "I2")
        self.assertEqual(families["F1"].wife_id, "I1")
        self.assertEqual(families["F1"].children, {"I3"})
        self.assertEqual(families["F1"].married, date(1983, 6, 10))

    def test_individual_rows_are_sorted_and_include_relationships(self):
        individuals, _ = parse_gedcom(SAMPLE_GEDCOM.splitlines())

        rows = format_individual_rows(individuals, today=date(2026, 6, 15))

        self.assertEqual([row[0] for row in rows], ["I1", "I2", "I3"])
        self.assertEqual(rows[0], ["I1", "Janet Willows", "F", "1962-05-05", "64", "True", "NA", "NA", "{'F1'}"])
        self.assertEqual(rows[2][7], "{'F1'}")
        self.assertEqual(rows[2][8], "NA")

    def test_family_rows_include_spouse_names_and_children(self):
        individuals, families = parse_gedcom(SAMPLE_GEDCOM.splitlines())

        rows = format_family_rows(families, individuals)

        self.assertEqual(rows, [[
            "F1",
            "1983-06-10",
            "NA",
            "I2",
            "Alfred Willows",
            "I1",
            "Janet Willows",
            "{'I3'}",
        ]])

    def test_deceased_rows_list_dead_people_for_us29(self):
        individuals, _ = parse_gedcom(SAMPLE_GEDCOM.splitlines())

        rows = format_deceased_rows(individuals, today=date(2026, 6, 15))

        self.assertEqual(rows, [["I3", "Mark Willows", "2020-11-10", "35"]])


if __name__ == "__main__":
    unittest.main()
