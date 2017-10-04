#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

from glink.cxx_modules import application, doit

application("main",
	sources = ["main.cpp", "ttt.cpp"]
)

doit("main")
