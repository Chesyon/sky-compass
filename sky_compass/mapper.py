# Copyright 2025 Chesyon, under the MIT license
# This file defines all the various RAM sections that are defined in pmdsky-debug, and provides the functions needed to map an offset within a section.

from pmdsky_debug_py.protocol import Symbol
from pmdsky_debug_py import na, eu, jp
from enum import Enum

Region = Enum("Region", ["na", "eu", "jp"])


class RegionSection:
    def __init__(self, section):
        self.start = section.loadaddress
        self.length = section.length
        self.end = self.start + self.length
        self.symbols = dict(section.functions.__dict__)
        self.symbols.update(section.data.__dict__)
        # Create input map (offset:symbolname) and output map (symbolname:offset)
        input_map = {self.start: "SECTION_START"}
        output_map = {"SECTION_START": self.start}
        for symbol_name in self.symbols:
            symbol = self.symbols[symbol_name]
            if type(symbol) is Symbol and symbol.absolute_addresses is not None:
                for i in range(len(symbol.absolute_addresses)):
                    input_map.update({symbol.absolute_addresses[i]: f"{symbol_name}{i}"})
                    output_map.update({f"{symbol_name}{i}": symbol.absolute_addresses[i]})
        input_map.update({self.end: "SECTION_END"})
        output_map.update({"SECTION_END": self.end})
        self.input_map = dict(sorted(input_map.items()))  # sort by key value
        self.output_map = output_map

    def in_range(self, offset: int) -> bool:
        return self.start <= offset <= self.end


class MappingResult:
    def __init__(self, succeeded: bool, result: int | None, min: None | int = None, max: None | int = None):
        self.succeeded = succeeded
        self.result = result
        self.min = min
        self.max = max

    def __str__(self):
        if self.succeeded:
            return hex(self.result)
        else:
            if self.min == -1:
                if self.max == -1:
                    return "Both nearest symbols were missing for this region, so no information can be given"
                return f"The nearest lesser symbol was missing for this region, but the address should be no greater than {hex(self.max)}"
            if self.max == -1:
                return f"The nearest greater symbol was missing for this region, but the address should be no less than {hex(self.min)}"
            return f"Could not find exact offset. Should be between {hex(self.min)} and {hex(self.max)}"


class GlobalSection:
    def __init__(
        self,
        name: str,
        na_section: RegionSection,
        eu_section: RegionSection,
        jp_section: RegionSection,
        parent_section: str | None = None,
    ):
        self.name = name
        self.parent_section = (
            parent_section  # This is ONLY used for string display, and has no functional purpose in the backend.
        )
        self.na_section = na_section
        self.eu_section = eu_section
        self.jp_section = jp_section

    def map_offset(self, offset: int, src_region: Region) -> tuple[MappingResult, MappingResult, MappingResult]:
        """Given an offset and its region, creates mappings for the other two regions. Returns three mapping results; NA, EU, and JP, in that order."""
        na_result = self.map_offset_single_target(offset, src_region, Region.na)
        eu_result = self.map_offset_single_target(offset, src_region, Region.eu)
        jp_result = self.map_offset_single_target(offset, src_region, Region.jp)
        return na_result, eu_result, jp_result

    def map_offset_single_target(self, offset: int, src_region: Region, target_region: Region) -> MappingResult:
        """Given an offset, the region it came from, and the desired region to map to, creates a MappingResult."""
        if src_region == target_region:
            return MappingResult(True, offset)
        return _map_offset_using_maps(
            offset, self.section_by_region(src_region).input_map, self.section_by_region(target_region).output_map
        )

    def section_by_region(self, region: Region) -> RegionSection:
        """Returns a RegionSection for the GlobalSection, depending on which region is requested."""
        match region:
            case Region.na:
                return self.na_section
            case Region.eu:
                return self.eu_section
            case Region.jp:
                return self.jp_section

    def __str__(self):
        output = self.name
        if self.parent_section:
            output += f" (subsection of {self.parent_section})"
        return output


