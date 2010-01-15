import logging
import re

from SPARQLWrapper import SPARQLWrapper, JSON
from SPARQLWrapper.sparqlexceptions import QueryBadFormed

from rdflib import Variable
from rdflib import Namespace, URIRef, Literal, Variable
from rdflib.sparql.bison import Parse as RdflibParse

from debian.config import *
from debian.sparql.helpers import SelectQueryHelper
from debian.sparql.miniast import Triple
from debian.errors import SPARQLQueryProcessorError

RDFS = Namespace(u"http://www.w3.org/2000/01/rdf-schema#")
FOAF = Namespace(u"http://xmlns.com/foaf/0.1/")
RDF = Namespace(u"http://www.w3.org/1999/02/22-rdf-syntax-ns#")
DEB = Namespace(u"http://idi.fundacionctic.org/steamy/debian.owl#")
NFO = Namespace(u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#")
TAG = Namespace(u"http://www.holygoat.co.uk/owl/redwood/0.1/tags/")
DOAP = Namespace(u"http://usefulinc.com/ns/doap#")

class Result():
    def __init__(self):
        self.maintname = None
        self.homepage = None
        self.distribution = None
        self.distributionurilink = None
        self.sectionname = None
        self.sectionurilink = None
        self.area = None
        self.priority = None


class SPARQLQueryProcessor():
    def _init_endpoint(self):
        self.endpoint = SPARQLWrapper(SPARQL_ENDPOINT)
        self.endpoint.setReturnFormat(JSON)

    def _query_endpoint(self, query):
        self.endpoint.setQuery(query)
        return self.endpoint.query().convert()

    def format_source_results(self):
        resultlist = []
        for result in self.results['results']['bindings']:
            obj = Result()
            obj.sourcename = result['sourcename']['value']
            obj.sourceurilink = result['source']['value'].replace(RES_BASEURI, PUBBY_BASEURI)
            obj.usourceurilink = result['unversionedsource']['value'].replace(RES_BASEURI, PUBBY_BASEURI)
            obj.fullversion = result['fullversion']['value']
            if 'maintname' in result: obj.maintname = result['maintname']['value']
            obj.maintmail = result['maintmail']['value']
            obj.mainturilink = result['maint']['value'].replace(RES_BASEURI, PUBBY_BASEURI)
            if 'homepage' in result: obj.homepage = result['homepage']['value'] 
            if 'distribution' in result: 
                obj.distribution = result['distribution']['value']
                obj.distributionurilink = result['distribution']['value'].\
                    replace(RES_BASEURI, PUBBY_BASEURI)
            if 'area' in result: obj.area = result['area']['value']
            if 'priority' in result: obj.priority = result['priority']['value']
            if 'section' in result and 'sectionname' in result:
                obj.sectionname = result['sectionname']['value']
                obj.sectionurilink = result['section']['value'].replace(RES_BASEURI, PUBBY_BASEURI)
            
            resultlist.append(obj)

        return resultlist

    def format_sparql_results(self):
        resultlist = []
        variables = self.results['head']['vars']

        for result in self.results['results']['bindings']:
            values = []
            for var in variables:
                if var in result:
                    values.append(result[var]['value'])
                else:
                    values.append(None)

            resultlist.append(values)

        return (variables, resultlist)

    def _clean_query(self, query):
        return re.sub("LIMIT.*|OFFSET.*", "", query) + "LIMIT " + str(RESULTS_PER_PAGE)

    def execute_sanitized_query(self, query):
        self._init_endpoint()
        print query # FIXME
        self.results = self._query_endpoint(query)

    def execute_query(self, query):
        query = self._clean_query(query)
        RdflibParse(query)
        self.execute_sanitized_query(query)

class SPARQLQueryBuilder():
    def __init__(self, params):
        self.params = params
        self.helper = SelectQueryHelper()
        self.binary_search = False
        self.source_search = False

    def create_query(self):
        self._consume_searchtype()
        self._add_base_elements()
        self._add_from()
        self._consume_distribution()
        self._consume_area()
        self._consume_sort()
        self._consume_homepage()
        self._consume_maintainer()
        self._consume_version()
        self._consume_priority()
        self._consume_comaintainer()
        self._consume_vcs()
        self._consume_section()
        self._consume_filter()
        self.helper.set_limit(RESULTS_PER_PAGE)
        return self.helper.__str__()

    def _add_base_elements(self):
        self.helper.push_triple_variables(\
            Variable("source"), RDF.type, DEB.Source)
        self.helper.push_triple_variables(\
            Variable("unversionedsource"), DEB.version, Variable("source"))
        self.helper.push_triple(\
            Variable("source"), DEB.maintainer, Variable("maint"))
        self.helper.add_variable("maintname")
        self.helper.add_optional(\
            Triple(Variable("maint"), FOAF.name, Variable("maintname")))
        self.helper.push_triple_variables(\
            Variable("maint"), FOAF.mbox, Variable("maintmail"))
        self.helper.push_triple_variables(\
            Variable("source"), DEB.versionNumber, Variable("version"))
        self.helper.push_triple_variables(\
            Variable("version"), DEB.fullVersion, Variable("fullversion"))
        self.helper.push_triple_variables(\
            Variable("source"), DEB.packageName, Variable("sourcename"))
 
        if self.params['searchtype'] in ('BINARY', 'BINARYDESC'):
            self.helper.push_triple_variables(\
                Variable("binary"), RDF.type, DEB.Binary)
            self.helper.push_triple_variables(\
                Variable("source"), DEB.binary, Variable("binary"))
            self.helper.push_triple_variables(\
                Variable("binary"), DEB.packageName, Variable("binaryname"))

    def _consume_filter(self):
        filter = self.params['filter']
        if filter:
            if self.binary_search:
                if self.params['searchtype'] == 'BINARYEXT':
                    self.helper.push_triple(\
                        Variable("binary"), DEB.extendedDescription, Variable("desc"))
                    restrictions = {Variable("desc"): filter, Variable("binaryname"): filter}
                    self.helper.add_or_filter_regex(restrictions)
                else:   
                    self.helper.add_or_filter_regex({Variable("binaryname"): filter})
            elif self.source_search:
                self.helper.add_or_filter_regex({Variable("sourcename"): filter})

    def _consume_distribution(self):
        distribution = self.params['distribution']
        if distribution == 'ANY':
            self.helper.push_triple_variables(Variable("source"),
                DEB.distribution, Variable("distribution"))
        else:
            self.helper.push_triple(Variable("source"),
                DEB.distribution, URIRef(distribution))

    def _consume_area(self):
        area = self.params['area']
        if area == 'ANY':
            self.helper.push_triple_variables(Variable("source"),
                DEB.area, Variable("area"))
        else:
            self.helper.push_triple(Variable("source"),
                DEB.area, URIRef(area))

    def _consume_searchtype(self):
        type = self.params['searchtype']
        if type in ('BINARY', 'BINARYEXT'):
            self.binary_search = True 
        elif type in ('SOURCE'):
            self.source_search = True

    def _consume_sort(self):
        sort = self.params['sort']
        if sort == 'MAINTNAME':
            self.helper.set_orderby("maintname")
        elif sort == 'MAINTMAIL':
            self.helper.set_orderby("maintmail")
        else:
            if self.binary_search:
                self.helper.set_orderby("binaryname")
            else:
                self.helper.set_orderby("sourcename")

    def _consume_homepage(self):
       if self.params['homepage']:
           self.helper.add_variable("homepage")
           triple = Triple(\
                Variable("source"), FOAF.page, Variable("homepage"))
           self.helper.add_optional(triple)

    def _consume_maintainer(self):
        option = self.params['maintainer']
        if option == 'TEAM':
            self.helper.push_triple(Variable("maint"), RDF.type, FOAF.Group)
        elif option == 'DEBIAN':
            self.helper.add_or_filter_regex({Variable("maintmail"): "@debian.org$"}, False)
        elif option == 'QA':
            uriref = URIRef(RES_BASEURI + "/team/packages%40qa.debian.org")
            self.helper.push_triple(Variable("source"), DEB.maintainer, uriref) 

    def _consume_version(self):
        options = self.params['version']
        if 'NATIVE' in options or 'NMU' in options:
            triple = Triple(\
                Variable("version"), DEB.debianRevision, Variable("debianRevision"))
            self.helper.add_optional(triple)
        if 'NATIVE' in options:
            self.helper.add_filter_notbound(Variable("debianRevision"))
        if 'NMU' in options:
            self.helper.push_triple(\
                Variable("version"), DEB.upstreamVersion, Variable("upstreamVersion"))
            restrictions = {Variable("debianRevision"): ".*\\\..*",\
                            Variable("upstreamVersion"): ".*\\\+nmu.*"}
            self.helper.add_or_filter_regex(restrictions, False)
        if 'EPOCH' in options:
            self.helper.push_triple(Variable("version"), DEB.epoch, Variable("epoch"))

    def _consume_priority(self):
        option = self.params['priority']
        if option == 'ANY':
            self.helper.add_variable("priority")
            triple = Triple(\
                Variable("source"), DEB.priority, Variable("priority"))
            self.helper.add_optional(triple)
        else:
            self.helper.push_triple(\
                Variable("source"), DEB.priority, URIRef(option))

    def _consume_section(self):
        keyword = self.params['section']
        if keyword:
            self.helper.push_triple(\
                Variable("source"), DEB.section, Variable("section"))
            self.helper.push_triple_variables(\
                 Variable("section"), DEB.sectionName, Variable("sectionname"))
            self.helper.add_or_filter_regex({Variable("sectionname"): keyword})
        else:
            self.helper.add_variable("section")
            self.helper.add_variable("sectionname")
            triple1 = Triple(\
                 Variable("source"), DEB.section, Variable("section"))
            triple2 = Triple(\
                 Variable("section"), DEB.sectionName, Variable("sectionname"))
            self.helper.add_optional(triple1, triple2)

    def _consume_comaintainer(self):
        option = self.params['comaintainer']
        if option == 'WITH':
            self.helper.push_triple(\
                Variable("source"), DEB.uploader, Variable("uploader"))
        elif option == 'WITHOUT':
            triple = Triple(\
                Variable("source"), DEB.uploader, Variable("uploader"))
            self.helper.add_optional(triple)
            self.helper.add_filter_notbound(Variable("uploader"))

    def _consume_vcs(self):
        options = self.params['vcs']
        if options:
            self.helper.push_triple(\
                Variable("source"), DEB.repository, Variable("repobnode"))
            graphpatterns = []
            if 'SVN' in options:
                graphpatterns.append(\
                    [Triple(Variable("repobnode"), RDF.type, DOAP.SVNRepository)])
            if 'GIT' in options:
                graphpatterns.append(\
                    [Triple(Variable("repobnode"), RDF.type, DOAP.GitRepository)])
            if 'CVS' in options:
                graphpatterns.append(\
                    [Triple(Variable("repobnode"), RDF.type, DOAP.CVSRepository)])
            if 'HG' in options:
                graphpatterns.append(\
                    [Triple(Variable("repobnode"), RDF.type, DOAP.HgRepository)])
        
            if len(graphpatterns) == 1:
                self.helper.add_triple(graphpatterns[0][0])
            else:
                self.helper.add_union(*graphpatterns)

    def _add_from(self):
        if FROM_GRAPH is not None:
            self.helper.set_from(FROM_GRAPH)
