import unittest
import hashlib
import mox

from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, URIRef, BNode, Literal

from models import *
from export import Triplifier

BQ = """
PREFIX deb:<http://idi.fundacionctic.org/steamy/debian.owl#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>

"""

RDF = Namespace(u"http://www.w3.org/1999/02/22-rdf-syntax-ns#")
DEB = Namespace(u"http://idi.fundacionctic.org/steamy/debian.owl#")

ALLTRIPLES = BQ + "SELECT ?x ?y ?z WHERE { ?x ?y ?z . }"

class TriplifierTest(unittest.TestCase):
  def setUp(self):
    self.graph = ConjunctiveGraph()
    self.t = Triplifier(self.graph, "b")
    self.base = "b"
    self.mox = mox.Mox()

  def compareGeneratedTriples(self, expected):
    for triple in self.graph.query(ALLTRIPLES):
      self.assertTrue(triple in expected, "%s is not in" % str(triple))
  
  def testTriplifyArchitecture(self):
    arch = Architecture("testArch")
    uriref = URIRef("b/arch/testArch")
    self.assertEqual(uriref, self.t.triplifyArchitecture(arch))
    self.assertEqual(1, len(self.graph))
    expected = [(uriref, RDF.type, DEB['Architecture'])]
    self.compareGeneratedTriples(expected)

  def testTriplifyVersionNumberSimple(self):
    version = VersionNumber("1.0-1")
    uriref = URIRef("b/version/1.0-1")
    self.assertEqual(uriref, self.t.triplifyVersionNumber(version))
    self.assertEqual(3, len(self.graph))
    expected = [(uriref, RDF.type, DEB['VersionNumber']),\
                (uriref, DEB['upstreamVersion'], Literal("1.0")),\
                (uriref, DEB['debianRevision'], Literal("1"))]
    self.compareGeneratedTriples(expected)

  def testTriplifyConstraintSimple(self):
    constraint = Constraint()
    constraint.package = "pkg"
    constraint.operator = ">>"
    constraint.version = VersionNumber("1.0-1")
    self.t.triplifyVersionNumber =\
        self.mockTriplifyVersionNumber(constraint.version)
    uriref = URIRef("b/constraint/%s" %\
        hashlib.sha1(constraint.package + constraint.operator +\
        str(constraint.version)).hexdigest())
    self.assertEqual(uriref, self.t.triplifyConstraint(constraint))
    self.mox.VerifyAll()
    self.assertEqual(4, len(self.graph))
    expected = [(uriref, RDF.type, DEB['SimplePackageConstraint']),\
                (uriref, DEB['packageName'], Literal("pkg")),\
                (uriref, DEB['constraintOperator'], Literal(">>")),\
                (uriref, DEB['versionNumber'], URIRef("b/version/1.0-1"))]
    self.compareGeneratedTriples(expected)

  def testTriplifyOrConstraint(self):
    orconstraint = OrConstraint()
    constraint1 = Constraint()
    constraint1.package = "pkg1"
    constraint2 = Constraint()
    constraint2.package = "pkg2"
    orconstraint.add(constraint1)
    orconstraint.add(constraint2)
    self.t.triplifyConstraint = self.mockTriplifyConstraint([constraint1, constraint2])
    self.assertEqual(BNode, self.t.triplifyOrConstraint(orconstraint).__class__)
    self.mox.VerifyAll()
    self.assertEqual(3, len(self.graph))

  # Mocks
  def mockTriplifyVersionNumber(self, version):
    classMock = self.mox.CreateMock(Triplifier)
    classMock.triplifyVersionNumber(version)\
                                    .AndReturn(URIRef(version.asURI("b")))
    self.mox.ReplayAll()
    return classMock.triplifyVersionNumber

  def mockTriplifyConstraint(self, constraints):
    classMock = self.mox.CreateMock(Triplifier)
    for constraint in constraints:
      classMock.triplifyConstraint(constraint)\
                                      .InAnyOrder()\
                                      .AndReturn(URIRef(constraint.asURI("b")))
    self.mox.ReplayAll()
    return classMock.triplifyConstraint
