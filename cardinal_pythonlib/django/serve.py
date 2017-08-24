#!/usr/bin/env python
# cardinal_pythonlib/django/serve.py

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


import os
from typing import Iterable, Union
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.http.response import HttpResponseBase
from django.utils.encoding import smart_str

from cardinal_pythonlib.pdf import (
    get_concatenated_pdf_from_disk,
    get_concatenated_pdf_in_memory,
    get_pdf_from_html,
    PdfPlan,
)


# =============================================================================
# File serving
# =============================================================================

# I thought this function was superseded by django-filetransfers:
# http://nemesisdesign.net/blog/coding/django-private-file-upload-and-serving/
# https://www.allbuttonspressed.com/projects/django-filetransfers
# ... but it turns out that filetransfers.api.serve_file uses a file object,
# not a filename. Not impossible, but never mind.

def add_http_headers_for_attachment(response: HttpResponse,
                                    offered_filename: str = None,
                                    content_type: str = None,
                                    as_attachment: bool = False,
                                    as_inline: bool = False,
                                    content_length: int = None) -> None:
    """
    Add HTTP headers to a Django response class object.

    as_attachment: if True, browsers will generally save to disk.
        If False, they may display it inline.
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec19.html
    as_inline: attempt to force inline (only if not as_attachment)
    """
    if offered_filename is None:
        offered_filename = ''
    if content_type is None:
        content_type = 'application/force-download'
    response['Content-Type'] = content_type
    if as_attachment:
        prefix = 'attachment; '
    elif as_inline:
        prefix = 'inline; '
    else:
        prefix = ''
    fname = 'filename=%s' % smart_str(offered_filename)
    response['Content-Disposition'] = prefix + fname
    if content_length is not None:
        response['Content-Length'] = content_length


def serve_file(path_to_file: str,
               offered_filename: str = None,
               content_type: str = None,
               as_attachment: bool = False,
               as_inline: bool = False) -> HttpResponseBase:
    """
    Serve up a file from disk.
    Two methods:
    (a) serve directly
    (b) serve by asking the web server to do so via the X-SendFile directive.
    """
    # http://stackoverflow.com/questions/1156246/having-django-serve-downloadable-files  # noqa
    # https://docs.djangoproject.com/en/dev/ref/request-response/#telling-the-browser-to-treat-the-response-as-a-file-attachment  # noqa
    # https://djangosnippets.org/snippets/365/
    if offered_filename is None:
        offered_filename = os.path.basename(path_to_file) or ''
    if settings.XSENDFILE:
        response = HttpResponse()
        response['X-Sendfile'] = smart_str(path_to_file)
        content_length = os.path.getsize(path_to_file)
    else:
        response = FileResponse(open(path_to_file, mode='rb'))
        content_length = None
    add_http_headers_for_attachment(response,
                                    offered_filename=offered_filename,
                                    content_type=content_type,
                                    as_attachment=as_attachment,
                                    as_inline=as_inline,
                                    content_length=content_length)
    return response
    # Note for debugging: Chrome may request a file more than once (e.g. with a
    # GET request that's then marked 'canceled' in the Network tab of the
    # developer console); this is normal:
    #   http://stackoverflow.com/questions/4460661/what-to-do-with-chrome-sending-extra-requests  # noqa


def serve_buffer(data: bytes,
                 offered_filename: str = None,
                 content_type: str = None,
                 as_attachment: bool = True,
                 as_inline: bool = False) -> HttpResponse:
    """
    Serve up binary data from a buffer.
    Options as for serve_file().
    """
    response = HttpResponse(data)
    add_http_headers_for_attachment(response,
                                    offered_filename=offered_filename,
                                    content_type=content_type,
                                    as_attachment=as_attachment,
                                    as_inline=as_inline,
                                    content_length=len(data))
    return response


# =============================================================================
# Simpler versions
# =============================================================================

def add_download_filename(response: HttpResponse, filename: str) -> None:
    # https://docs.djangoproject.com/en/1.9/howto/outputting-csv/
    add_http_headers_for_attachment(response)
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        filename)


def file_response(data: Union[bytes, str],  # HttpResponse encodes str if req'd
                  content_type: str,
                  filename: str) -> HttpResponse:
    response = HttpResponse(data, content_type=content_type)
    add_download_filename(response, filename)
    return response


# =============================================================================
# PDF serving
# =============================================================================

def serve_concatenated_pdf_from_disk(
        filenames: Iterable[str],
        offered_filename: str = "crate_download.pdf",
        **kwargs) -> HttpResponse:
    """
    Concatenates PDFs from disk and serves them.
    """
    pdf = get_concatenated_pdf_from_disk(filenames, **kwargs)
    return serve_buffer(pdf,
                        offered_filename=offered_filename,
                        content_type="application/pdf",
                        as_attachment=False,
                        as_inline=True)


def serve_pdf_from_html(html: str,
                        offered_filename: str = "test.pdf",
                        **kwargs) -> HttpResponse:
    """Same args as pdf_from_html."""
    pdf = get_pdf_from_html(html, **kwargs)
    return serve_buffer(pdf,
                        offered_filename=offered_filename,
                        content_type="application/pdf",
                        as_attachment=False,
                        as_inline=True)


def serve_html_or_pdf(html: str, viewtype: str) -> HttpResponse:
    """
    For development.

    HTML = contents
    viewtype = "pdf" or "html"
    """
    if viewtype == "pdf":
        return serve_pdf_from_html(
            html,
            header_html=settings.PDF_LETTER_HEADER_HTML,
            footer_html=settings.PDF_LETTER_FOOTER_HTML)
    elif viewtype == "html":
        return HttpResponse(html)
    else:
        raise ValueError("Bad viewtype")


def serve_concatenated_pdf_from_memory(
        pdf_plans: Iterable[PdfPlan],
        start_recto: bool = True,
        offered_filename: str = "crate_download.pdf") -> HttpResponse:
    """
    Concatenates PDFs into memory and serves it.
    """
    pdf = get_concatenated_pdf_in_memory(pdf_plans, start_recto=start_recto)
    return serve_buffer(pdf,
                        offered_filename=offered_filename,
                        content_type="application/pdf",
                        as_attachment=False,
                        as_inline=True)