from licant.scripter import scriptq

import os
import sys
import json

gpath = "/etc/licant"
lpath = os.path.expanduser("~/.config/licant")

libs = None

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def include(lib):
	global libs
	if libs == None:
		glibs = {}
		llibs = {}

		if os.path.exists(gpath):
			glibs = json.load(open(gpath))

		if os.path.exists(lpath):
			llibs = json.load(open(lpath))

		libs =  merge_two_dicts(glibs, llibs)

	if not lib in libs:
		print("Unregistred library")
		exit(-1)

	#print(libs[lib])
	scriptq.execute(libs[lib])	