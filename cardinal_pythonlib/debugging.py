#!/usr/bin/env python
# cardinal_pythonlib/debugging.py

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

Offers the getch() and kbhit() functions.

"""

import ctypes
import inspect
import logging
import pdb
import sys
import traceback
from types import FrameType
from typing import Callable, Optional

log = logging.getLogger(__name__)  # don't use BraceStyleAdapter; {} used
log.addHandler(logging.NullHandler())


# =============================================================================
# Debugging
# =============================================================================

def pdb_run(main_func: Callable[[], None]) -> None:
    # noinspection PyBroadException
    try:
        main_func()
    except:
        type_, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


def cause_segfault() -> None:
    """
    This function will induce a segmentation fault and CRASH the application.
    Method as per https://docs.python.org/3/library/faulthandler.html
    """
    ctypes.string_at(0)  # will crash!


# =============================================================================
# Name of calling class/function, for status messages
# =============================================================================

def get_class_from_frame(fr: FrameType) -> Optional[str]:
    # http://stackoverflow.com/questions/2203424/python-how-to-retrieve-class-information-from-a-frame-object  # noqa
    args, _, _, value_dict = inspect.getargvalues(fr)
    # we check the first parameter for the frame function is named 'self'
    if len(args) and args[0] == 'self':
        # in that case, 'self' will be referenced in value_dict
        instance = value_dict.get('self', None)
        if instance:
            # return its class
            cls = getattr(instance, '__class__', None)
            if cls:
                return cls.__name__
            return None
    # return None otherwise
    return None


# noinspection PyProtectedMember
def get_caller_name(back: int = 0) -> str:
    """
    Return details about the CALLER OF THE CALLER (plus n calls further back)
    of this function.
    """
    # http://stackoverflow.com/questions/5067604/determine-function-name-from-within-that-function-without-using-traceback  # noqa
    try:
        frame = sys._getframe(back + 2)
    except ValueError:
        # Stack isn't deep enough.
        return '?'
    function_name = frame.f_code.co_name
    class_name = get_class_from_frame(frame)
    if class_name:
        return "{}.{}".format(class_name, function_name)
    return function_name


# =============================================================================
# Show the structore of an object in detail
# =============================================================================

def debug_object(obj, log_level: int = logging.DEBUG) -> None:
    msgs = ["For {o!r}:".format(o=obj)]
    for attrname in dir(obj):
        attribute = getattr(obj, attrname)
        msgs.append("- {an!r}: {at!r}, of type {t!r}".format(
            an=attrname, at=attribute, t=type(attribute)))
    log.log(log_level, "\n".join(msgs))