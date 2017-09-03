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

host_binutils = binutils(
	cxx= 		"c++",
	cc= 		"cc",
	ld= 		"ld",
	ar= 		"ar",
	objdump= 	"objdump"
)

class options:
	def __init__(self, binutils = host_binutils, include_paths = None, defines = None, cxx_flags="", cc_flags="", ld_flags="", ldscripts = None):
		self.binutils = binutils
		self.incopt = glink.util.flag_prefix("-I", include_paths) 
		self.defopt = glink.util.flag_prefix("-D", defines)
		self.ldscripts = glink.util.flag_prefix("-T", ldscripts) 
		self.cxx_flags = cxx_flags
		self.cc_flags = cc_flags
		self.ld_flags = ld_flags
		self.execrule=  "{opts.binutils.cxx} {srcs} -o {tgt} {opts.ld_flags} {opts.ldscripts}"
		self.cxxobjrule="{opts.binutils.cxx} -c {src} -o {tgt} {opts.incopt} {opts.defopt} {opts.cxx_flags}"
		self.ccobjrule= "{opts.binutils.cc} -c {src} -o {tgt} {opts.incopt} {opts.defopt} {opts.cc_flags}"
	
cxx_ext_list = ["cpp", "cxx"]
cc_ext_list = ["cc", "c"]
asm_ext_list = ["asm", "s", "S"]

def object(src, tgt, opts = options(), type=None, deps=None, message="OBJECT {tgt}"):
	if deps == None:
		deps = [src]

	if type == None:
		ext = os.path.basename(src).split('.')[-1]
	
		if ext in cxx_ext_list:
			type = "cxx"
		elif ext in cc_ext_list:
			type = "cc"
		elif ext in asm_ext_list:
			type = "asm"
		else:
			print("Unrecognized extention: {}".format(glink.util.red(ext)))
			exit(-1)
	if type == "cxx":
		build = glink.make.execute(opts.cxxobjrule)
	elif type == "cc":
		build = glink.make.execute(opts.ccobjrule)
	elif type == "asm":
		build = glink.make.execute(opts.ccobjrule)
	else:
		print(glink.util.red("Unrecognized extention"))
		exit(-1)
	core.targets[tgt] = glink.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		src=src,
		deps=deps,
		build=build,
		message=message
		#clr=glink.make.executor("rm -f {tgt}"),  
	)

def executable(tgt, srcs, opts = options(), message="EXECUTABLE {tgt}"):
	core.targets[tgt] = glink.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		build=glink.make.execute(opts.execrule),
		#clr=glink.make.executor("rm -f {tgt}"),  
		srcs=" ".join(srcs),
		deps=srcs,
		message=message
	)