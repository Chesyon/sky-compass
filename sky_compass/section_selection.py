# Copyright 2025-2026 Chesyon, under the MIT license
# This file handles retrieving the relevant GlobalSection class for an offset.
# If your usage of sky-compass only concerns a few sections (for example, if you KNOW all offsets you're going to be handling are for the script engine), you may wish to write an alternative to this file to save redundant checks.

from mapper import (
    Region,
    GlobalSection,
    Arm7,
    Arm9,
    Libs,
    Itcm,
    Overlay0,
    Overlay1,
    Overlay2,
    Overlay3,
    Overlay4,
    Overlay5,
    Overlay6,
    Overlay7,
    Overlay8,
    Overlay9,
    Overlay10,
    Overlay11,
    Overlay12,
    Overlay13,
    Overlay14,
    Overlay15,
    Overlay16,
    Overlay17,
    Overlay18,
    Overlay19,
    Overlay20,
    Overlay21,
    Overlay22,
    Overlay23,
    Overlay24,
    Overlay25,
    Overlay26,
    Overlay27,
    Overlay28,
    Overlay29,
    MoveEffects,
    Overlay30,
    Overlay31,
    Overlay32,
    Overlay33,
    Overlay34,
    Overlay35,
    Overlay36,
)
from re import compile
from enum import Enum

overlays = [
    Overlay0,
    Overlay1,
    Overlay2,
    Overlay3,
    Overlay4,
    Overlay5,
    Overlay6,
    Overlay7,
    Overlay8,
    Overlay9,
    Overlay10,
    Overlay11,
    Overlay12,
    Overlay13,
    Overlay14,
    Overlay15,
    Overlay16,
    Overlay17,
    Overlay18,
    Overlay19,
    Overlay20,
    Overlay21,
    Overlay22,
    Overlay23,
    Overlay24,
    Overlay25,
    Overlay26,
    Overlay27,
    Overlay28,
    Overlay29,
    Overlay30,
    Overlay31,
    Overlay32,
    Overlay33,
    Overlay34,
    Overlay35,
    Overlay36,
]
sections = [Arm7, Arm9] + overlays

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


def section_for_offset(offset: int, region: Region, name: str | None) -> tuple[list[GlobalSection] | None, list[Enum]]:
    issues: list[Enum] = []
    if name:
        p = compile("ov([0-3]?[0-9])$") # TODO: this can probably be moved outside of the function. we don't need to be compiling this every time, do we?
        m = p.match(name)
        if not m:  # NOT an overlay
            match name:
                case "arm7":
                    if verify_offset(offset, region, Arm7):
                        return [Arm7], issues
                    else:
                        issues.append(Issue.VERIFICATION_FAILED)
                case "arm9":
                    if verify_offset(offset, region, Arm9):
                        return [check_for_arm9_subsection(offset, region)], issues
                    else:
                        issues.append(Issue.VERIFICATION_FAILED)
                case "libs":
                    if verify_offset(offset, region, Libs):
                        return [Libs], issues
                    else:
                        issues.append(Issue.VERIFICATION_FAILED)
                case "itcm":
                    if verify_offset(offset, region, Itcm):
                        return [Itcm], issues
                    else:
                        issues.append(Issue.VERIFICATION_FAILED)
                case "moveeffects":
                    if verify_offset(offset, region, MoveEffects):
                        return [MoveEffects], issues
                    else:
                        issues.append(Issue.VERIFICATION_FAILED)
                case _:
                    issues.append(Issue.INVALID_SECTION)
        else:
            overlay_num = int(m.group(1))
            if overlay_num > 36:
                issues.append(Issue.INVALID_SECTION)
            else:  # User described an overlay that exists. Is the offset in it?
                overlay = overlays[overlay_num]
                if verify_offset(offset, region, overlay):
                    if overlay_num == 29:
                        return [check_for_ov29_subsection(offset, region)], issues
                    return [overlay], issues  # Overlay verified! We're done!
                else:
                    issues.append(Issue.VERIFICATION_FAILED)
    # User either did not provide a name, name was invalid, or offset wasn't in the specified region. Find it ourselves!
    issues.append(Issue.FINDING_AUTOMATICALLY)
    potential_sections: list[GlobalSection] = []
    for section in sections:
        if verify_offset(offset, region, section):
            if section is Arm9:
                potential_sections.append(check_for_arm9_subsection(offset, region))
            elif section is Overlay29:
                potential_sections.append(check_for_ov29_subsection(offset, region))
            else:
                potential_sections.append(section)
    if len(potential_sections) < 1:
        issues.append(Issue.NO_VALID_SECTIONS)
    elif len(potential_sections) > 1:
        issues.append(Issue.MULTIPLE_VALID_SECTIONS)
    return potential_sections, issues


def check_for_arm9_subsection(offset: int, region: Region) -> GlobalSection:
    """Returns Libs or Itcm if the offset is in that subsection, otherwise returns Arm9."""
    if verify_offset(offset, region, Libs):
        return Libs
    if verify_offset(offset, region, Itcm):
        return Itcm
    return Arm9


def check_for_ov29_subsection(offset: int, region: Region) -> GlobalSection:
    """Returns move_effects if the offset is in that subsection, otherwise returns Overlay29."""
    if verify_offset(offset, region, MoveEffects):
        return MoveEffects
    return Overlay29


def verify_offset(offset: int, region: Region, section: GlobalSection) -> bool:
    """Checks if the provided offset is within the section for the region."""
    return section.section_by_region(region).in_range(offset)
