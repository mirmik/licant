from glink.core import core
import glink.make
import os

class binutils:
	def __init__(self, cxx, cc, ld, ar, objdump):
		self.cc = cc
		self.cxx = cxx
		self.ld = ld
		self.ar = ar
		self.objdump = objdump

class CXXCompileOptions:
	def __init__(self, binutils, includePaths = None, defines = None, cxx_flags="", cc_flags="", ld_flags=""):
		self.binutils = binutils
		self.incopt = glink.util.flag_prefix("-I", includePaths) 
		self.defopt = glink.util.flag_prefix("-D", defines) 
		self.cxx_flags = cxx_flags
		self.cc_flags = cc_flags
		self.ld_flags = ld_flags
		self.execrule=  "{opts.binutils.cxx} {srcs} -o {tgt} {opts.ld_flags}"
		self.cxxobjrule="{opts.binutils.cxx} -c {src} -o {tgt} {opts.incopt} {opts.defopt} {opts.cxx_flags}"
		self.ccobjrule= "{opts.binutils.cc} -c {src} -o {tgt} {opts.incopt} {opts.defopt} {opts.cc_flags}"

def options(binutils, includePaths = None, defines = None, cxx_flags="", cc_flags="", ld_flags=""):
		return CXXCompileOptions(binutils, includePaths, defines, cxx_flags, cc_flags, ld_flags)
	
cxx_ext_list = ["cpp", "cxx"]
cc_ext_list = ["cc", "c"]
asm_ext_list = ["asm", "s", "S"]

host_binutils = binutils(
	cxx= 		"c++",
	cc= 		"cc",
	ld= 		"ld",
	ar= 		"ar",
	objdump= 	"objdump"
)

def object(src, tgt, opts, type=None, echo=True, message=None, rmmsg=None):
	if type == None:
		ext = src.split('.')[-1]
	
		if ext in cxx_ext_list:
			type = "cxx"
		elif ext in cc_ext_list:
			type = "cc"
		elif ext in asm_ext_list:
			type = "asm"
		else:
			print(glink.util.red("Unrecognized extention"))
			exit(-1)
	if type == "cxx":
		build = glink.make.executor(opts.cxxobjrule, echo, message)
	elif type == "cc":
		build = glink.make.executor(opts.ccobjrule , echo, message)
	elif type == "asm":
		build = glink.make.executor(opts.ccobjrule , echo, message)
	else:
		print(glink.util.red("Unrecognized extention"))
		exit(-1)
	core.targets[tgt] = glink.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		src=src,
		deps=[src],
		build=build,
		clr=glink.make.executor("rm -f {tgt}", echo, rmmsg),  
	)

def executable(tgt, srcs, opts, echo=True, message=None, rmmsg=None):
	core.targets[tgt] = glink.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		build=glink.make.executor(opts.execrule, echo, message),
		clr=glink.make.executor("rm -f {tgt}", echo, rmmsg),  
		srcs=" ".join(srcs),
		deps=srcs
	)