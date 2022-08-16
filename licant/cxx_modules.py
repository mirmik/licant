# coding: utf-8

from cmath import inf
from licant.modules import mlibrary
from licant.cxx_make import host_toolchain
from licant.util import red, yellow, cxx_read_depends

import os
import licant.util as gu
import licant.make

import glob
import queue


class solver:
    def __init__(self, type, merge, include, default):
        self.type = type
        self.merge = merge
        self.include = include
        self.default = default


def base(base, local, solver, tbase, tlocal):
    return base


def local(base, local, solver, tbase, tlocal):
    if local is None:
        return solver.default
    return local


def concat(base, local, solver, tbase, tlocal):
    if local is None:
        local = []
    if base is None:
        base = []
    return base + local


def strconcat(base, local, solver, tbase, tlocal):
    if local is None:
        return base
    return base + " " + local


def concat_add_srcdir(base, local, solver, tbase, tlocal):
    if local is None:
        local = []
    else:
        if "srcdir" in tlocal.opts:
            srcdir = tlocal.opts["srcdir"]
        else:
            srcdir = ""

        local = list(
            map(
                lambda p: os.path.join(
                    tlocal.opts["__dir__"], srcdir, os.path.expanduser(p)
                ),
                local,
            )
        )
    # print(base + local)
    return base + local


def local_add_srcdir(base, local, solver, tbase, tlocal):
    if "srcdir" in tlocal.opts:
        srcdir = tlocal.opts["srcdir"]
    else:
        srcdir = ""
    if isinstance(local, type("str")):
        local = [local]
    if local is None:
        return []
    return list(
        map(
            lambda p: os.path.join(
                tlocal.opts["__dir__"], srcdir, os.path.expanduser(p)
            ),
            local,
        )
    )


def concat_add_locdir(base, local, solver, tbase, tlocal):
    if local is None:
        return base

    if isinstance(local, type("str")):
        local = [local]
    local = list(
        map(
            lambda p: os.path.join(
                tlocal.opts["__dir__"], os.path.expanduser(p)), local
        )
    )
    return base + local


def concat_add_locdir_second(base, local, solver, tbase, tlocal):
    """ Добавить локальный путь ко всем вторым элементам локального массива.
    Для поддержки локальных заголовков."""
    if local is None:
        return base
    local = [(pl[0], os.path.join(tlocal.opts["__dir__"], pl[1]))
             for pl in local]
    return base + local


def local_if_exist(base, local, solver, tbase, tlocal):
    return base if local is None else local


def concat_to_submodule(base, local, solver, tbase, tlocal):
    if local is None:
        local = []
    if base is None:
        base = []
    lm = [licant.modules.submodule(l) for l in local]
    return base + lm


cxx_module_field_list = {
    #                                       # merge                     #include                    #default
    "srcdir": solver("str", local, base, "."),
    "depends": solver("list", local, base, []),
    "objects": solver("list", local_add_srcdir, concat_add_srcdir, []),
    "sources": solver("list", local_add_srcdir, concat_add_srcdir, []),
    "qt_moc": solver("list", local_add_srcdir, concat_add_srcdir, []),
    "qt_ui": solver("list", local_add_srcdir, concat_add_srcdir, []),
    "libs": solver("list", concat, concat, []),
    "libdirs": solver("list", concat, concat, []),
    "target": solver("str", local_if_exist, base, "target"),
    "include_paths": solver("list", concat_add_locdir, concat_add_locdir, []),
    "cxxstd": solver("str", local_if_exist, local_if_exist, "c++17"),
    "ccstd": solver("str", local_if_exist, local_if_exist, "c11"),
    "cxx_flags": solver("str", strconcat, strconcat, ""),
    "cc_flags": solver("str", strconcat, strconcat, ""),
    "ld_flags": solver("str", strconcat, strconcat, ""),
    "modules": solver("list", local, concat, []),
    "type": solver("str", local, base, "objects"),
    "builddir": solver("str", local_if_exist, base, "build"),
    "toolchain": solver("toolchain", local_if_exist, base, host_toolchain),
    "optimize": solver("str", local_if_exist, base, ""),
    "include_modules": solver("list", concat_to_submodule, base, []),
    "defines": solver("list", concat, concat, []),
    "ldscripts": solver("list", concat_add_locdir, concat_add_locdir, []),
    "local_headers": solver(
        "list", concat_add_locdir_second, concat_add_locdir_second, []
    ),
    "mdepends": solver("list", local, base, []),
    "debug": solver("str", local_if_exist, base, "-g"),
}


