#!/usr/bin/python
# -*- coding: utf8 -*-

from optparse import OptionParser
import unittest
import xmlrunner

from test.unit import modelsTest, parserTest, exportTest

class TestRunner:
  def __init__(self):
    self.out = None

  def config(self):
    parser = OptionParser()
    parser.add_option("-x", "--xml", action="store_true", dest="xml",\
                      default=False, help="switch to XML output")
    parser.add_option("-o", "--output", dest="output",\
                      metavar="FILE", help="dump XML to FILE")

    (self.opts, args) = parser.parse_args()

    if self.opts.output:
      self.out = open(self.opts.output, "w")

    return self

  def run(self):
    suite = unittest.TestLoader().loadTestsFromModule(modelsTest)
    suite.addTests(unittest.TestLoader().loadTestsFromModule(parserTest))
    suite.addTests(unittest.TestLoader().loadTestsFromModule(exportTest))
    if self.opts.xml:
      xmlrunner.XMLTestRunner(self.out).run(suite)
      if self.out:
        self.out.close()
    else:
      unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    TestRunner().config().run()
