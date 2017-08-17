from glink.util import red 
from glink.scripter import scriptq
import inspect

class ModuleLibrary:
	def __init__(self):
		self.modules = {}

	def register(self, mod):
		if mod.name in self.modules:
			print("Попытка зарегистрировать модуль {0} повторно".format(red(mod.name)))
		else:
			self.modules[mod.name] = mod

	def get(self, name):
		return self.modules[name]

class Module:
	def __init__(self, name, script, **kwargs):
		self.name = name
		self.script = script
		self.opts = kwargs

#class VariantModule(Module):
#	pass

mlibrary = ModuleLibrary()

def module(name, **kwargs):
	mlibrary.register(Module(name, script=scriptq.last(), **kwargs))

#def implementation(name, impl, **kwargs):
#	mlibrary.register_impl(
#		Implementation(name, impl, script=scriptq.last(), **kwargs)
#	)
#	print("impl {0} {1} register")

class submodule:
	def __init__(self, name, addopts = None):
		self.name = name
		self.addopts = addopts