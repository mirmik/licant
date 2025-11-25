import os
import subprocess

from licant.cli import cliexecute as ex
from licant.core import Core, Target, UpdatableTarget, default_core, do, get_target, routine
from licant.cxx_make import clang_toolchain, gcc_toolchain, objcopy
from licant.cxx_modules import (
    application as cxx_application,
    library as cxx_library,
    objects as cxx_objects,
    shared_library as cxx_shared_library,
    static_and_shared as cxx_static_and_shared,
    static_library as cxx_static_library,
)
from licant.libs import include
from licant.make import DirectoryTarget, Executor, FileTarget, MakeCore, copy, fileset, makefile, makedir, source
from licant.modules import implementation, module, module_default_implementation, submodule
from licant.modules import module_default_implementation as module_defimpl
from licant.util import error
import licant.scripter

__version__ = "1.20.0"


def directory():
    return licant.scripter.scriptq.curdir()


def execute(path):
    licant.scripter.scriptq.execute(path)


def execute_recursive(*argv, **kwargs):
    licant.scripter.scriptq.execute_recursive(*argv, **kwargs)


def about():
    return "I'm Licant"


class Object(object):
    pass


glbfunc = Object()
attribute_store = Object()


def global_function(var):
    setattr(glbfunc, var.__name__, var)


def import_attribute(name, var):
    setattr(attribute_store, name, var)


def attribute(name):
    return getattr(attribute_store, name)

# also os.system but throw exception on error


def system(cmd, message=None):
    if message is not None:
        print(message)
    else:
        print(cmd)
    status = subprocess.check_call(cmd, shell=True)
    if status != 0:
        raise Exception("system error")


def mtime(path):
    return os.path.getmtime(path)


__all__ = [
    "include",
    "system",
    "error",
    "module_default_implementation",
    "module_defimpl",
    "module",
    "implementation",
    "submodule",
    "cxx_modules",
    "cxx_objects",
    "cxx_library",
    "cxx_application",
    "shared_library",
    "static_library",
    "static_and_shared",
    "makedir",
    "makefile",
    "fileset",
    "copy",
    "source",
    "do",
    "routine",
    "routine_decorator",
    "mtime",
    "UpdatableTarget",
    "Core",
    "core",
    "cxx_static_library",
    "cxx_shared_library",
    "objcopy",
    "get_target",
    "Target",
    "ex",
    "MakeCore",
    "DirectoryTarget",
    "FileTarget",
]
