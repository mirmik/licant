#!/usr/bin/env python

import sys
sys.path.insert(0, "../..")

import licant

@licant.default_routine
def routine1():
	print("1")

@licant.routine
def routine2():
	print("2")

licant.ex()