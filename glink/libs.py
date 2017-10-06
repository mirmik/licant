from glink.scripter import scriptq

import os
import sys
import json

gpath = "/etc/glink"
lpath = os.path.expanduser("~/.config/glink")

libs = None

def include(lib):
	global libs
	if libs == None:
		glibs = {}
		llibs = {}

		if os.path.exists(gpath):
			glibs = json.load(open(gpath))

		if os.path.exists(lpath):
			llibs = json.load(open(lpath))

		libs = {**glibs, **llibs}

	if not lib in libs:
		print("Unregistred library")
		exit(-1)

	scriptq.execute(libs[lib])	