# Copyright 2026 Chesyon, under the MIT license
from pydantic import BaseModel
from enum import Enum


class Region(str, Enum):
    REGION_NA = "na"
    REGION_EU = "eu"
    REGION_JP = "jp"


Issue = Enum(
    "Issue",
    [
        "VERIFICATION_FAILED",  # Offset was not in the specified location.
        "INVALID_SECTION",  # Specified section does not exist.
        "FINDING_AUTOMATICALLY",  # Finding section automatically.
        "NO_VALID_SECTIONS",  # This offset doesn't fall within any valid section.
        "MULTIPLE_VALID_SECTIONS",
    ],
)


class MappingResult(BaseModel):
    result: int | None
    minimum: int | None
    maximum: int | None


class CompassRequest(BaseModel):
    address: int
    region: Region
    section: str | None = None


class CompassResponse(BaseModel):
    succeeded: bool
    sections: list[str]
    issues: list[Issue]
    na: MappingResult | None
    eu: MappingResult | None
    jp: MappingResult | None
