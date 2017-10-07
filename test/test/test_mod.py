#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "../..")

from licant.modules import module, submodule
import licant.cxx_modules

licant.scripter.scriptq.execute("src/test.g.py")

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
	],

	type = "application",
	target="target",
	
)

target = licant.cxx_modules.make("main",
	builddir = "build",
	binutils = licant.cxx_make.host_binutils
)

licant.make.doit(target)