def _map_offset_using_maps(offset: int, input_map, output_map) -> MappingResult:
    lesser_input_map_offset = 0
    for input_map_offset in input_map:  # REQUIRES DICT TO BE SORTED BY OFFSET TO WORK
        if offset > input_map_offset:
            lesser_input_map_offset = input_map_offset
        elif offset < input_map_offset:
            # This is our greater offset
            greater_input_map_offset = input_map_offset
            break
        else:
            # If our offset falls exactly on a symbol, skip doing any math and just get the exact symbol dst offset.
            return MappingResult(True, output_map[input_map[input_map_offset]])
    nearest_src_symbols_distance = (
        greater_input_map_offset - lesser_input_map_offset
    )  # How far apart are the nearest two symbols?
    # Get dst offsets of nearest symbols
    lesser_symbol = input_map[lesser_input_map_offset]
    if lesser_symbol in output_map:
        lesser_output_map_offset = output_map[lesser_symbol]
    else:
        lesser_output_map_offset = -1
    greater_symbol = input_map[greater_input_map_offset]
    if greater_symbol in output_map:
        greater_output_map_offset = output_map[greater_symbol]
    else:
        greater_output_map_offset = -1
    if lesser_input_map_offset == -1 or greater_input_map_offset == -1:
        return MappingResult(False, None, lesser_input_map_offset, greater_input_map_offset)
    nearest_dst_symbols_distance = (
        greater_output_map_offset - lesser_output_map_offset
    )  # How far apart are the dst equivalents of the nearest two symbols?
    if nearest_src_symbols_distance != nearest_dst_symbols_distance:
        # Offset {hex(src_offset)} is not mappable, distance between nearest symbols ({input_map[lesser_input_map_offset]} and {input_map[greater_input_map_offset]}) differs between src ({hex(nearest_src_symbols_distance)}) and dst ({hex(nearest_dst_symbols_distance)})
        return MappingResult(False, None, lesser_output_map_offset, greater_output_map_offset)
    # Symbols are the same distance apart in dst and src
    return MappingResult(True, offset - lesser_input_map_offset + lesser_output_map_offset)


