import sys
import inspect

import licant.util
import licant.core

_internal_routines = {}
_routines = {}
_default = None

def routine_decor(func):
	global _routines
	global _default
	_routines[func.__name__] = func
	return func

def default_routine_decor(func):
	_default = func
	return routine_decor(func)	

def cliexecute():
	#print("Licant CliExecute utility")
	opts, args = licant.core.core.parse_argv(sys.argv[1:])

	if len(args) == 0:
		if _default == None:
			licant.util.error("default routine isn't set")
		return do_routine(_default)

	if not sys.argv[0] in _routines:
		licant.util.error("bad routine " + licant.util.yellow(args[0]))

	return do_routine(_routines[args[0]])




def do_routine(func):
	ins = inspect.getargspec(_default)
	nargs = len(ins.args)
	if nargs == 0 : func()
	if nargs == 1 : func(opts)
	if nargs == 2 : func(opts, args)



#def internal_routines(dct):
#	global _internal_routines
#	_internal_routines = dct

#def add_routine(name, func):
#	_routines[name] = func

#def default(name):
#	global _default
#	_default = name

#def invoke(argv, *args, **kwargs):
#	if len(argv) != 0:
#		name = argv[0]
#	else:
#		name = _default

#	func = None

#	if name in _routines:
#		func = _routines[name]
#	elif name in _internal_routines:
#		func = _internal_routines[name]
#	else: 
#		print("Bad routine")
#		sys.exit(-1) 

#	ins = inspect.getargspec(func)
#	nargs = len(ins.args)
#	return func(*args[:nargs]) 

