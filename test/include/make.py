#!/usr/bin/python3
#coding: utf-8

from glink.cxx_modules import application, doit
from glink.libs import include

include("gxx")

application("main",
	sources = ["main.cpp"]
)

doit("main")