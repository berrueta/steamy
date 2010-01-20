#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Nacho Barrientos Arias <nacho@debian.org>
#
# License: MIT

import logging
import httplib
import urllib
import re

from sgmllib import SGMLParser
from datetime import datetime

from rdflib.Graph import ConjunctiveGraph
from rdflib import URIRef, Literal, BNode
from SPARQLWrapper import SPARQLWrapper2
from SPARQLWrapper.sparqlexceptions import EndPointNotFound

from models import AlternateLink, MetaLink
from errors import W3CValidatorUnableToConnectError 
from errors import W3CValidatorUnexpectedValidationResultError
from errors import W3CValidatorUnexpectedStatusCodeError
from namespaces import *

def homepages(endpoint, graph):
    endpoint = SPARQLWrapper2(endpoint)
    q = """
        PREFIX deb: <http://idi.fundacionctic.org/steamy/debian.owl#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        SELECT DISTINCT ?homepage
        %s
        WHERE { 
          ?source a deb:Source ;
                  foaf:page ?homepage .
        }
    """ % ("FROM <%s>" % graph if graph is not None else "")
    endpoint.setQuery(q)
    try:
        results = endpoint.query()
    except EndPointNotFound, e:
        logging.error("Wrong or inactive endpoint, aborting.")
        return

    for result in results["homepage"]:
        yield re.sub("<|>", "", result["homepage"].value).strip()


def w3c_validator(uri):
    conn = httplib.HTTPConnection("validator.w3.org")
    try:
        conn.request("GET", "/check?uri=%s" % urllib.quote(uri, ""))
    except: # Socket.error
        raise W3CValidatorUnableToConnectError()

    response = conn.getresponse()

    if response.status == httplib.OK:
        if response.getheader("X-W3C-Validator-Status") == "Valid":
            return True
        elif response.getheader("X-W3C-Validator-Status") == "Invalid":
            return False
        else:
            raise W3CValidatorUnexpectedValidationResultError()
    else:
       raise W3CValidatorUnexpectedStatusCodeError(response.status) 


class LinkRetrieval(SGMLParser):
    def reset(self):
        SGMLParser.reset(self)
        self.results = []

    def start_link(self, attrs):
        rels = [value.lower() for key, value in attrs if key=='rel']
        types = [value.lower() for key, value in attrs if key=='type']
        hrefs = [value for key, value in attrs if key=='href']
        # SGMLParser does not ignore newlines and could lead to broken URIs
        hrefs = map(lambda x: re.sub("\s", "", x), hrefs)
        if 'alternate' in rels:
            self.results.append(AlternateLink(types, hrefs))
            logging.debug("Appended alternate: types=%s hrefs=%s" % \
                         (types, hrefs))
        if 'meta' in rels:
            self.results.append(MetaLink(types, hrefs))
            logging.debug("Appended meta: types=%s hrefs=%s" % \
                         (types, hrefs))

    def get_rss_hrefs(self):
        for x in self.results: 
            if x.is_rss():
                for href in x.hrefs:
                    yield href

    def get_rdf_meta_hrefs(self):
        for x in self.results:
            if x.is_meta_rdf(): # FIXME: What if N3?
                for href in x.hrefs:
                    yield href


class TripleProcessor():
    def __init__(self, graphpool):
        self.pool = graphpool

    def request_serialization(self):
        if self.pool.count_triples() > 0:
            logging.info("\nSerializing %s triples contained in %s graphs..." % \
                (self.pool.count_triples(), len(self.pool)))
            
            self.pool.serialize()

    def push_alternate(self, homepage, feed):
        self.pool.add_triple((URIRef(homepage), XHV.alternate, URIRef(feed)))
        self.pool.add_triple((URIRef(feed), RDFS.type, FOAF.Document))

    def push_meta(self, homepage, href):
        self.pool.add_triple((URIRef(homepage), XHV.meta, URIRef(href)))
        self.pool.add_triple((URIRef(href), RDFS.type, FOAF.Document))

    def push_graph(self, graph):
        self.pool.merge_graph(graph)

    def push_validation_success(self, uri):
        assertion = self._push_generic_validation(uri)
        result = BNode()
        self.pool.add_triple((result, EARL.outcome, EARL.passed))
        self.pool.add_triple((assertion, EARL.result, result))

    def push_validation_failure(self, uri):
        assertion = self._push_generic_validation(uri)
        result = BNode()
        self.pool.add_triple((result, RDF.type, EARL.TestResult))
        self.pool.add_triple((result, EARL.outcome, EARL.failed))
        self.pool.add_triple((assertion, EARL.result, result))

    def _push_generic_validation(self, uri):
        assertion = BNode()
        subject = URIRef(uri)
        self.pool.add_triple((assertion, RDF.type, EARL.Assertion))
        self.pool.add_triple((subject, RDF.type, EARL.TestSubject))
        self.pool.add_triple((assertion, EARL.testCase, DEB.W3CValidationTest))
        self.pool.add_triple((assertion, EARL.subject, subject))
        self.pool.add_triple((assertion, EARL.mode, EARL.automatic))
        self.pool.add_triple((assertion, DC.date, Literal(datetime.now())))
        return assertion
