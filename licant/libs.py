from licant.scripter import scriptq
from licant.util import yellow
import licant.core

import os
import sys
import json

gpath = "/var/lib/licant"
lpath = os.path.expanduser("~/.licant")

libs = None


def merge_two_dicts(x, y):
	z = x.copy()   # start with x's keys and values
	z.update(y)    # modifies z with y's keys and values & returns None
	return z


def init():
	global libs

	glibs = {}
	llibs = {}

	if os.path.exists(gpath):
		glibs = json.load(open(gpath))

	if os.path.exists(lpath):
		llibs = json.load(open(lpath))

	libs = merge_two_dicts(glibs, llibs)

def include(lib):
	if libs is None:
		init()

	if not lib in libs:
		print("Unregistred library {}. Use licant-config utility or manually edit {} or {} file.".format(
			yellow(lib), yellow(lpath), yellow(gpath)))
		exit(-1)

	scriptq.execute(libs[lib])

def print_libs(taget, *args):
	if libs is None:
		init()
		
	keys = sorted(libs.keys())
	for k in keys:
		print("{}: {}".format(k,libs[k]))


libs_target = licant.core.Target(
	tgt="l",
	deps=[],
	list=print_libs,
	actions={"list"}
)

licant.core.core.add(libs_target)
