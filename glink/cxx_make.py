import glink.make
import os

class binutils:
	def __init__(self, cxx, cc, ld, ar, objdump):
		self.cc = cc
		self.cxx = cxx
		self.ld = ld
		self.ar = ar
		self.objdump = objdump

cxx_ext_list = ["cpp", "cxx"]
cc_ext_list = ["cc", "c"]
asm_ext_list = ["asm", "s", "S"]

class cxx_make(glink.make.make):
	def __init__(self, binutils, includePaths = None, defines = None, cxx_flags="", cc_flags="", ld_flags=""):
		glink.make.make.__init__(self)
		self.binutils = binutils
		self.incopt = glink.util.flag_prefix("-I", includePaths) 
		self.defopt = glink.util.flag_prefix("-D", defines) 
		self.cxx_flags = cxx_flags
		self.cc_flags = cc_flags
		self.ld_flags = ld_flags
		self.execrule=  "{context.binutils.cxx} {srcs} -o {tgt} {context.ld_flags}"
		self.cxxobjrule="{context.binutils.cxx} -c {src} -o {tgt} {context.incopt} {context.defopt} {context.cxx_flags}"
		self.ccobjrule= "{context.binutils.cc} -c {src} -o {tgt} {context.incopt} {context.defopt} {context.cc_flags}"

	def object(self, src, tgt, type=None, echo=True, message=None, rmmsg=None):
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
			act = glink.make.executor(self.cxxobjrule, echo, message)
		elif type == "cc":
			act = glink.make.executor(self.ccobjrule , echo, message)
		elif type == "asm":
			act = glink.make.executor(self.ccobjrule , echo, message)

		else:
			print(glink.util.red("Unrecognized extention"))
			exit(-1)


		self.core.targets[tgt] = glink.make.file_target(
			context=self,
			tgt=tgt, 
			src=src,
			deps=[src],
			act=act,
			clr=glink.make.executor("rm -f {tgt}", echo, rmmsg),  
		)

	def executable(self, tgt, srcs, echo=True, message=None, rmmsg=None):
		self.core.targets[tgt] = glink.make.file_target(
			context=self,
			tgt=tgt, 
			act=glink.make.executor(self.execrule, echo, message),
			clr=glink.make.executor("rm -f {tgt}", echo, rmmsg),  
			srcs=" ".join(srcs),
			deps=srcs
		)
		
def host_cxx_maker(**kwargs):
	cpp = cxx_make(
		binutils(
			cxx= 		"c++",
			cc= 		"cc",
			ld= 		"ld",
			ar= 		"ar",
			objdump= 	"objdump"
		),
		**kwargs
	)
	return cpp
	
def avr_cxx_maker(**kwargs):
	cpp = cpp_maker(
		binutils(
			cxx= 		"avr-g++",
			cc= 		"avr-gcc",
			ld= 		"avr-ld",
			ar= 		"avr-ar",
			objdump= 	"avr-objdump"
		),
		**kwargs
	)
	return cpp