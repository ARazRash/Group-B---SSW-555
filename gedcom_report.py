import argparse
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Set


MONTHS = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}


@dataclass
class Individual:
    individual_id: str
    name: str = "NA"
    gender: str = "NA"
    birthday: Optional[date] = None
    death: Optional[date] = None
    death_recorded: bool = False
    child_families: Set[str] = field(default_factory=set)
    spouse_families: Set[str] = field(default_factory=set)


@dataclass
class Family:
    family_id: str
    married: Optional[date] = None
    divorced: Optional[date] = None
    husband_id: str = "NA"
    wife_id: str = "NA"
    children: Set[str] = field(default_factory=set)


def parse_gedcom_date(date_text):
    parts = date_text.strip().upper().split()
    if len(parts) != 3:
        return None
    day_text, month_text, year_text = parts
    month = MONTHS.get(month_text)
    if month is None:
        return None
    return date(int(year_text), month, int(day_text))


def parse_gedcom(lines):
    individuals = {}
    families = {}
    current_record = None
    current_kind = None
    current_event = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split(maxsplit=2)
        level = parts[0]

        if level == "0":
            current_event = None
            current_record = None
            current_kind = None
            if len(parts) == 3 and parts[1].startswith("@"):
                record_id = clean_id(parts[1])
                record_type = parts[2]
                if record_type == "INDI":
                    current_record = individuals.setdefault(record_id, Individual(record_id))
                    current_kind = "INDI"
                elif record_type == "FAM":
                    current_record = families.setdefault(record_id, Family(record_id))
                    current_kind = "FAM"
            continue

        if current_record is None or len(parts) < 2:
            continue

        tag = parts[1]
        value = parts[2] if len(parts) == 3 else ""

        if level == "1":
            current_event = tag if tag in {"BIRT", "DEAT", "MARR", "DIV"} else None
            if current_kind == "INDI":
                apply_individual_tag(current_record, tag, value)
            elif current_kind == "FAM":
                apply_family_tag(current_record, tag, value)
        elif level == "2" and tag == "DATE":
            parsed_date = parse_gedcom_date(value)
            apply_event_date(current_record, current_kind, current_event, parsed_date)

    return individuals, families


def clean_id(value):
    return value.strip().strip("@")


def apply_individual_tag(individual, tag, value):
    if tag == "NAME":
        individual.name = value
    elif tag == "SEX":
        individual.gender = value
    elif tag == "FAMC":
        individual.child_families.add(clean_id(value))
    elif tag == "FAMS":
        individual.spouse_families.add(clean_id(value))
    elif tag == "DEAT":
        individual.death_recorded = True


def apply_family_tag(family, tag, value):
    if tag == "HUSB":
        family.husband_id = clean_id(value)
    elif tag == "WIFE":
        family.wife_id = clean_id(value)
    elif tag == "CHIL":
        family.children.add(clean_id(value))


def apply_event_date(record, record_kind, event, parsed_date):
    if parsed_date is None:
        return
    if record_kind == "INDI" and event == "BIRT":
        record.birthday = parsed_date
    elif record_kind == "INDI" and event == "DEAT":
        record.death = parsed_date
        record.death_recorded = True
    elif record_kind == "FAM" and event == "MARR":
        record.married = parsed_date
    elif record_kind == "FAM" and event == "DIV":
        record.divorced = parsed_date


def format_individual_rows(individuals, today=None):
    today = today or date.today()
    rows = []
    for individual_id in sorted(individuals, key=natural_id_key):
        individual = individuals[individual_id]
        rows.append([
            individual.individual_id,
            individual.name,
            individual.gender,
            format_date(individual.birthday),
            format_age(individual, today),
            str(not individual.death_recorded),
            format_date(individual.death),
            format_id_set(individual.child_families),
            format_id_set(individual.spouse_families),
        ])
    return rows


def format_family_rows(families, individuals):
    rows = []
    for family_id in sorted(families, key=natural_id_key):
        family = families[family_id]
        rows.append([
            family.family_id,
            format_date(family.married),
            format_date(family.divorced),
            family.husband_id,
            lookup_name(individuals, family.husband_id),
            family.wife_id,
            lookup_name(individuals, family.wife_id),
            format_id_set(family.children),
        ])
    return rows


def format_deceased_rows(individuals, today=None):
    today = today or date.today()
    rows = []
    for individual_id in sorted(individuals, key=natural_id_key):
        individual = individuals[individual_id]
        if individual.death_recorded:
            rows.append([
                individual.individual_id,
                individual.name,
                format_date(individual.death),
                format_age(individual, today),
            ])
    return rows


def format_age_rows(individuals, today=None):
    today = today or date.today()
    rows = []
    for individual_id in sorted(individuals, key=natural_id_key):
        individual = individuals[individual_id]
        rows.append([
            individual.individual_id,
            individual.name,
            format_age(individual, today),
        ])
    return rows


def format_gender_role_errors(families, individuals):
    rows = []
    for family_id in sorted(families, key=natural_id_key):
        family = families[family_id]
        add_gender_role_error(rows, family, individuals, family.husband_id, "Husband", "M")
        add_gender_role_error(rows, family, individuals, family.wife_id, "Wife", "F")
    return rows


