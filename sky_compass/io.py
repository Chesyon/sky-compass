# Copyright 2026 Chesyon, under the MIT License
# This file is responsible for communicating between the "frontend" and "backend".

import json
from section_selection import section_for_offset, Issue
from mapper import MappingResult, Region

# TODO: Consider making an enum for response in the same way as Issue.

def region_from_str(string: str) -> Region | None:
    match string:
        case "na":
            return Region.na
        case "eu":
            return Region.eu
        case "jp":
            return Region.jp
        case _:
            return None

# Put a json in, get a json out.
def json_io(s : str) -> str:
    deserialized = json.loads(s)
    output_dat = deserialized_io(deserialized)
    # TODO: Add a short name field to GlobalSection that matches the expected json name. __str__ will use that, and the current one can become a CLI specific function.
    if output_dat["response"] != "Invalid input":
        output_dat.update({"sections": [str(section) for section in output_dat["sections"]]}) # dumps doesn't have a way to map GlobalSection, so we map it ourselves
    # TODO: dumps will convert enums (currently just Issue, but also Response if i make that an enum) into numbers. This may be confusing. Either annotate the enums with their numbers (faster but less readable), or add a __str__ to convert them (i.e Issue.INVALID_SECTION -> "INVALID_SECTION") 
    return json.dumps(output_dat)

# TODO: Can't we make this a class function for MappingResult?
def mapping_result_to_dict(result: MappingResult):
    return {"result": result.result, "min": result.min, "max": result.max}

# TODO: Write typehints for raw
# TODO: Can raw use Mapping?
def deserialized_io(raw, skip_verification : bool = False):
    output = {"response": "Invalid input"}
    if not skip_verification:
        if not isinstance(raw, dict): return output # raw is not a dict (huh?)
        if raw.keys() != ['address', 'region', 'section']: return output
        if not isinstance(raw["address"], int): return output
        if not isinstance(raw["region"], str): return output
        if not isinstance(raw["section"], str): return output
    address = raw["address"]
    region = region_from_str(raw["region"])
    if (not skip_verification) and (not region): return output
    sections, section_issues = section_for_offset(address, region, raw["section"])
    output.update({"sections": sections, "issues": section_issues})
    if len(sections) != 1 or Issue.INVALID_SECTION in section_issues:
        output.update({"response": "Section error"}) # A section issue prevents mapping from continuing. (This is normal; an expected use of sky-compass is just to check the section of an address.)
        return output
    # We're good to map!
    na_result, eu_result, jp_result = sections[0].map_offset(address, region)
    output.update({"response": "Success", "outputs": {"na": mapping_result_to_dict(na_result), "eu": mapping_result_to_dict(eu_result), "jp": mapping_result(jp_result)}})
    return output
