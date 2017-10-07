from licant.util import red 
from licant.scripter import scriptq
import inspect

#from slots import *

special = ["__script__", "__dir__"]

class Module:
	#__slots__ = ['name', 'script', 'stack', 'opts']
	def __init__(self, name, script, dir, stack, **kwargs):
		self.name = name
		self.script = script
		self.stack = stack
		self.opts = kwargs
		self.opts["__script__"]=self.script
		self.opts["__dir__"]=dir
	#	self.set_up()

class VariantModule:
	def __init__(self):
		self.impls = {}

	def addimpl(self, impl, mod):
		self.impls[impl] = mod

class ModuleLibrary:
	def __init__(self):
		self.modules = {}

	def register(self, mod):
		if mod.name in self.modules:
			print("Attempt to register the module {} again".format(red(mod.name)))
			exit(-1)
		else:
			self.modules[mod.name] = mod

	def register_impl(self, mod, impl):
		if mod.name in self.modules:
			if not isinstance(self.modules[mod.name], VariantModule):
				print("Attempt to register the module {} again".format(red(mod.name)))
				exit(-1)
			else:
				varmod = self.modules[mod.name]
		else:
			varmod = VariantModule()
			self.modules[mod.name] = varmod

		varmod.addimpl(impl, mod)		

	def get(self, name, impl=None):
		if not name in self.modules:
			print("The missing module {} was requested".format(red(name)))
			exit(-1)
				 
		m = self.modules[name]
		if impl == None:
			if isinstance(m, VariantModule):
				print("Need implementation: {}".format(red(name)))
				exit(-1)
			else:
				return m
		else:
			if isinstance(m, Module):
				print("This modile have only one implementation: {}".format(red(name)))
				exit(-1)
			else:
				if impl in m.impls:
					return m.impls[impl]
				else:
					print("Unregistred implementation: {}".format(red(impl)))
					exit(-1)
		

mlibrary = ModuleLibrary()

def module(name, impl=None, **kwargs):
	if impl != None:
		implementation(name, impl, **kwargs)
		return
	mlibrary.register(Module(name, script=scriptq.last(), dir=scriptq.curdir(), stack=list(scriptq.stack), **kwargs))

def implementation(name, impl, **kwargs):
	mlibrary.register_impl(Module(name, script=scriptq.last(), dir=scriptq.curdir(), stack=list(scriptq.stack), **kwargs), impl=impl)

class submodule:
	def __init__(self, name, impl=None, addopts = None):
		self.name = name
		self.impl = impl
		self.addopts = addopts

	def __repr__(self):
		return "subm(" + self.name + ")"