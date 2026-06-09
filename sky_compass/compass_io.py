# Copyright 2026 Chesyon, under the MIT license
# This file is responsible for communicating between the "frontend" and "backend".

from sky_compass.section_selection import section_for_offset
from sky_compass.compass_types import CompassRequest, CompassResponse


def deserialized_io(request: CompassRequest) -> CompassResponse:
    sections, section_issues = section_for_offset(request)
    section_names = [str(section) for section in sections]
    if len(sections) != 1:
        return CompassResponse(
            succeeded=False, sections=section_names, issues=section_issues, na=None, eu=None, jp=None
        )
    na_result, eu_result, jp_result = sections[0].map_offset(request.address, request.region)
    return CompassResponse(
        succeeded=True, sections=section_names, issues=section_issues, na=na_result, eu=eu_result, jp=jp_result
    )
