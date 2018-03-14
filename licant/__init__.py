from licant.cli import cliexecute as ex
from licant.cli import default_routine_decorator as default_routine
from licant.cli import routine_decorator as routine

from licant.core import do as do
from licant.core import add_target as add_target 

from licant.make import add_makefile_target as add_makefile_target 

def about():
	return "I'm Licant"