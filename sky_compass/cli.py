# Copyright 2025-2026 Chesyon, under the MIT license
# The 'frontend' for sky-compass.

import argparse
from section_selection import section_for_offset, Issue
from mapper import Region


def region_from_str(string: str) -> Region | None:
    match string.lower():
        case "na":
            return Region.na
        case "eu":
            return Region.eu
        case "jp":
            return Region.jp
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

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sky-compass",
        description="CLI util to convert RAM addresses between releases of PMD:EoS using pmdsky-debug symbols."
    )
    parser.add_argument("region", choices=['na', 'eu', 'jp'], type=lambda reg: "na" if reg.lower() == "us" else reg.lower(), help="Source region of address")
    parser.add_argument("address", type=lambda addr: int(addr, 16), help="Address to be converted")
    parser.add_argument("section", type=lambda sec: sec.lower().replace("overlay", "ov"), required=False, help="What overlay/section the address is in. If blank, sky-compass will try to figure it out on its own.") # TODO: add choices
    args = parser.parse_args()
    # Region
    region = region_from_str(args.region)
    # Section
    sections, section_issues = section_for_offset(args.address, region, args.section)
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
        na_offset, eu_offset, jp_offset = section.map_offset(args.offset, region)
    else:
        section_name = "overlay36"
        na_offset = hex(args.offset)
        eu_offset = na_offset
        jp_offset = na_offset
    # Display output offsets.
    print(
        f"{hex(args.offset)} [{region_name(region)}] in {section_name}:\nNA: {na_offset}\nEU: {eu_offset}\nJP: {jp_offset}"
    )

if __name__ == "__main__":
    main()
