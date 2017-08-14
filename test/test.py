#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "..")

import glink.util as gu
from glink.make import copy, file, print_result_string
import glink.make
import glink.cxx_make as cxx

print(gu.green("Script Start"))

opts = cxx.options(
	binutils = cxx.host_binutils,
)

srcs = [
	"main.cpp", 
	"ttt.cpp"
]

objs = ["build/main/" + gu.changeext(s,"o") for s in srcs]


for s, o in zip(srcs, objs):
    file(s)
    cxx.object(src=s, tgt=o, opts=opts)

cxx.executable(tgt="target", srcs=objs, opts=opts)

copy(src="target", tgt="mirmik")

target = "mirmik"

def all():
	return glink.make.make(target)

def clean():
	return glink.make.clean(target)

result = gu.do_argv_routine(arg=1, default="all", locs=locals())
print_result_string(result)