#!/usr/bin/python3
#coding: utf-8

from licant.cxx_modules import application, doit
from licant.modules import submodule
from licant.libs import include

include("gxx")

application("main",
	sources = ["main.cpp"],

	include_modules = [
		submodule("gxx"),
		submodule("gxx.dprint", "stdout")
	]
)

doit("main")