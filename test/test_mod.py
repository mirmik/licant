#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "..")

import glink.util as gu
from glink.modules import module, submodule
#
#import glink.core
#import glink.cxx_make
import glink.cxx_modules

module("lib",
	sources=["src/lib.cpp"]
)

module("main",
	srcdir = "src",
	sources = ["main.cpp", "ttt.cpp"],
	includePaths = ["inc"],

	modules=[
		submodule("lib")
	]
)

glink.cxx_modules.make("main",
	type = "application",
	target = "target",
	builddir = "build",
	binutils = glink.cxx_make.host_binutils
)

glink.make.copy(src = "target", tgt = "target2")
target = "target2"

def all():
	return glink.make.make(target, rebuild=True)

def clean():
	return glink.make.clean(target)

def install():
	print("Делаю вид, что инсталирую")

result = gu.do_argv_routine(arg=1, default="all", locs=locals())
glink.make.print_result_string(result)