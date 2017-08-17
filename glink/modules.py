from glink.util import red 
from glink.scripter import scriptq
import inspect

class Module:
	def __init__(self, name, script, stack, **kwargs):
		self.name = name
		self.script = script
		self.stack = stack
		self.opts = kwargs

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
			print("Попытка зарегистрировать модуль {0} повторно".format(red(mod.name)))
			exit(-1)
		else:
			self.modules[mod.name] = mod

	def register_impl(self, mod, impl):
		if mod.name in self.modules:
			if not isinstance(self.modules[mod.name], VariantModule):
				print("Попытка зарегистрировать модуль {0} повторно".format(red(mod.name)))
				exit(-1)
			else:
				varmod = self.modules[mod.name]
		else:
			varmod = VariantModule()
			self.modules[mod.name] = varmod

		varmod.addimpl(impl, mod)		

	def get(self, name, impl=None):
		m = self.modules[name]
		if impl == None:
			if isinstance(m, VariantModule):
				print("Требуется уточнение реализации: {}".format(red(name)))
				exit(-1)
			else:
				return m
		else:
			if isinstance(m, Module):
				print("У этого модуля только одна реализации: {}".format(red(name)))
				exit(-1)
			else:
				if impl in m.impls:
					return m.impls[impl]
				else:
					print("Несуществующая реализации: {}".format(red(impl)))
					exit(-1)
		

mlibrary = ModuleLibrary()

def module(name, **kwargs):
	mlibrary.register(Module(name, script=scriptq.last(), stack=list(scriptq.stack), **kwargs))

def implementation(name, impl, **kwargs):
	mlibrary.register_impl(Module(name, script=scriptq.last(), stack=list(scriptq.stack), **kwargs), impl=impl)

class submodule:
	def __init__(self, name, impl=None, addopts = None):
		self.name = name
		self.impl = impl
		self.addopts = addopts