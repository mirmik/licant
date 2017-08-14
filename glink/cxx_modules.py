from glink.modules import mlibrary
from glink.cxx_make import host_binutils, binutils
from glink.util import red, yellow


class solver:
	def __init__(self, type, merge, include, default):
		self.type 	 = type
		self.merge	 = merge
		self.include = include
		self.default = default

def base(base, add):
	return base

cxx_module_field_list = {
	"srcdir": solver("str", base, base, "."),
	"sources": solver("list", base, base, []),
	"includePaths": solver("list", base, base, []),
	"cxxstd": solver("str", base, base, "c++11"),
	"ccstd": solver("str", base, base, "c11"),
	"modules": solver("list", base, base, []),
	"type": solver("str", base, base, "application"),
	"builddir": solver("str", base, base, "build"),
	"binutils": solver("binutils", base, base, host_binutils),
	"includeModules": solver("list", base, base, []),
}

class CXXModuleOptions:
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
			if k in other.opts:
				resopts[k] = self.table[k].merge(self.opts[k], other.opts[k])
			else:
				resopts[k] = self.opts[k]

		return CXXModuleOptions(**resopts)
		
	def __init__(self, table=cxx_module_field_list, **kwargs):
		self.opts = kwargs
		self.table = table
		self.check()

def make(name, **kwargs):
	mod = mlibrary.get(name)
	#print("make module {}".format(mod.name))

	opts = CXXModuleOptions(**kwargs)
	opts.set_default_if_empty()

	def modmake(mod, baseopts):
		modopts = CXXModuleOptions(**mod.opts)
		cxxopts = baseopts.merge(modopts)

		print(cxxopts.opts)
		pass

	result = modmake(mod, opts)