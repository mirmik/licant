#!/usr/bin/env python3.5
#coding: utf-8

import sys
sys.path.insert(0, "..")

from glink.make import copy, file, make, clean

file("first")
copy(src="second", tgt="third")
copy(src="first", tgt="second")

make("third")
clean("third")

#cpp = glink.cxx_make.host_cxx_maker(includePaths=["inc"])
#
#srcs = [
#	"main.cpp", 
#	"ttt.cpp"
#]
#
#objs = ["build/main/" + gu.changeext(s,"o") for s in srcs]
#
#
#for s, o in zip(srcs, objs):
#    cpp.file(s)
#    cpp.object(src=s, tgt=o)
#
#cpp.executable(tgt="target", srcs=objs)
#
#target = "target"
#
#def all():
#	return cpp.make(target)
#
#def clean():
#	return cpp.clean(target)
#
#result = glink.util.do_argv_routine(arg=1, default="all", locs=locals())
#cpp.print_result_string(result)