#!/usr/bin/env python

import sys
sys.path.insert(0, "../..")

import licant

@licant.routine
def routine1():
	print("1")

@licant.routine
def routine2():
	print("2")

@licant.routine(depacts = ["routine1", "routine2"])
def routine3():
	print("3")

licant.ex("routine1")