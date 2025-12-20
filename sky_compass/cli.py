# Copyright 2025 Chesyon, under the MIT license
# The 'frontend' for sky-compass.

from section_selection import section_for_offset, Issue
from mapper import Region
from sys import argv as args


def region_from_str(string: str) -> Region | None:
    match string.lower():
        case "na":
            return Region.na
        case "eu":
            return Region.eu
        case "jp":
            return Region.jp
        case "us":
            return Region.na
        case _:
            return None


def region_name(region: Region) -> str:
    match region:
        case Region.na:
            return "NA"
        case Region.eu:
            return "EU"
        case Region.jp:
            return "JP"


if __name__ == "__main__":
    if len(args) < 3:
        print("Please provide a region, an offset, and optionally a section.")
        exit(1)
    # Region
    region = region_from_str(args[1])
    if not region:
        print("Region wasn't recognized. Valid options: na, eu, jp")
        exit(1)
    # Offset
    try:
        offset_str = args[2].lower()
        if offset_str.startswith("0x"):
            offset = int(offset_str[2:], 16)
        else:
            offset = int(offset_str)
    except ValueError as e:
        print("Couldn't parse offset. Error:")
        print(e)
        exit(1)
    # Section
    if len(args) == 3:  # No provided section
        sections, section_issues = section_for_offset(offset, region, None)
    else:
        sections, section_issues = section_for_offset(offset, region, args[3])
    is_ov36 = False
    for issue in section_issues:
        match issue:
            case Issue.VERIFICATION_FAILED:
                print("Offset isn't in the provided section.")
            case Issue.IS_OV36:
                is_ov36 = True
            case Issue.INVALID_SECTION:
                print("Provided section does not exist.")
            case Issue.FINDING_AUTOMATICALLY:
                print("Finding section automatically...")
            case Issue.NO_VALID_SECTIONS:
                print("Offset was not found in any possible section.")
                exit(1)
            case Issue.MULTIPLE_VALID_SECTIONS:
                num_sections = len(sections)
                possible_sections_str = f"{num_sections} sections contain this offset: "
                for i in range(num_sections):
                    if i == num_sections - 1:
                        possible_sections_str += "and "
                    possible_sections_str += sections[i].name
                    if i != num_sections - 1:
                        possible_sections_str += ", "
                    else:
                        possible_sections_str += "."
                print(possible_sections_str)
                print("Please retry, providing the desired section.")
                exit(1)
    # Map
    if not is_ov36:
        section = sections[0]
        section_name = str(section)
        na_offset, eu_offset, jp_offset = section.map_offset(offset, region)
    else:
        section_name = "overlay36"
        na_offset = hex(offset)
        eu_offset = hex(offset)
        jp_offset = hex(offset)
    # Display output offsets.
    print(
        f"{hex(offset)} [{region_name(region)}] in {section_name}:\nNA: {na_offset}\nEU: {eu_offset}\nJP: {jp_offset}"
    )
