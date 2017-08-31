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

def base(base, local, solver, tbase, tlocal):
	return base

def local(base, local, solver, tbase, tlocal):
	if local == None:
		return solver.default
	return local

def concat(base, local, solver, tbase, tlocal):
	if local == None:
		local = []
	return base + local

def concat_add_srcdir(base, local, solver, tbase, tlocal):
	if local == None:
		local = []
	else:
		if "srcdir" in tlocal.opts:
			srcdir = tlocal.opts["srcdir"]
		else:
			srcdir = ""

		local = list(map(lambda p: os.path.join(tlocal.opts["__dir__"], srcdir, p), local))
	return base + local

def local_add_srcdir(base, local, solver, tbase, tlocal):
	if "srcdir" in tlocal.opts:
		srcdir = tlocal.opts["srcdir"]
	else:
		srcdir = ""
	return list(map(lambda p: os.path.join(tlocal.opts["__dir__"], srcdir, p), local))
	
def concat_add_locdir(base, local, solver, tbase, tlocal):
	if local == None:
		local = []
	else:
		local = list(map(lambda p: os.path.join(tlocal.opts["__dir__"], p), local))
	return base + local

cxx_module_field_list = {
	"loglevel": 		solver("str", 		base, 						base,					"info"),
	"srcdir": 			solver("str", 		local, 						base,					"."),
	"sources": 			solver("list", 		local_add_srcdir,			concat_add_srcdir,		[]),
	"target": 			solver("str", 		base, 						base,					"target"),
	"include_paths": 	solver("list", 		concat_add_locdir, 			concat_add_locdir,		[]),
	"cxxstd": 			solver("str", 		base, 						base,					"c++11"),
	"ccstd": 			solver("str", 		base, 						base,					"c11"),
	"cxx_flags": 		solver("str", 		base, 						base,					""),
	"cc_flags": 		solver("str", 		base, 						base,					""),
	"modules": 			solver("list", 		local, 						concat,					[]),
	"type": 			solver("str", 		base, 						base,					"application"),
	"builddir": 		solver("str", 		base, 						base,					"build"),
	"binutils": 		solver("binutils", 	base, 						base,					host_binutils),
	"include_modules": 	solver("list", 		concat, 					local,					[]),
}

class CXXModuleOptions:
	def __getitem__(self, key):
		return self.opts[key]

	def check(self):
		for k, v in self.opts.items():
			if not k in glink.modules.special:
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

	def merge(self, other, fnc):
		resopts = {}
		for k, v in self.opts.items():
			
			base = self.opts[k]
			if k in other.opts:
				local = other.opts[k]
			else: 
				local = None

			func = getattr(self.table[k], fnc)
			resopts[k] = func(base, local, self.table[k], self, other)

		return CXXModuleOptions(**resopts)

	def __init__(self, table=cxx_module_field_list, **kwargs):
		self.opts = kwargs
		self.table = table
		self.check()

def cxx_options_from_modopts(modopts):
	cxxstd = "-std=" + modopts["cxxstd"]
	ccstd = "-std=" + modopts["ccstd"]

	cxx_flags = cxxstd + " " + modopts["cxx_flags"]
	cc_flags = ccstd + " " + modopts["cc_flags"]

	return glink.cxx_make.options(
		binutils = modopts["binutils"],
		include_paths = modopts["include_paths"],
		cc_flags = cc_flags,
		cxx_flags = cxx_flags,
	)	

def build_paths(srcs, opts, ext):
	objs = []
	for s in srcs:
		objs.append(os.path.normpath(os.path.join(opts.opts["builddir"], gu.changeext(s, ext).replace("..", "__")))) 
	return objs

def sources_paths(opts, moddir):
	return opts["sources"]
	#return [os.path.normpath(os.path.join(moddir, opts["srcdir"], s)) for s in opts["sources"]]


def link_objects(srcs, objs, opts, adddeps):
	cxxopts = cxx_options_from_modopts(opts)
	for s, o in zip(srcs, objs):
		glink.make.source(s)
		glink.cxx_make.object(src=s, tgt=o, opts=cxxopts, deps=[s] + adddeps)

def application(srcs, opts):
	cxxopts = cxx_options_from_modopts(opts)
	glink.cxx_make.executable(tgt=opts["target"], srcs=srcs, opts=cxxopts)
	return opts["target"]

def virtual(srcs, opts):
	glink.core.target(tgt=opts["target"], deps=srcs)
	return opts["target"]

def make(name, **kwargs):
	#mod = mlibrary.get(name)
	#print("make module {}".format(mod.name))

	opts = CXXModuleOptions(**kwargs)
	opts.set_default_if_empty()

	def modmake(name, impl, baseopts):
		mod = mlibrary.get(name, impl)

		moddir = os.path.dirname(mod.script)
		
		modopts = CXXModuleOptions(**mod.opts)
		locopts = baseopts.merge(modopts, "merge")

		for simod in locopts["include_modules"]:
			imod = mlibrary.get(simod.name, simod.impl)
			locopts = locopts.merge(imod, "include")

		locsrcs = sources_paths(locopts, moddir)
		locobjs = build_paths(locsrcs, locopts, "o")
		locdeps = build_paths(locsrcs, locopts, "d")

		adddeps = mod.stack
		
		link_objects(locsrcs, locobjs, locopts, adddeps)

		submodules_results = []
		#print(locopts["modules"])
		for smod in locopts["modules"]:
			submodules_results += modmake(smod.name, smod.impl, locopts)

		return locobjs + submodules_results

	result = modmake(name, None, opts)
	if opts["type"] == "application":
		return application(result, opts)
	elif opts["type"] == "objects":
		return virtual(result, opts)
	else:
		print("Неверный тип сборки: {}", gu.red(opts["type"]))
		exit(-1)