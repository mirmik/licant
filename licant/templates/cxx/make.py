#!/usr/bin/env python3

from licant.cxx_modules import application, doit

application("target",
	sources = ["main.cpp"]
)

doit("target")