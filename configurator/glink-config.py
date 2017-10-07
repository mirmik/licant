#!/usr/bin/python3
#coding: utf-8

import sys
import os
import json
from optparse import OptionParser

usage = "usage: %prog [options] lib path"
parser = OptionParser(usage = usage)
parser.add_option("-l", "--local", action = "store_true", default = False)
parser.add_option("-r", "--remove", action = "store_true", default = False)
opts, args = parser.parse_args(sys.argv[1:])

if not ((len(args) == 2) or (opts.remove and len(args) == 1)):
	#parser.print_help()
	parser.error("incorrect numbers of argument")
	exit(0)

if opts.local:
	paths_file = os.path.expanduser("~/.config/licant") 
else:
	paths_file = "/etc/licant" 

name = args[0]

if (os.path.exists(paths_file)):
	try:
		paths = json.load(open(paths_file))
	except:
		print("Load error:")
		print("Wrong format", paths_file)
		exit(-1)
else:
	paths = {}

if opts.remove:
	try:
		del paths[name]
	except:
		print("Unregistred library {}".format(name))

else:
	path = args[1]
	abspath = os.path.abspath(path)
	exists = os.path.exists(abspath)

	if not exists:
		print("File {} is not exists".format(path))
		exit(-1)

	paths[name] = abspath

try:
	json.dump(paths, open(paths_file, "w"))
except IOError as e:
	print("Dump error:")
	print(e)
	exit(-1)

print("Libraries:")
for k, v in paths.items():
	print(k, v)