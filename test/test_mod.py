#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "..")

import glink.util as gu
from glink.modules import module

import glink.cxx_make
import glink.cxx_modules

module("main",
	sources = ["main.cpp"],
	includeModules=[]
)

glink.cxx_modules.make("main",
	type = "application",
	builddir = "build",
	sources = ["dasd"],
	binutils = glink.cxx_make.host_binutils
)