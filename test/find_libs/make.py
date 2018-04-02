#!/usr/bin/env python

import sys
sys.path.insert(0, "../..")

import licant
from licant.cxx_modules import application
from licant.modules import submodule
from licant.libs import include, find_library

qt5 = find_library("qt5")
print(qt5)





def qt5_init_action(mod, opts):
	parts = getattr(opts, "parts", None)
	if parts == None:
		licant.error("QtModuleError")

	qtIncPath = licant.find_include_path("qt5")
	
	mod.opts["include_modules"].append(
		submodule("qt5.base", path = qtIncPassth),
	)

	mod.opts["include_modules"].extend(
		submodule("qt5.{}".format(sub), path = qtIncPassth) for sub in parts,
	)

module("qt5",
	init_action = qt5_init_action,
)