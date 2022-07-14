#!/usr/bin/python
#coding: utf-8

import sys
import os
import json
from optparse import OptionParser

import licant.libs

paths = {}


def add_record(name, path):
    global paths
    abspath = os.path.abspath(path)
    exists = os.path.exists(abspath)

    if not exists:
        print("File {} is not exists".format(path))
        exit(-1)

    paths[name] = abspath


def licant_libs_utility():
    global paths
    usage = "usage: %prog [options] lib path"
    parser = OptionParser(usage=usage)
    parser.add_option("-u", "--user", action="store_true", default=False)
    parser.add_option("-r", "--remove", action="store_true", default=False)
    parser.add_option("-l", "--list", action="store_true", default=False)
    opts, args = parser.parse_args(sys.argv[1:])

    paths_file = licant.libs.lpath if opts.user else licant.libs.gpath

    if (os.path.exists(paths_file)):
        try:
            paths = json.load(open(paths_file))
        except:
            print("Load error:")
            print("Wrong format", paths_file)
            exit(-1)
    else:
        paths = {}

    if opts.list:
        print("Libraries:")
        for k, v in paths.items():
            print(k, v)
        exit(0)

    if len(args) > 2 or (opts.remove and len(args) != 1):
        parser.error("incorrect numbers of argument")
        exit(0)

    if len(args) == 0:
        parser.help()
        exit(0)

    path = None
    name = None
    if len(args) == 2 and opts.remove == False:
        name = args[0]
        path = args[1]
        add_record(name, path)

    if len(args) == 1 and opts.remove == False:
        import glob
        ret = glob.glob(os.path.join(args[0], "*.g.py"))
        for f in ret:
            fname = os.path.basename(f)
            name = fname.split('.')[0]
            path = f
            add_record(name, path)

    if opts.remove:
        try:
            del paths[name]
        except:
            print("Unregistred library {}".format(name))

    try:
        print(f"update: {paths_file}, text: {json.dumps(paths, indent=4)}")
        json.dump(paths, open(paths_file, "w"))
    except IOError as e:
        print("Dump error:")
        print(e)
        exit(-1)


if __name__ == "__main__":
    licant_libs_utility()
