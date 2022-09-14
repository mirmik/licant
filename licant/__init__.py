import subprocess
import os
from licant.cli import cliexecute as ex
from licant.core import Core, Target, UpdatableTarget, UpdateStatus
from licant.core import core as default_core
from licant.core import routine_decorator as routine
from licant.core import do
from licant.core import get_target
from licant.make import copy, fileset, Executor, makefile, source, makedir, MakeCore, DirectoryTarget, FileTarget
from licant.cxx_make import objcopy
from licant.cxx_modules import application as cxx_application
from licant.cxx_modules import shared_library as cxx_shared_library
from licant.cxx_modules import static_library as cxx_static_library
from licant.cxx_modules import static_and_shared as cxx_static_and_shared
from licant.cxx_modules import library as cxx_library
from licant.cxx_modules import objects as cxx_objects
from licant.modules import module, implementation, submodule
from licant.modules import module_default_implementation as module_defimpl
from licant.modules import module_default_implementation
from licant.util import error
from licant.cxx_make import gcc_toolchain, clang_toolchain, host_toolchain
import licant.scripter
from licant.libs import include

__version__ = "1.12.2"


def directory():
    return licant.scripter.scriptq.curdir()


def subtree(tgt):
    return default_core.subtree(tgt)


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
    "UpdateStatus",
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
