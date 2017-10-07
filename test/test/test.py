#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "..")

import licant.util as gu
from licant.make import copy, ftarget, source, function, print_result_string
import licant.make
import licant.cxx_make as cxx

print(gu.green("Script Start"))

opts = cxx.options(
	binutils = cxx.host_binutils,
	cxx_flags = "-std=c++98"
)

srcs = [
	"a.c", 
	"b.cpp"
]

objs = ["build/main/" + gu.changeext(s,"o") for s in srcs]


for s, o in zip(srcs, objs):
    source(s)
    cxx.object(src=s, tgt=o, opts=opts)

cxx.executable(tgt="target", srcs=objs, opts=opts)


def func(*args, **kwargs):
	print("Раньше mirmik, но позже target")

function(tgt="fnc", deps=["target"], func=func)
copy(tgt="mirmik", src="target", adddeps=["fnc"])

target = "mirmik"
def all():
	return licant.make.make(target)

def clean():
	return licant.make.clean(target)

result = gu.do_argv_routine(arg=1, default="all", locs=locals())
print_result_string(result)