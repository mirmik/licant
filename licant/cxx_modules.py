from licant.modules import mlibrary
from licant.cxx_make import host_binutils, binutils
from licant.util import red, yellow, cxx_read_depends


import os
import licant.util as gu
import licant.make

import glob

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

def strconcat(base, local, solver, tbase, tlocal):
	if local == None:
		return base
	return base + " " + local

def concat_add_srcdir(base, local, solver, tbase, tlocal):
	if local == None:
		local = []
	else:
		if "srcdir" in tlocal.opts:
			srcdir = tlocal.opts["srcdir"]
		else:
			srcdir = ""

		local = list(map(lambda p: os.path.join(tlocal.opts["__dir__"], srcdir, p), local))
	#print(base + local)
	return base + local

def local_add_srcdir(base, local, solver, tbase, tlocal):
	if "srcdir" in tlocal.opts:
		srcdir = tlocal.opts["srcdir"]
	else:
		srcdir = ""
	if isinstance(local, type("str")):
		local = [local]
	return list(map(lambda p: os.path.join(tlocal.opts["__dir__"], srcdir, p), local))
	
def concat_add_locdir(base, local, solver, tbase, tlocal):
	if local == None:
		local = []
	else:
		if isinstance(local, type("str")):
			local = [local]
		local = list(map(lambda p: os.path.join(tlocal.opts["__dir__"], p), local))
	return base + local

def local_if_exist(base, local, solver, tbase, tlocal):
	if local == None:
		return base
	else:
		return local


cxx_module_field_list = {
#	"loglevel": 		solver("str", 		base, 						base,					"info"),
	"srcdir": 			solver("str", 		local, 						base,					"."),
	"sources": 			solver("list", 		local_add_srcdir,			concat_add_srcdir,		[]),
	"libs": 			solver("list", 		local,						base,		[]),
	"target": 			solver("str", 		local_if_exist,				base,					"target"),
	"include_paths": 	solver("list", 		concat_add_locdir, 			concat_add_locdir,		[]),
	"cxxstd": 			solver("str", 		local_if_exist, 			local_if_exist,			"c++14"),
	"ccstd": 			solver("str", 		local_if_exist, 			local_if_exist,			"c11"),
	"cxx_flags": 		solver("str", 		strconcat, 					strconcat,				""),
	"cc_flags": 		solver("str", 		strconcat, 					strconcat,				""),
	"ld_flags": 		solver("str", 		strconcat, 					strconcat,				""),
	"modules": 			solver("list", 		local, 						concat,					[]),
	"type": 			solver("str", 		local,			 			base,					"objects"),
	"builddir": 		solver("str", 		base, 						base,					"build"),
	"binutils": 		solver("binutils", 	local_if_exist, 			base,					host_binutils),
	"include_modules": 	solver("list", 		concat, 					base,					[]),
	"defines": 			solver("list", 		concat, 					concat,					[]),
	"ldscripts":		solver("list", 		concat_add_locdir, 			concat_add_locdir,		[]),
}

class CXXModuleOptions:
	def __getitem__(self, key):
		return self.opts[key]

	def check(self):
		for k, v in self.opts.items():
			if not k in licant.modules.special:
				if not k in self.table:
					print("Unresolved option: {}".format(red(k)))
					exit(-1)

				if v.__class__.__name__ != self.table[k].type:
					print("Option should be object of {}: {}".format(yellow(self.table[k].type), red(k)))
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

	ld_libs = "".join([" -l" + l for l in modopts["libs"]])

	return licant.cxx_make.options(
		binutils = modopts["binutils"],
		include_paths = modopts["include_paths"],
		cc_flags = cc_flags,
		cxx_flags = cxx_flags,
		defines = modopts["defines"],
		ldscripts = modopts["ldscripts"],
		ld_flags = modopts["ld_flags"] + ld_libs,
	)	

def build_paths(srcs, opts, ext):
	#print(srcs)
	objs = []
	for s in srcs:
		if os.path.isabs(s):
			objs.append(opts.opts["builddir"] + gu.changeext(s, ext))
		else:
			objs.append(os.path.normpath(os.path.join(opts.opts["builddir"], gu.changeext(s, ext).replace("..", "__")))) 
	#print(objs)
	return objs

def sources_paths(opts, moddir):
	ret = []
	for s in opts["sources"]:
		if "*" in s:
			ret.extend(glob.glob(s))		
		else:
			ret.append(s)
	return ret

def link_objects(srcs, objs, deps, opts, adddeps):
	cxxopts = cxx_options_from_modopts(opts)
	for s, o, d in zip(srcs, objs, deps):
		licant.make.source(s)
		
		headers = cxx_read_depends(d)
		if headers == None:
			headers = []
		else:
			for h in headers:
				licant.make.source(h)
		licant.cxx_make.depend(src=s, tgt=d, opts=cxxopts, deps=[s] + adddeps + headers)
		licant.cxx_make.object(src=s, tgt=o, opts=cxxopts, deps=[s, d] + adddeps + headers)

def executable(srcs, opts):
	cxxopts = cxx_options_from_modopts(opts)
	licant.cxx_make.executable(tgt=opts["target"], srcs=srcs, opts=cxxopts)
	return opts["target"]

def virtual(srcs, opts):
	licant.core.target(tgt=opts["target"], deps=srcs)
	return opts["target"]

def make(name, impl = None, **kwargs):
	opts = CXXModuleOptions(**kwargs)
	opts.set_default_if_empty()

	def modmake(name, impl, baseopts):
		mod = mlibrary.get(name, impl)

		moddir = os.path.dirname(mod.script)
		
		modopts = CXXModuleOptions(**mod.opts)
		locopts = baseopts.merge(modopts, "merge")

		def include_modules(locopts, lst):
			retopts = locopts
			for simod in lst:
				imod = mlibrary.get(simod.name, simod.impl)
				retopts = retopts.merge(imod, "include")

				if "include_modules" in imod.opts:
					retopts = include_modules(retopts, imod.opts["include_modules"])

			#print(retopts.__dict__)
			return retopts

		locopts = include_modules(locopts, locopts["include_modules"])

		locsrcs = sources_paths(locopts, moddir)
		locobjs = build_paths(locsrcs, locopts, "o")
		locdeps = build_paths(locsrcs, locopts, "d")

		adddeps = []#mod.stack
		
		link_objects(locsrcs, locobjs, locdeps, locopts, adddeps)

		submodules_results = []
		#print(locopts["modules"])
		for smod in locopts["modules"]:
			submodules_results += modmake(smod.name, smod.impl, locopts)

		if locopts["type"] == "application":
			return executable(locobjs + submodules_results, locopts)
		elif locopts["type"] == "objects":
			#print(locobjs + submodules_results)
			#return virtual(locobjs + submodules_results, locopts)
			#print(locobjs + submodules_results)
			return locobjs + submodules_results
		else:
			print("Wrong type of assemble: {}", gu.red(locopts["type"]))
			exit(-1)

	res = modmake(name, impl, opts)
	return res 

def application(name, impl=None, type="application", target="target", **kwargs):
	return licant.modules.module(name, impl=impl, type=type, target=target, **kwargs)

def doit(mod):
	licant.make.doit(make(mod))