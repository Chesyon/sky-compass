# Copyright 2026 Chesyon, under the MIT license
from pydantic import BaseModel
from enum import Enum


class Region(str, Enum):
    REGION_NA = "na"
    REGION_EU = "eu"
    REGION_JP = "jp"


class Issue(str, Enum):
    ISSUE_VERIFICATION_FAILED = "VERIFICATION_FAILED"
    ISSUE_INVALID_SECTION = "INVALID_SECTION"
    ISSUE_FINDING_AUTOMATICALLY = "FINDING_AUTOMATICALLY"
    ISSUE_NO_VALID_SECTIONS = "NO_VALID_SECTIONS"
    ISSUE_MULTIPLE_VALID_SECTIONS = "MULTIPLE_VALID_SECTIONS"


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
