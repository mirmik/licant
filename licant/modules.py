from licant.util import red
from licant.scripter import scriptq
import licant.core

import re

special = ["__script__", "__dir__"]


class Module:
    def __init__(self, name, script=None, dir=None, stack=None, **kwargs):
        self.name = name
        self.script = script
        self.stack = stack
        self.opts = kwargs
        self.opts["__script__"] = self.script
        self.opts["__dir__"] = dir


class VariantModule:
    def __init__(self):
        self.impls = {}

    def addimpl(self, impl, mod):
        self.impls[impl] = mod
        mod.impl = impl


class ModuleLibrary:
    def __init__(self):
        self.modules = {}
        self.defimpls = {}

    def register_impl(self, mod, impl):
        if mod.name in self.modules:
            if not isinstance(self.modules[mod.name], VariantModule):
                print("Attempt to register the module {} again".format(red(mod.name)))
                exit(-1)
            else:
                varmod = self.modules[mod.name]
        else:
            varmod = VariantModule()
            self.modules[mod.name] = varmod

        varmod.addimpl(impl, mod)

    def get(self, name, impl=None):
        if name not in self.modules:
            print("The missing module {} was requested".format(red(name)))
            exit(-1)

        m = self.modules[name]
        if impl is None:
            return self.get_default(name)
        else:
            if isinstance(m, Module):
                licant.error("stand by module is deprecated")
            else:
                if impl in m.impls:
                    return m.impls[impl]
                else:
                    if impl == "__none__":
                        m.addimpl(impl="__none__", mod=Module(name))
                        return m.impls[impl]

                    print("Unregistred implementation: {} (module:{})".format(
                        red(impl), red(name)))
                    exit(-1)

    def set_defimpl(self, modname, impl, force=False):
        if modname in self.defimpls and not force:
            licant.error(
                "Default implementation for module {} setted twice : first:{}, second:{}".format(
                    licant.util.yellow(modname),
                    licant.util.yellow(
                        self.defimpls[modname] + ":" + self.get(modname, self.defimpls[modname]).stack[-1]),
                    licant.util.yellow(
                        impl + ":" + self.get(modname, impl).stack[-1]),
                )
            )
        self.defimpls[modname] = impl

    def is_variant(self, name):
        licant.error("deprecated with 'always implementation concept'")
        if name not in self.modules:
            licant.error(
                "Isn't registred as module ({})".format(
                    licant.util.yellow(name))
            )
        return isinstance(self.modules[name], VariantModule)

    def get_default(self, name):
        if name not in self.defimpls:
            if name not in self.modules:
                licant.error(
                    "Unregistred module ({})".format(
                        licant.util.yellow(name)
                    )
                )

            else:
                licant.error(
                    "Doesn`t have default impl of that module ({})".format(
                        licant.util.yellow(name)
                    )
                )

        return self.get(name, self.defimpls[name])


mlibrary = ModuleLibrary()


def module(name, impl=None, default=False, **kwargs):
    if impl is not None:
        implementation(name, impl, default=default, **kwargs)
        return
    implementation(name, "__default__", default=True, **kwargs)


def implementation(name, impl, default=False, **kwargs):
    mlibrary.register_impl(
        Module(
            name,
            script=scriptq.last(),
            dir=scriptq.curdir(),
            stack=list(scriptq.stack),
            **kwargs
        ),
        impl=impl,
    )

    if default:
        module_default_implementation(name, impl)


class submodule:
    def __init__(self, name, impl=None, addopts=None):
        if isinstance(name, tuple):
            self.name = name[0]
            self.impl = name[1]
            self.addopts = addopts
        elif isinstance(name, submodule):
            self.name = name.name
            self.impl = name.impl
            self.addopts = addopts
        else:
            self.name = name
            self.impl = impl
            self.addopts = addopts

    def __repr__(self):
        return "subm(" + self.name + ")"


def module_default_implementation(mod, impl):
    mlibrary.set_defimpl(mod, impl, force=True)


def print_modules_list(target, *args):
    if len(mlibrary.modules) == 0:
        print("modules doesn't founded")
        return

    mkeys = sorted(mlibrary.modules.keys())

    if len(args) > 0:
        mkeys = [m for m in mkeys if re.search(args[0], m)]

    for k in mkeys:
        v = mlibrary.modules[k]
        if isinstance(v, VariantModule):
            print("{}: {}".format(k, list(v.impls.keys())))


def print_module(target, *args):
    if len(args) == 0:
        print("Usage: EXECUTABLE m print NAME\nUsage: EXECUTABLE m print NAME IMPL\n")
        return

    if len(args) == 1:
        module = mlibrary.get_default(args[0])
    else:
        module = mlibrary.get(args[0], args[1])

    print(module.__dict__)


modules_target = licant.core.Target(
    tgt="m",
    deps=[],
    list=print_modules_list,
    print=print_module,
    actions={"list", "print"},
    __help__="Info about modules",
)

licant.core.core.add(modules_target)
