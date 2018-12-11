from licant.cli import cliexecute as ex

from licant.core import Core, Target, UpdatableTarget, UpdateStatus
from licant.core import core as default_core
from licant.core import routine_decorator as routine

from licant.make import copy, fileset
from licant.cxx_modules import application as cxx_application
from licant.cxx_modules import shared_library as cxx_shared_library

from licant.modules import module, submodule
from licant.util import error

import licant.scripter
from licant.libs import include

__version__ = '1.1.0'


def subtree(tgt):
	return default_core.subtree(tgt)


def execute(path):
    licant.scripter.scriptq.execute(path)


def execute_recursive(*argv, **kwargs):
    licant.scripter.scriptq.execute_recursive(*argv, **kwargs)


def about():
    return "I'm Licant"