class CXXModuleOptions:
    def __getitem__(self, key):
        return self.opts[key]

    def check(self):
        for k, v in self.opts.items():
            if k not in licant.modules.special:
                if k not in self.table:
                    print("Unresolved option: {}".format(red(k)))
                    print("cxx_module_field_list:", cxx_module_field_list)
                    exit(-1)

                if v.__class__.__name__ != self.table[k].type:
                    print(
                        "Option should be object of {}: {}".format(
                            yellow(self.table[k].type), red(k)
                        )
                    )
                    exit(-1)

    def set_default_if_empty(self, table=cxx_module_field_list):
        for k in table:
            if k not in self.opts:
                self.opts[k] = table[k].default

    def merge(self, other, fnc):
        resopts = {}
        for k, v in self.opts.items():

            base = self.opts[k]
            if k in other.opts:
                local = other.opts[k]
            else:
                local = None

            func = getattr(self.table[k], fnc)
            resopts[k] = func(base, local, self.table[k], self, other)

        return CXXModuleOptions(**resopts)

    def __init__(self, table=cxx_module_field_list, **kwargs):
        self.opts = kwargs
        self.table = table
        self.check()

    def __str__(self):
        return str(self.opts)


def cxx_options_from_modopts(modopts):
    """Конвертировать информацию из модуля в структуру опций cxx_make"""

    cxxstd = "-std=" + modopts["cxxstd"]
    ccstd = "-std=" + modopts["ccstd"]

    cxx_flags = " ".join([cxxstd, modopts["debug"], modopts["cxx_flags"]])
    cc_flags = " ".join([ccstd, modopts["debug"], modopts["cc_flags"]])

    ld_srcs_add = "".join([" -L" + os.path.expanduser(l)
                           for l in modopts["libdirs"]])
    ld_srcs_add += "".join([" -l" + l for l in modopts["libs"]])

    return licant.cxx_make.options(
        toolchain=modopts["toolchain"],
        include_paths=modopts["include_paths"],
        cc_flags=cc_flags,
        cxx_flags=cxx_flags,
        defines=modopts["defines"],
        ldscripts=modopts["ldscripts"],
        ld_flags=modopts["ld_flags"],
        ld_srcs_add=ld_srcs_add,
        optimize=modopts["optimize"],
    )


def build_paths(srcs, opts, ext, prefix=None, builddir=None):
    if builddir is None:
        builddir = opts.opts["builddir"]

    objs = []

    for s in srcs:
        if prefix:
            split = os.path.split(s)
            s = os.path.join(*split[:-1], prefix + split[-1])
        if os.path.isabs(s):
            s = builddir + gu.changeext(s, ext)
            objs.append(s)
        else:
            objs.append(
                os.path.normpath(
                    os.path.join(
                        builddir, gu.changeext(s, ext).replace("..", "__")
                    )
                )
            )

    return objs


def sources_paths(opts):
    ret = []
    for s in opts["sources"]:
        if "*" in s:
            ret.extend(glob.glob(s))
        else:
            ret.append(s)
    return ret


def qt_moc_paths(opts):
    ret = []
    for s in opts["qt_moc"]:
        if "*" in s:
            ret.extend(glob.glob(s))
        else:
            ret.append(s)
    return ret


def qt_ui_paths(opts):
    ret = []
    for s in opts["qt_ui"]:
        if "*" in s:
            ret.extend(glob.glob(s))
        else:
            ret.append(s)
    return ret


def link_objects(srcs, objs, deps, cxxopts, adddeps):

    for s, o, d in zip(srcs, objs, deps):
        if s not in licant.core.core.targets:
            licant.make.source(s)

        headers = cxx_read_depends(d)
        force = headers is None
        if headers is None:
            headers = []
        else:
            for h in headers:
                if h not in licant.core.core.targets:
                    licant.make.source(h)

        licant.cxx_make.depend(
            src=s, tgt=d, opts=cxxopts, deps=[s] + adddeps + headers, force=force
        )
        licant.cxx_make.object(
            src=s, tgt=o, opts=cxxopts, deps=[s, d] + adddeps + headers
        )


def link_qt_moc(mocs, srcs, cxxopts, adddeps):
    for m, s in zip(mocs, srcs):
        licant.make.source(m)
        licant.cxx_make.qt_moc(src=m, tgt=s, opts=cxxopts, deps=[m] + adddeps)


def link_qt_ui(uis, srcs, cxxopts, adddeps):
    for m, s in zip(uis, srcs):
        licant.make.source(m)
        licant.cxx_make.qt_uic(src=m, tgt=s, opts=cxxopts, deps=[m] + adddeps)


def executable(srcs, opts):
    cxxopts = cxx_options_from_modopts(opts)
    licant.cxx_make.executable(tgt=opts["target"], srcs=srcs, opts=cxxopts)
    return opts["target"]