def find_duplicate_ids(lines):
    first_seen = {}
    duplicates = []
    for line_number, raw_line in enumerate(lines, start=1):
        parts = raw_line.strip().split(maxsplit=2)
        if len(parts) != 3 or parts[0] != "0" or not parts[1].startswith("@"):
            continue

        record_type = parts[2]
        if record_type not in {"INDI", "FAM"}:
            continue

        clean_record_id = clean_id(parts[1])
        key = (record_type, clean_record_id)
        if key in first_seen:
            display_type = "Individual" if record_type == "INDI" else "Family"
            duplicates.append([
                "ERROR",
                "US22",
                display_type,
                clean_record_id,
                str(first_seen[key]),
                str(line_number),
            ])
        else:
            first_seen[key] = line_number
    return duplicates


def add_gender_role_error(rows, family, individuals, individual_id, role, expected_gender):
    if individual_id == "NA":
        return
    individual = individuals.get(individual_id, Individual(individual_id))
    actual_gender = individual.gender
    if actual_gender != expected_gender:
        rows.append([
            "ERROR",
            "US21",
            family.family_id,
            individual_id,
            individual.name,
            role,
            expected_gender,
            actual_gender,
        ])


def natural_id_key(value):
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", value)
    if not match:
        return (value, 0)
    prefix, number = match.groups()
    return (prefix, int(number))


def format_date(value):
    return value.isoformat() if value else "NA"


def format_age(individual, today):
    if individual.birthday is None:
        return "NA"
    end_date = individual.death or today
    age = end_date.year - individual.birthday.year
    if (end_date.month, end_date.day) < (individual.birthday.month, individual.birthday.day):
        age -= 1
    return str(age)


def format_id_set(values):
    if not values:
        return "NA"
    return "{" + ", ".join(f"'{value}'" for value in sorted(values, key=natural_id_key)) + "}"


def lookup_name(individuals, individual_id):
    if individual_id == "NA":
        return "NA"
    return individuals.get(individual_id, Individual(individual_id)).name


def render_table(title, headers, rows):
    widths = [
        max(len(str(cell)) for cell in [header, *[row[index] for row in rows]])
        for index, header in enumerate(headers)
    ]
    separator = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    header_line = "|" + "|".join(f" {header:<{widths[index]}} " for index, header in enumerate(headers)) + "|"
    body_lines = [
        "|" + "|".join(f" {cell:<{widths[index]}} " for index, cell in enumerate(row)) + "|"
        for row in rows
    ]
    return "\n".join([title, separator, header_line, separator, *body_lines, separator])


def render_story_result(title, headers, rows, empty_message):
    if not rows:
        return f"{title}\n{empty_message}"
    return render_table(title, headers, rows)


def build_report(individuals, families, today=None, source_lines=None):
    individual_headers = ["ID", "Name", "Gender", "Birthday", "Age", "Alive", "Death", "Child", "Spouse"]
    family_headers = [
        "ID",
        "Married",
        "Divorced",
        "Husband ID",
        "Husband Name",
        "Wife ID",
        "Wife Name",
        "Children",
    ]
    age_headers = ["ID", "Name", "Age"]
    deceased_headers = ["ID", "Name", "Death", "Age"]
    gender_headers = ["Type", "Story", "Family ID", "Individual ID", "Name", "Role", "Expected", "Actual"]
    duplicate_headers = ["Type", "Story", "Record Type", "ID", "First Line", "Duplicate Line"]
    individual_table = render_table("Individuals", individual_headers, format_individual_rows(individuals, today))
    family_table = render_table("Families", family_headers, format_family_rows(families, individuals))
    age_table = render_table("US27 Include Individual Ages", age_headers, format_age_rows(individuals, today))
    deceased_table = render_story_result(
        "US29 List Deceased",
        deceased_headers,
        format_deceased_rows(individuals, today),
        "No deceased individuals were found.",
    )
    gender_table = render_story_result(
        "US21 Correct Gender for Role",
        gender_headers,
        format_gender_role_errors(families, individuals),
        "No gender role errors were found.",
    )
    duplicate_table = render_story_result(
        "US22 Unique IDs",
        duplicate_headers,
        find_duplicate_ids(source_lines or []),
        "No duplicate individual or family IDs were found.",
    )
    return f"{individual_table}\n\n{family_table}\n\n{age_table}\n\n{deceased_table}\n\n{gender_table}\n\n{duplicate_table}\n"


def load_gedcom(path):
    with open(path, "r", encoding="utf-8-sig") as gedcom_file:
        return gedcom_file.readlines()


def main():
    parser = argparse.ArgumentParser(description="Print individual and family tables from a GEDCOM file.")
    parser.add_argument("gedcom_file", nargs="?", default="GEDCOME_GroupB", help="GEDCOM input file")
    parser.add_argument("-o", "--output", help="Optional output text file")
    args = parser.parse_args()

    source_lines = load_gedcom(args.gedcom_file)
    individuals, families = parse_gedcom(source_lines)
    report = build_report(individuals, families, source_lines=source_lines)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(report)
    print(report, end="")


if __name__ == "__main__":
    main()
