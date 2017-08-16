from glink.modules import mlibrary
from glink.cxx_make import host_binutils, binutils
from glink.util import red, yellow

import os
import glink.util as gu
import glink.make


class solver:
	def __init__(self, type, merge, include, default):
		self.type 	 = type
		self.merge	 = merge
		self.include = include
		self.default = default

def base(base, local, solver):
	return base

def local(base, local, solver):
	if local == None:
		return solver.default
	return local

def lstconcat(base, local, solver):
	if local == None:
		local = []
	return base + local

cxx_module_field_list = {
	"loglevel": 		solver("str", 		base, 		base,	"info"),
	"srcdir": 			solver("str", 		local, 		base,	"."),
	"sources": 			solver("list", 		local, 		base,	[]),
	"target": 			solver("str", 		base, 		base,	"target"),
	"includePaths": 	solver("list", 		lstconcat, 	base,	[]),
	"cxxstd": 			solver("str", 		base, 		base,	"c++11"),
	"ccstd": 			solver("str", 		base, 		base,	"c11"),
	"modules": 			solver("list", 		local, 		base,	[]),
	"type": 			solver("str", 		base, 		base,	"application"),
	"builddir": 		solver("str", 		base, 		base,	"build"),
	"binutils": 		solver("binutils", 	base, 		base,	host_binutils),
	"includeModules": 	solver("list", 		base, 		base,	[]),
}

class CXXModuleOptions:
	def __getitem__(self, key):
		return self.opts[key]

	def check(self):
		for k, v in self.opts.items():
			if not k in self.table:
				print("Нераспознанная опция: {}".format(red(k)))
				exit(-1)

			if (self.table[k].type != type(v).__name__):
				print("Опция должна быть объектом типа {}: {}".format(yellow(self.table[k].type), red(k)))
				exit(-1)

	def set_default_if_empty(self, table=cxx_module_field_list):
		for k in table:
			if not k in self.opts:
				self.opts[k] = table[k].default

	def merge(self, other):
		resopts = {}
		for k, v in self.opts.items():
			
			base = self.opts[k]
			if k in other.opts:
				local = other.opts[k]
			else: 
				local = None

			resopts[k] = self.table[k].merge(base, local, self.table[k])

		return CXXModuleOptions(**resopts)
		
	def __init__(self, table=cxx_module_field_list, **kwargs):
		self.opts = kwargs
		self.table = table
		self.check()

def cxx_options_from_modopts(modopts):
	return glink.cxx_make.options(
		binutils = modopts["binutils"],
		includePaths = modopts["includePaths"]
	)

def objects_paths(srcs, opts):
	objs = []
	for s in srcs:
		objs.append(os.path.normpath(os.path.join(opts.opts["builddir"], gu.changeext(s, "o")))) 
	return objs

def sources_paths(opts):
	return [os.path.normpath(os.path.join(opts["srcdir"], s)) for s in opts["sources"]]


def link_objects(srcs, objs, opts):
	if opts["loglevel"] == "debug":
		message = None
		echo = True
	elif opts["loglevel"] == "info":
		message="OBJECT {tgt}"
		rmmsg = "DELETE {tgt}" 
		echo=False

	cxxopts = cxx_options_from_modopts(opts)
	for s, o in zip(srcs, objs):
		glink.make.file(s)
		glink.cxx_make.object(src=s, tgt=o, opts=cxxopts, message=message, rmmsg=rmmsg, echo=echo)

def application(srcs, opts):
	if opts["loglevel"] == "debug":
		message = None
		echo = True
	elif opts["loglevel"] == "info":
		message="APPLICATION {tgt}" 
		rmmsg = "DELETE {tgt}"
		echo=False

	cxxopts = cxx_options_from_modopts(opts)
	glink.cxx_make.executable(tgt=opts["target"], srcs=srcs, opts=cxxopts, message=message, rmmsg=rmmsg, echo=echo)
	return opts["target"]

def make(name, **kwargs):
	#mod = mlibrary.get(name)
	#print("make module {}".format(mod.name))

	opts = CXXModuleOptions(**kwargs)
	opts.set_default_if_empty()

	def modmake(name, baseopts):
		mod = mlibrary.get(name)
		
		modopts = CXXModuleOptions(**mod.opts)
		locopts = baseopts.merge(modopts)
		
		locsrcs = sources_paths(locopts)
		locobjs = objects_paths(locsrcs, locopts)

		link_objects(locsrcs, locobjs, locopts)

		submodules_results = []
		for smod in locopts["modules"]:
			submodules_results += modmake(smod.name, locopts)

		return locobjs + submodules_results

	result = modmake(name, opts)
	if opts["type"] == "application":
		return application(result, opts)