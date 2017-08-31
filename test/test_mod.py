#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "..")

import glink.util as gu
from glink.modules import module, submodule
#
from glink.core import core
#import glink.cxx_make
import glink.cxx_modules

glink.scripter.scriptq.execute("src/test.g.py")


#glink.core.core.runtime["infomod"] = "debug"
#opts = core.parse_argv(sys.argv[1:])

module("lib",
	sources=["src/lib.cpp"]
)

module("libimpl", impl = "std",
	sources=["src/aaa.cpp"]
)

module("incm",
	sources=["src/inc.cpp"]
)

module("main",
	srcdir = "src",
	sources = ["main.cpp", "ttt.cpp"],
	include_paths = ["inc"],

	modules=[
		submodule("lib"),
		submodule("libimpl", "std"),
		submodule("lll")
	],

	include_modules=[
		submodule("incm")
	]
)

target = glink.cxx_modules.make("main",
	type = "objects",
	target="target",
	builddir = "build",
	binutils = glink.cxx_make.host_binutils
)

#glink.make.copy(src = "target", tgt = "target2")
#target = "target2"

#def all():
#	return glink.make.make(target)

#def clean():
#	return glink.make.clean(target)

#def install():
#	print("Делаю вид, что инсталирую")

result = glink.make.doit(target)

#result = gu.do_argv_routine(arg=1, default="all", locs=locals())
glink.make.print_result_string(result)