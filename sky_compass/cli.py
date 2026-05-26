# Copyright 2025-2026 Chesyon, under the MIT license
# The 'frontend' for sky-compass.

import argparse
from sky_compass.compass_io import deserialized_io
from sky_compass.section_selection import Issue
from sky_compass.mapper import Region


def region_name(region: Region) -> str:
    match region:
        case Region.na:
            return "NA"
        case Region.eu:
            return "EU"
        case Region.jp:
            return "JP"


# TODO: This probably makes MappingResult.__str__ redundant. IO doesn't even return the MappingResult, it returns a dict, so we can't even *use* that function for the CLI anymore.
def offset_result_string(result_dict) -> str:
    result = result_dict["result"]
    if result:
        return hex(result)
    else:
        min = result_dict["min"]
        max = result_dict["max"]
        if not min:  # if min is None
            if not max:
                return "Both nearest symbols were missing for this region, so no information can be given"
            return f"The nearest lesser symbol was missing for this region, but the address should be no greater than {hex(max)}"
        if not max:
            return f"The nearest greater symbol was missing for this region, but the address should be no less than {hex(min)}"
        return f"Could not find exact offset. Should be between {hex(min)} and {hex(max)}"


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
    )  # TODO: add choices ([str(sec) for sec in sections]? this doesn't include sub-sections though)
    args = parser.parse_args()
    output = deserialized_io({"address": args.address, "region": args.region, "section": args.section}, True)
    sections = output["sections"]
    # TODO: Add a cli_str function to the Issue class, have the error messages defined there. MULTIPLE_VALID_SECTIONS will probably still need to have some special behavior though.
    for issue in output["issues"]:
        match issue:
            case Issue.VERIFICATION_FAILED:
                print("Offset isn't in the provided section.")
            case Issue.INVALID_SECTION:
                # TODO: This shouldn't be possible IF we add choices to the section arg. If this were fatal, I'd remove this case and let argparse handle it, but section selection is specifically DESIGNED to handle invalid sections, so argparse doesn't even need to block this? I might just not need choices at all... still would like a way to tell the user what's considered valid, though.
                print("Provided section does not exist.")
            case Issue.FINDING_AUTOMATICALLY:
                print("Finding section automatically...")
            case Issue.NO_VALID_SECTIONS:
                print("Offset was not found in any possible section.")
            case Issue.MULTIPLE_VALID_SECTIONS:
                num_sections = len(sections)
                possible_sections_str = f"{num_sections} sections contain this offset: "
                for i in range(num_sections):
                    if i == num_sections - 1:
                        possible_sections_str += "and "
                    possible_sections_str += sections[i].cli_str()
                    if i != num_sections - 1:
                        possible_sections_str += ", "
                    else:
                        possible_sections_str += "."
                print(possible_sections_str)
                print("Please retry, providing the desired section.")
    # I could just put exits in the the issues that would stop mapping above, but this is probably better for readability.
    # TODO: Not a huge fan of needing to have the "Success" string defined in two separate places. Either make this an enum in the same way as Issue, or make a constant for this.
    if output["response"] != "Success":
        exit(1)
    # Display output offsets.
    outputs = output["outputs"]
    print(
        f"{hex(args.address)} [{args.region.upper()}] in {sections[0]}:\nNA: {offset_result_string(outputs['na'])}\nEU: {offset_result_string(outputs['eu'])}\nJP: {offset_result_string(outputs['jp'])}"
    )


if __name__ == "__main__":
    main()
