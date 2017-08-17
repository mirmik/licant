#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "..")

import glink.util as gu
from glink.make import copy, ftarget, source, function, print_result_string
import glink.make
import glink.cxx_make as cxx

print(gu.green("Script Start"))

#opts = cxx.options(
#	binutils = cxx.host_binutils,
#)
#
#srcs = [
#	"a.cpp", 
#	"b.cpp"
#]
#
#objs = ["build/main/" + gu.changeext(s,"o") for s in srcs]
#
#
#for s, o in zip(srcs, objs):
#    source(s)
#    cxx.object(src=s, tgt=o, opts=opts)
#
#cxx.executable(tgt="target", srcs=objs, opts=opts)

#copy(src="target", tgt="mirmik")
source("a.cpp")
source("b.cpp")

ftarget(tgt="a.o", deps=["a.cpp"], 			build=glink.make.execute("g++ a.cpp -c -o a.o"))
ftarget(tgt="b.o", deps=["b.cpp"], 			build=glink.make.execute("g++ b.cpp -c -o b.o"))
ftarget(tgt="target", deps=["a.o", "b.o"], 	build=glink.make.execute("g++ a.o b.o -o target"))
ftarget(tgt="mirmik", deps=["target", "fnc"], 		build=glink.make.execute("cp target mirmik"))

def func(*args, **kwargs):
	print("Раньше mirmik, но позже target")

function(tgt="fnc", deps=["target"], func=func)


target = "mirmik"
def all():
	return glink.make.make(target)

def clean():
	return glink.make.clean(target)

result = gu.do_argv_routine(arg=1, default="all", locs=locals())
print_result_string(result)