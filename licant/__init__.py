from licant.core import Core, Target
from licant.core import core as default_core

from licant.cli import cliexecute as ex
from licant.cli import routine_decorator as routine

from licant.core import do as do
#from licant.core import add_target as add_target 

from licant.make import add_makefile_target as add_makefile_target 

def execute(path):
	licant.scripter.scriptq.execute(path)

def execute_recursive(*argv, **kwargs):
	licant.scripter.scriptq.execute(*argv, **kwargs)

def about():
	return "I'm Licant"