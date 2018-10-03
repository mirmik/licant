from licant.core import Core, Target, UpdatableTarget, UpdateStatus
from licant.core import core as default_core

from licant.make import copy, fileset

from licant.cli import cliexecute as ex
from licant.cli import routine_decorator as routine

from licant.modules import module, submodule
from licant.util import error

import licant.scripter


def execute(path):
    licant.scripter.scriptq.execute(path)


def execute_recursive(*argv, **kwargs):
    licant.scripter.scriptq.execute_recursive(*argv, **kwargs)


def about():
    return "I'm Licant"
