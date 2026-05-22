# Copyright 2026 Chesyon, under the MIT license
# This file aims to provide a basic way of connecting sky-compass with non-Python languages, without depending on any language-specific libraries like Jython or Cython.
# Using any other way to call json_io in io.py is preferred; this should only be used if there's no better option.

from sys import argv as args
from io import json_io

if __name__ == "__main__":
    print(json_io(args[1]))