def dynlib(srcs, opts):
    cxxopts = cxx_options_from_modopts(opts)
    licant.cxx_make.dynamic_library(
        tgt=opts["target"], srcs=srcs, opts=cxxopts)
    return opts["target"]


def statlib(srcs, opts):
    cxxopts = cxx_options_from_modopts(opts)
    licant.cxx_make.static_library(tgt=opts["target"], srcs=srcs, opts=cxxopts)
    return opts["target"]


def virtual(srcs, opts):
    licant.core.target(tgt=opts["target"], deps=srcs)
    return opts["target"]


def collect_modules(mod):
    # Альтернативная система модулей.
    mdepends_default = queue.Queue()
    mdepends = dict()
    included_from = dict()

    class SortKey:
        def __init__(self):
            self.sortkey = 0

        def __call__(self, mod):
            mod.__sortkey = self.sortkey
            self.sortkey += 1

    setsortkey = SortKey()

    def add_included_from(name, incfrom):
        if name not in included_from:
            included_from[name] = set()

        included_from[name].add(incfrom)

    def specify_implementation(name, mod, incfrom):
        mdepends[name] = mod
        setsortkey(mod)
        add_included_from(name, incfrom)

    def request_implementation(name, incfrom):
        mdepends_default.put(name)
        add_included_from(name, incfrom)

    def collect_modules(mod):
        if licant.core.core.runtime["trace"]:
            print("trace: collect_modules( {} )".format(mod.name))

        for md in mod.opts["mdepends"]:
            if isinstance(md, str):
                if md in mdepends:
                    continue

                request_implementation(name=md, incfrom=mod.name)

            elif isinstance(md, tuple):
                nmod = mlibrary.get(md[0], md[1])

                if md[0] in mdepends and mdepends[md[0]] is not nmod:
                    licant.error(
                        "This module added early and it's different: mod:{} now:{} early:{}".format(
                            licant.util.yellow(nmod.name),
                            licant.util.yellow(nmod.impl),
                            licant.util.yellow(mdepends[md[0]].impl),
                        )
                    )

                specify_implementation(name=md[0], mod=nmod, incfrom=mod.name)

                if "mdepends" in nmod.opts:
                    # Сразу же выполняем обход по данному модулю
                    collect_modules(nmod)

            else:
                licant.error("Very strange mpdepend")

    if "mdepends" in mod.opts:
        collect_modules(mod)

    while not mdepends_default.empty():
        name = mdepends_default.get()
        if name in mdepends:
            continue

        defmod = mlibrary.get_default(name)
        specify_implementation(name, defmod, mod.name)

        if "mdepends" in defmod.opts:
            collect_modules(defmod)

    for m in mdepends:
        mdepends[m].included_from = included_from[m]

    return [
        mdepends[x]
        for x in sorted(mdepends, key=lambda x: mdepends[x]._SortKey__sortkey)
    ]


