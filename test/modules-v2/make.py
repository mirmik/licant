#!/usr/bin/env python3
#coding: utf-8

import sys

sys.path.insert(0, "../..")

import licant

licant.module("module_a", impl="a",
	sources = ["a.cpp"]
)

licant.module("module_a", impl="b",
	sources = ["b.cpp"]
)

licant.module("module_b",
	sources = ["c.cpp"],
	mdepends = [
		("module_a", "a"),
	]
)

licant.module_defimpl("module_a", "a")


licant.cxx_application("target",
	sources = ["main.cpp"],
	mdepends = [
		"module_b",
		("module_a", "a"),
	]
)


licant.ex("target")