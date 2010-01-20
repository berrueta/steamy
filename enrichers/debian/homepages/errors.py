# -*- coding: utf-8 -*-
#
# Nacho Barrientos Arias <nacho@debian.org>
#
#

class W3CValidatorError(Exception):
    pass

class W3CValidatorUnableToConnectError(W3CValidatorError):
    def __str__(self):
        return "Unable to connect to W3C markup validation service"

class W3CValidatorUnexpectedValidationResultError(W3CValidatorError):
    def __str__(self):
        return "W3C validation service returned an unexpected result"

class W3CValidatorUnexpectedStatusCodeError(W3CValidatorError):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return "W3C validation service returned an unexpected status code"

class RSSParsingError(Exception):
    pass

class RSSParsingFeedUnavailableError(RSSParsingError):
    def __str__(self):
        return "Feed not available (Either NOT_FOUND or GONE returned)"

class RSSParsingFeedMalformedError(RSSParsingError):
    def __str__(self):
        return "Feed is not well-formed XML"

class RSSParsingUnparseableVersionError(RSSParsingError):
    def __init__(self, format):
        self.format = format

    def __str__(self):
        return "Unparseable feed format '%s'" % self.format

class RDFDiscoveringError(Exception):
    pass

class RDFDiscoveringBrokenLinkError(RDFDiscoveringError):
    def __str__(self):
        return "File is not available"

class RDFDiscoveringMalformedError(RDFDiscoveringError):
    def __str__(self):
        return "Parser error"
