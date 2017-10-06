#!/usr/bin/python3
#coding: utf-8

from glink.cxx_modules import application, doit
from glink.modules import submodule
from glink.libs import include

include("gxx")

application("main",
	sources = ["main.cpp"],

	include_modules = [
		submodule("gxx"),
		submodule("gxx.dprint", "stdout")
	]
)

doit("main")