def prepare_targets(name, impl=None, **kwargs):
    opts = CXXModuleOptions(**kwargs)
    opts.set_default_if_empty()

    def modmake(name, impl, baseopts):
        mod = mlibrary.get(name, impl)

        modopts = CXXModuleOptions(**mod.opts)
        locopts = baseopts.merge(modopts, "merge")

        adddeps = []  # mod.stack

        # Проходим по include_modules, рекурсивно формируем локальные опции.
        def include_modules(locopts, lst):
            retopts = locopts
            for simod in lst:
                imod = mlibrary.get(simod.name, simod.impl)
                retopts = retopts.merge(imod, "include")

                if "include_modules" in imod.opts:
                    retopts = include_modules(
                        retopts, imod.opts["include_modules"])

            return retopts

        locopts = include_modules(locopts, locopts["include_modules"])

        # Система модулей mdepends
        for imod in collect_modules(mod):
            locopts = locopts.merge(imod, "include")

        local_headers_targets = []
        if len(locopts["local_headers"]):
            locopts["include_paths"].append(
                locopts["builddir"] + "/__LOCAL_HEADERS__/")
            for pair in locopts["local_headers"]:
                licant.make.source(pair[1])
                tgtpath = os.path.join(
                    locopts["builddir"], "__LOCAL_HEADERS__", pair[0]
                )
                licant.make.copy(src=pair[1], tgt=tgtpath)

                local_headers_targets.append(tgtpath)

        licant.make.fileset(name + "__local_headers__", local_headers_targets)
        adddeps.append(name + "__local_headers__")

        for dep in locopts["depends"]:
            if "*" in dep:
                adddeps.extend(glob.glob(dep))
            else:
                adddeps.append(dep)

        locsrcs = sources_paths(locopts)
        locobjs = build_paths(locsrcs, locopts, "o")
        locdeps = build_paths(locsrcs, locopts, "d")

        cxxopts = cxx_options_from_modopts(locopts)

        if len(locopts["qt_ui"]) != 0:
            uidir = os.path.join(locopts.opts["builddir"], "ui")
            locui = qt_ui_paths(locopts)
            locuihxx = build_paths(locui, locopts, "h",
                                   builddir=uidir,
                                   prefix="ui_")
            link_qt_ui(locui, locuihxx, cxxopts, adddeps)
            adddeps.extend(locuihxx)

            if uidir not in locopts.opts["include_paths"]:
                locopts.opts["include_paths"].append(uidir)

            # Recompile with ui include path
            cxxopts = cxx_options_from_modopts(locopts)

        if len(locopts["qt_moc"]) != 0:
            locmoc = qt_moc_paths(locopts)
            locmoccxx = build_paths(locmoc, locopts, "h.cxx")
            locmocobjs = build_paths(locmoc, locopts, "h.cxx.o")
            locmocdeps = build_paths(locmoc, locopts, "h.cxx.d")
            link_qt_moc(locmoc, locmoccxx, cxxopts, adddeps)

            locsrcs.extend(locmoccxx)
            locobjs.extend(locmocobjs)
            locdeps.extend(locmocdeps)

        link_objects(locsrcs, locobjs, locdeps, cxxopts, adddeps)

        if len(locopts["objects"]) != 0:
            for t in locopts["objects"]:
                licant.make.source(t)
            locobjs.extend(locopts["objects"])

        submodules_results = []
        # print(locopts["modules"])
        for smod in locopts["modules"]:
            submodules_results += modmake(smod.name, smod.impl, locopts)

        if locopts["type"] == "application":
            return ([executable(locobjs + submodules_results, locopts)], locopts)
        elif locopts["type"] == "shared_library":
            return ([dynlib(locobjs + submodules_results, locopts)], locopts)
        elif locopts["type"] == "static_library":
            return ([statlib(locobjs + submodules_results, locopts)], locopts)
        elif locopts["type"] == "objects":
            return (locobjs + submodules_results, locopts)
        else:
            print("Wrong type of assemble: {}".format(gu.red(locopts["type"])))
            exit(-1)

    res, locopts = modmake(name, impl, opts)
    return (res, locopts)


def task(name, target, impl, type, **kwargs):
    if type != "objects":
        if target is None or target == name:
            target = "./" + name
        licant.modules.module(name, impl=impl, type=type,
                              target=target, **kwargs)
    else:
        licant.modules.module(name, impl=impl, type=type, **kwargs)
    ret, opts = prepare_targets(name)
    licant.make.fileset(tgt=name, targets=ret, finalopts=opts)
    return ret


def application(name, target=None, impl=None, type="application", **kwargs):
    return task(name, target, impl, type, **kwargs)


def shared_library(name, target=None, impl=None, type="shared_library", **kwargs):
    return task(name, target, impl, type, **kwargs)


def static_library(name, target=None, impl=None, type="static_library", **kwargs):
    return task(name, target, impl, type, **kwargs)


def objects(name, target=None, impl=None, type="objects", **kwargs):
    return task(name, target, impl, type, **kwargs)


def library(*args, shared=True, **kwargs):
    if shared:
        return shared_library(*args, **kwargs)
    else:
        return static_library(*args, **kwargs)


def static_and_shared(name, static_lib, shared_lib, **kwargs):
    static_library(static_lib, **kwargs)
    shared_library(shared_lib, **kwargs)
    return licant.fileset(tgt=name, targets=[static_lib, shared_lib])


def print_collect_list(target, *args):
    if len(args) > 0:
        name = args[0]
    else:
        print("You should specify target name")
        return
    for m in sorted(collect_modules(mlibrary.get(name)), key=lambda x: x.name):
        if hasattr(m, "impl"):
            print("{}:{}".format(m.name, m.impl))
        else:
            print(m.name)


def print_finalopts(target, *args):
    if len(args) > 0:
        name = args[0]
    else:
        name = licant.cli.default_target
    print(licant.core.core.get(name).finalopts)


def included_from(target, *args):
    if len(args) > 0:
        name = args[0]
    else:
        print("You should specify target name")
        return

    for m in sorted(collect_modules(mlibrary.get(name)), key=lambda x: x.name):
        print(m.name, ":", m.included_from)


modules_target = licant.core.Target(
    tgt="cxxm",
    deps=[],
    collect_modules=print_collect_list,
    included_from=included_from,
    finalopts=print_finalopts,
    actions={"collect_modules", "finalopts", "included_from"},
    __help__="Info about collected modules",
)

licant.core.core.add(modules_target)
