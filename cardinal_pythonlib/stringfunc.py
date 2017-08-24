#!/usr/bin/env python
# cardinal_pythonlib/sqlalchemy/subproc.py

"""
===============================================================================
    Copyright (C) 2009-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of cardinal_pythonlib.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
===============================================================================
"""


from typing import Any, Dict, Iterable, List
import unicodedata

import regex


# =============================================================================
# Replacement
# =============================================================================

def multiple_replace(text: str, rep: Dict[str, str]) -> str:
    """Returns text in which the keys of rep (a dict) have been replaced by
    their values."""
    # http://stackoverflow.com/questions/6116978/python-replace-multiple-strings  # noqa
    rep = dict((regex.escape(k), v) for k, v in rep.items())
    pattern = regex.compile("|".join(rep.keys()))
    return pattern.sub(lambda m: rep[regex.escape(m.group(0))], text)


def replace_in_list(stringlist: Iterable[str],
                    replacedict: Dict[str, str]) -> List[str]:
    newlist = []
    for fromstring in stringlist:
        newlist.append(multiple_replace(fromstring, replacedict))
    return newlist


# =============================================================================
# Mangling to ASCII
# =============================================================================

def mangle_unicode_to_ascii(s: Any) -> str:
    """Mangle unicode to ASCII, losing accents etc. in the process."""
    # http://stackoverflow.com/questions/1207457
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    return (
        unicodedata.normalize('NFKD', s)
                   .encode('ascii', 'ignore')  # gets rid of accents
                   .decode('ascii')  # back to a string
    )


# =============================================================================
# Making strings and string lists
# =============================================================================

def strnum(prefix: str, num: int, suffix: str = "") -> str:
    return "{}{}{}".format(prefix, num, suffix)


def strnumlist(prefix: str, numbers: List[int], suffix: str = "") -> List[str]:
    return ["{}{}{}".format(prefix, num, suffix) for num in numbers]


def strseq(prefix: str, first: int, last: int, suffix: str = "") -> List[str]:
    return [strnum(prefix, n, suffix) for n in range(first, last + 1)]