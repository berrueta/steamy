# -*- coding: utf-8 -*-
#
# Nacho Barrientos Arias <nacho@debian.org>
#
# License: MIT

import re

from rdflib import Variable, URIRef

from debian.sparql.miniast import * 
from debian.sparql.visitor import QueryStringVisitor

class SelectQueryHelper():
    def __init__(self):
        self.query = SelectQuery()

    def add_variable(self, varname):
        if not varname in self.query.variables:
            self.query.variables.append(Variable(varname))

    def add_triple(self, triple):
        if not triple in filter(lambda x: isinstance(x, Triple),\
                                self.query.whereclause.stmts):
            self.query.whereclause.stmts.append(triple)

    def push_triple(self, subject, property, object):
        triple = Triple(subject, property, object)
        self.add_triple(triple)

    def add_optional(self, *args):
        self.query.whereclause.stmts.append(Optional(*args))

    def add_filter(self, expr):
        self.query.whereclause.stmts.append(Filter(expr))

    def add_union(self, *args):
        if len(args) < 2:
            raise Exception("I need at least two graphpatterns to build an union")
        union = Union()
        for graphpattern in args:
            union.graphpatterns.append(graphpattern)
        self.query.whereclause.stmts.append(union)

    def add_triple_variables(self, triple):
        self.add_triple(triple)
        for k,v in triple.__dict__.items():
            if isinstance(v, Variable):
                self.add_variable(v)

    def push_triple_variables(self, subject, property, object):
        triple = Triple(subject, property, object)
        self.add_triple_variables(triple)

    def set_from(self, uri):
        self.query.fromgraph = URIRef(uri)

    def set_limit(self, value):
        self.query.modifiers.append(Limit(value))

    def set_offset(self, value):
        self.query.modifiers.append(Offset(value))

    def set_orderby(self, varname):
        self.query.orderby = Orderby(Variable(varname))

    def set_distinct(self):
        self.query.distinct = True

    def __str__(self):
        v = QueryStringVisitor()
        return v.visit(self.query) 

    def add_or_filter_regex(self, dict):
        nodes = []
        for variable,regex in dict.items():
            nodes.append(FunCall("regex", variable, '"%s"' % regex, '"i"'))
        self.add_filter(self._build_fixed_operator_tree("||", nodes))

    def add_filter_notbound(self, var):
        f = FunCall("bound", var)
        unexp = UnaryExpression(f, "!")
        self.add_filter(unexp)

    def add_filter_regex_str_var(self, var, regex):
        f = FunCall("str", var)
        self.add_filter(FunCall("regex", f, '"%s"' % regex))

    def _build_fixed_operator_tree(self, operator, items):
        if len(items) == 1:
            return items.pop()
        else:
            item = items.pop()
            return BinaryExpression(item, operator,\
                       self._build_fixed_operator_tree(operator, items))