Arm7 = GlobalSection("arm7", RegionSection(na.arm7), RegionSection(eu.arm7), RegionSection(jp.arm7))
Arm9 = GlobalSection("arm9", RegionSection(na.arm9), RegionSection(eu.arm9), RegionSection(jp.arm9))
Libs = GlobalSection("libs", RegionSection(na.libs), RegionSection(eu.libs), RegionSection(jp.libs), "arm9")
Itcm = GlobalSection("itcm", RegionSection(na.itcm), RegionSection(eu.itcm), RegionSection(jp.itcm), "arm9")
Overlay0 = GlobalSection("overlay0", RegionSection(na.overlay0), RegionSection(eu.overlay0), RegionSection(jp.overlay0))
Overlay1 = GlobalSection("overlay1", RegionSection(na.overlay1), RegionSection(eu.overlay1), RegionSection(jp.overlay1))
Overlay2 = GlobalSection("overlay2", RegionSection(na.overlay2), RegionSection(eu.overlay2), RegionSection(jp.overlay2))
Overlay3 = GlobalSection("overlay3", RegionSection(na.overlay3), RegionSection(eu.overlay3), RegionSection(jp.overlay3))
Overlay4 = GlobalSection("overlay4", RegionSection(na.overlay4), RegionSection(eu.overlay4), RegionSection(jp.overlay4))
Overlay5 = GlobalSection("overlay5", RegionSection(na.overlay5), RegionSection(eu.overlay5), RegionSection(jp.overlay5))
Overlay6 = GlobalSection("overlay6", RegionSection(na.overlay6), RegionSection(eu.overlay6), RegionSection(jp.overlay6))
Overlay7 = GlobalSection("overlay7", RegionSection(na.overlay7), RegionSection(eu.overlay7), RegionSection(jp.overlay7))
Overlay8 = GlobalSection("overlay8", RegionSection(na.overlay8), RegionSection(eu.overlay8), RegionSection(jp.overlay8))
Overlay9 = GlobalSection("overlay9", RegionSection(na.overlay9), RegionSection(eu.overlay9), RegionSection(jp.overlay9))
Overlay10 = GlobalSection(
    "overlay10", RegionSection(na.overlay10), RegionSection(eu.overlay10), RegionSection(jp.overlay10)
)
Overlay11 = GlobalSection(
    "overlay11", RegionSection(na.overlay11), RegionSection(eu.overlay11), RegionSection(jp.overlay11)
)
Overlay12 = GlobalSection(
    "overlay12", RegionSection(na.overlay12), RegionSection(eu.overlay12), RegionSection(jp.overlay12)
)
Overlay13 = GlobalSection(
    "overlay13", RegionSection(na.overlay13), RegionSection(eu.overlay13), RegionSection(jp.overlay13)
)
Overlay14 = GlobalSection(
    "overlay14", RegionSection(na.overlay14), RegionSection(eu.overlay14), RegionSection(jp.overlay14)
)
Overlay15 = GlobalSection(
    "overlay15", RegionSection(na.overlay15), RegionSection(eu.overlay15), RegionSection(jp.overlay15)
)
Overlay16 = GlobalSection(
    "overlay16", RegionSection(na.overlay16), RegionSection(eu.overlay16), RegionSection(jp.overlay16)
)
Overlay17 = GlobalSection(
    "overlay17", RegionSection(na.overlay17), RegionSection(eu.overlay17), RegionSection(jp.overlay17)
)
Overlay18 = GlobalSection(
    "overlay18", RegionSection(na.overlay18), RegionSection(eu.overlay18), RegionSection(jp.overlay18)
)
Overlay19 = GlobalSection(
    "overlay19", RegionSection(na.overlay19), RegionSection(eu.overlay19), RegionSection(jp.overlay19)
)
Overlay20 = GlobalSection(
    "overlay20", RegionSection(na.overlay20), RegionSection(eu.overlay20), RegionSection(jp.overlay20)
)
Overlay21 = GlobalSection(
    "overlay21", RegionSection(na.overlay21), RegionSection(eu.overlay21), RegionSection(jp.overlay21)
)
Overlay22 = GlobalSection(
    "overlay22", RegionSection(na.overlay22), RegionSection(eu.overlay22), RegionSection(jp.overlay22)
)
Overlay23 = GlobalSection(
    "overlay23", RegionSection(na.overlay23), RegionSection(eu.overlay23), RegionSection(jp.overlay23)
)
Overlay24 = GlobalSection(
    "overlay24", RegionSection(na.overlay24), RegionSection(eu.overlay24), RegionSection(jp.overlay24)
)
Overlay25 = GlobalSection(
    "overlay25", RegionSection(na.overlay25), RegionSection(eu.overlay25), RegionSection(jp.overlay25)
)
Overlay26 = GlobalSection(
    "overlay26", RegionSection(na.overlay26), RegionSection(eu.overlay26), RegionSection(jp.overlay26)
)
Overlay27 = GlobalSection(
    "overlay27", RegionSection(na.overlay27), RegionSection(eu.overlay27), RegionSection(jp.overlay27)
)
Overlay28 = GlobalSection(
    "overlay28", RegionSection(na.overlay28), RegionSection(eu.overlay28), RegionSection(jp.overlay28)
)
Overlay29 = GlobalSection(
    "overlay29", RegionSection(na.overlay29), RegionSection(eu.overlay29), RegionSection(jp.overlay29)
)
MoveEffects = GlobalSection(
    "move_effects",
    RegionSection(na.move_effects),
    RegionSection(eu.move_effects),
    RegionSection(jp.move_effects),
    "overlay29",
)
Overlay30 = GlobalSection(
    "overlay30", RegionSection(na.overlay30), RegionSection(eu.overlay30), RegionSection(jp.overlay30)
)
Overlay31 = GlobalSection(
    "overlay31", RegionSection(na.overlay31), RegionSection(eu.overlay31), RegionSection(jp.overlay31)
)
Overlay32 = GlobalSection(
    "overlay32", RegionSection(na.overlay32), RegionSection(eu.overlay32), RegionSection(jp.overlay32)
)
Overlay33 = GlobalSection(
    "overlay33", RegionSection(na.overlay33), RegionSection(eu.overlay33), RegionSection(jp.overlay33)
)
Overlay34 = GlobalSection(
    "overlay34", RegionSection(na.overlay34), RegionSection(eu.overlay34), RegionSection(jp.overlay34)
)
Overlay35 = GlobalSection(
    "overlay35", RegionSection(na.overlay35), RegionSection(eu.overlay35), RegionSection(jp.overlay35)
)
