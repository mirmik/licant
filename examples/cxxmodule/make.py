#!/usr/bin/env python3
# coding: utf-8

import sys

sys.path.insert(0, "../..")

from licant.cxx_modules import application, shared_library, objects
import licant

aret = application(
	"app", 
	sources=[
		"main.cpp", 
		"ttt.cpp"
	], 
	optimize="-O2")

licant.ex("app")
