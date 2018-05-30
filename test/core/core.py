#!/usr/bin/env python3
#coding: utf-8

import os
import sys

sys.path.insert(0, "../..")

import licant

core = licant.Core()

def hello_world_0(tgt):
	print("hw0")

def hello_world_1(tgt):
	print("hw1")

def copy(tgt):
	task = "cp {} {}".format(tgt.src, tgt.tgtpath)
	print(task)
	res = os.system(task)

core.add(licant.Target(tgt="copy", src="a", tgtpath="b", deps=[], do=copy))
core.add(licant.Target(tgt="hello_world_0", deps=[], do=hello_world_0))
core.add(licant.Target(tgt="hello_world_1", deps=["hello_world_0", "copy"], do=hello_world_1))

stree = core.subtree("hello_world_1")

print(stree)

stree.reverse_recurse_invoke("do", threads = 1)

