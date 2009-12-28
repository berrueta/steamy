import hashlib

from debian_bundle.changelog import Version

class SourcePackage():
  def __init__(self):
    self.package = None
    self.binary = None
    self.version = None
    self.buildDepends = None
    self.buildDependsIndep = None
    self.architecture = None
    self.files = None
    self.directory = None

  def asURI(self, base):
    return "%s/source/%s/%s" % (base, self.package, self.version)

  def asLabel(self):
    return "Source: %s (%s)" % (self.package, self.version)

class BinaryPackageLite():
  def __init__(self, package=None, version=None):
    self.package = package
    self.version = version

  def asURI(self, base):
    return "%s/binary/%s/%s" % (base, self.package, self.version)

  def asLabel(self):
    return "Binary: %s (%s)" % (self.package, self.version)

  def __repr__(self):
    return "%s (%s)" % (self.package, self.version)

class BinaryPackage(BinaryPackageLite):
  def __init__(self):
    self.depends = None
    self.recommends = None
    self.build = None
    self.filename = None

class BinaryPackageBuild():
  def __init__(self, ancestor = None):
    self.architecture = None
    self.installedSize = None
    self.ancestor = ancestor # Cycles are OK in Python! :)

  def asURI(self, base):
    return "%s/binary/%s/%s/%s" % \
            (base, self.ancestor.package, self.ancestor.version, self.architecture)

  def asLabel(self):
    return "BinaryBuild: %s (%s) [%s]" % \
            (self.ancestor.package, self.ancestor.version, self.architecture)

class Architecture():
  INSTANCES = ("all")

  def __init__(self, arch):
    self.name = arch

  def asURI(self, base):
    return "%s/arch/%s" % (base, self.name)

  def asLabel(self):
    return "Architecture: %s" % (self.name)

  def __repr__(self):
    return str(self.name)

  def __eq__(self, other):
    return self.name.__eq__(other.name)

  def hasInstance(self):
    return self.name in self.INSTANCES

class VersionNumber(Version):
  def asURI(self, base):
    return "%s/version/%s" % (base, str(self))

class Constraints():
  def __init__(self):
    self.orconstraints = []

  def add(self, orconstraint):
    self.orconstraints.append(orconstraint)

  def get(self, index):
    return self.orconstraints[index]

  def len(self):
    return len(self.orconstraints)

  def __repr__(self):
    return "Constraints: %s" % str(self.orconstraints)

  def __iter__(self):
    return self.orconstraints.__iter__()

class OrConstraint():
  def __init__(self):
    self.constraints = []

  def add(self, constraint):
    self.constraints.append(constraint)

  def get(self, index):
    return self.constraints[index]

  def __repr__(self):
    return "OrConstraint: %s" % str(self.constraints)

class Constraint():
  def __init__(self):
    self.package = None
    self.operator = None
    self.version = None
    self.exceptin = []
    self.onlyin = []

  def asURI(self, base):
    tail = "%s" % self.package
    if self.operator and self.version:
      tail = tail + "%s%s" % (self.operator, self.version)
    # FIMXE: Add *in
    return "%s/constraint/%s" % (base, hashlib.sha1(tail).hexdigest())

  def asLabel(self):
    label = "Constraint: %s" % self.package
    if self.operator and self.version:
      label = label + " (%s %s)" % (self.operator, self.version)

    for arch in self.exceptin:
      label = label + " !%s" % arch.name

    for arch in self.onlyin:
      label = label + " %s" % arch.name

    return label

  def __repr__(self):
    if self.operator and self.version:
      return "%s (%s %s)" % (self.package, self.operator, self.version)
    else:
      return "%s" % self.package

class File():
  def __init__(self, name, md5sum, size, ancestor = None):
    self.name = name
    self.md5sum = md5sum
    self.size = size
    self.ancestor = ancestor

  def asURI(self, base):
    return "%s/path/%s/%s" % \
          (base, self.ancestor.path, self.name)

  def asLabel(self):
    return "File: %s" % self.name

  def __repr__(self):
    return "%s %s %s" % (self.md5sum, self.size, self.name)

  def __eq__(self, other):
    return self.md5sum.__eq__(other.md5sum)

class Directory():
  def __init__(self, path):
    self.path = path

  def asLabel(self):
    return "Directory: %s" % self.path

  def asURI(self, base):
    return "%s/path/%s" % (base, self.path)

  def __eq__(self, other):
    return self.path.__eq__(other.path)
