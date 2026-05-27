# Copyright 2025-2026 Chesyon, under the MIT license
# The 'frontend' for sky-compass.

import argparse
from sky_compass.compass_io import deserialized_io
from sky_compass.section_selection import Issue
from sky_compass.types import CompassRequest, MappingResult


def offset_result_string(result: MappingResult) -> str:
    result = result.result
    if result:
        return hex(result)
    else:
        minimum = result.minimum
        maximum = result.maximum
        if not minimum:
            if not maximum:
                return "Both nearest symbols were missing for this region, so no information can be given"
            return f"The nearest lesser symbol was missing for this region, but the address should be no greater than {hex(maximum)}"
        if not maximum:
            return f"The nearest greater symbol was missing for this region, but the address should be no less than {hex(minimum)}"
        return f"Could not find exact offset. Should be between {hex(minimum)} and {hex(maximum)}"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sky-compass",
        description="CLI util to convert RAM addresses between releases of PMD:EoS using pmdsky-debug symbols.",
    )
    parser.add_argument(
        "region",
        choices=["na", "eu", "jp"],
        type=lambda reg: "na" if reg.lower() == "us" else reg.lower(),
        help="Source region of address",
    )
    parser.add_argument("address", type=lambda addr: int(addr, 16), help="Address to be converted")
    parser.add_argument(
        "section",
        type=lambda sec: sec.lower().replace("overlay", "ov").replace("_", ""),
        nargs="?",
        help="What overlay/section the address is in. If blank, sky-compass will try to figure it out on its own.",
    )
    args = parser.parse_args()
    output = deserialized_io(CompassRequest(address=args.address, region=args.region, section=args.section))
    # TODO: MAYBE add a cli_str function to the Issue class, have the error messages defined there. MULTIPLE_VALID_SECTIONS will probably still need to have some special behavior though.
    for issue in output.issues:
        match issue:
            case Issue.ISSUE_VERIFICATION_FAILED:
                print("Offset isn't in the provided section.")
            case Issue.ISSUE_INVALID_SECTION:
                print("Provided section does not exist.")
            case Issue.ISSUE_FINDING_AUTOMATICALLY:
                print("Finding section automatically...")
            case Issue.ISSUE_NO_VALID_SECTIONS:
                print("Offset was not found in any possible section.")
            case Issue.ISSUE_MULTIPLE_VALID_SECTIONS:
                num_sections = len(output.sections)
                possible_sections_str = f"{num_sections} sections contain this offset: "
                for i in range(num_sections):
                    if i == num_sections - 1:
                        possible_sections_str += "and "
                    possible_sections_str += output.sections[i].cli_str()
                    if i != num_sections - 1:
                        possible_sections_str += ", "
                    else:
                        possible_sections_str += "."
                print(possible_sections_str)
                print("Please retry, providing the desired section.")
    # I could just put exits in the the issues that would stop mapping above, but this is probably better for readability.
    if not output.succeeded:
        exit(1)
    # Display output offsets.
    print(
        f"{hex(args.address)} [{args.region.upper()}] in {output.sections[0]}:\nNA: {offset_result_string(output.na)}\nEU: {offset_result_string(output.eu)}\nJP: {offset_result_string(output.jp)}"
    )


if __name__ == "__main__":
    main()
