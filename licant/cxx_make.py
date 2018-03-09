from licant.core import core
import licant.make
import os

class binutils:
	def __init__(self, cxx, cc, ld, ar, objdump, moc):
		self.cc = cc
		self.cxx = cxx
		self.ld = ld
		self.ar = ar
		self.objdump = objdump
		self.moc = moc

	def __repr__(self):
		return str(self.__dict__)

host_binutils = binutils(
	cxx= 		"c++",
	cc= 		"cc",
	ld= 		"ld",
	ar= 		"ar",
	objdump= 	"objdump",
	moc= 		"moc" #Qt support
)

class options:
	def __init__(self, binutils = host_binutils, include_paths = None, defines = None, cxx_flags="", cc_flags="", ld_flags="", ldscripts = None):
		self.binutils = binutils
		self.incopt = licant.util.flag_prefix("-I", include_paths) 
		self.defopt = licant.util.flag_prefix("-D", defines)
		self.ldscripts = licant.util.flag_prefix("-T", ldscripts) 
		self.cxx_flags = cxx_flags
		self.cc_flags = cc_flags
		self.ld_flags = ld_flags
		self.execrule=  "{opts.binutils.cxx} {srcs} -o {tgt} {opts.ld_flags} {opts.ldscripts}"
		self.dynlibrule= "{opts.binutils.cxx} --shared {srcs} -o {tgt} {opts.ld_flags} {opts.ldscripts}"
		self.cxxobjrule="{opts.binutils.cxx} -c {src} -o {tgt} {opts.incopt} {opts.defopt} {opts.cxx_flags}"
		self.ccobjrule= "{opts.binutils.cc} -c {src} -o {tgt} {opts.incopt} {opts.defopt} {opts.cc_flags}"
		
		self.cxxdeprule="{opts.binutils.cxx} -MM {src} > {tgt} {opts.incopt} {opts.defopt} {opts.cxx_flags}"
		self.ccdeprule= "{opts.binutils.cc} -MM {src} > {tgt} {opts.incopt} {opts.defopt} {opts.cc_flags}"
		self.mocrule="{opts.binutils.moc} {src} > {tgt}"
		
#		cc_rule = "%CC% -o %tgt% -c %src% %__options__%",
#		s_rule = "%CC% -o %tgt% -c %src% %__options__%",
#		cxx_dep_rule = "%CXX% -MM %src% > %tgt% %__options__%",
#		cc_dep_rule = "%CC% -MM %src% > %tgt% %__options__%",

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
			print("Unrecognized extention: {}".format(licant.util.red(ext)))
			exit(-1)
	if type == "cxx":
		build = licant.make.execute(opts.cxxobjrule)
	elif type == "cc":
		build = licant.make.execute(opts.ccobjrule)
	elif type == "asm":
		build = licant.make.execute(opts.ccobjrule)
	else:
		print(licant.util.red("Unrecognized extention"))
		exit(-1)
	core.targets[tgt] = licant.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		src=src,
		deps=deps,
		build=build,
		message=message
		#clr=licant.make.executor("rm -f {tgt}"),  
	)

def moc(src, tgt, opts = options(), type=None, deps=None, message="MOC {tgt}"):
	if deps == None:
		deps = [src]

	core.targets[tgt] = licant.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		src=src,
		deps=deps,
		build=licant.make.execute(opts.mocrule),
		message=message
		#clr=licant.make.executor("rm -f {tgt}"),  
	)

def depend(src, tgt, opts = options(), type=None, deps=None, message="DEPENDS {tgt}"):
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
			print("Unrecognized extention: {}".format(licant.util.red(ext)))
			exit(-1)
	if type == "cxx":
		build = licant.make.execute(opts.cxxdeprule)
	elif type == "cc":
		build = licant.make.execute(opts.ccdeprule)
	elif type == "asm":
		build = licant.make.execute(opts.ccdeprule)
	else:
		print(licant.util.red("Unrecognized extention"))
		exit(-1)
	core.targets[tgt] = licant.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		src=src,
		deps=deps,
		build=build,
		message=message
		#clr=licant.make.executor("rm -f {tgt}"),  
	)

def executable(tgt, srcs, opts = options(), message="EXECUTABLE {tgt}"):
	core.targets[tgt] = licant.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		build=licant.make.execute(opts.execrule),
		#clr=licant.make.executor("rm -f {tgt}"),  
		srcs=" ".join(srcs),
		deps=srcs,
		message=message
	)

def dynamic_library(tgt, srcs, opts = options(), message="DYNLIB {tgt}"):
	core.targets[tgt] = licant.make.FileTarget(
		opts=opts,
		tgt=tgt, 
		build=licant.make.execute(opts.dynlibrule),
		#clr=licant.make.executor("rm -f {tgt}"),  
		srcs=" ".join(srcs),
		deps=srcs,
		message=message
	)

#utils
def make_gcc_binutils(pref):
	return binutils(
	cxx= 		pref + "-g++",
	cc= 		pref + "-gcc",
	ld= 		pref + "-ld",
	ar= 		pref + "-ar",
	objdump= 	pref + "-objdump"
)