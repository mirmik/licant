import sys
import inspect

_internal_routines = {}
_routines = {}
_default = None

def internal_routines(dct):
	global _internal_routines
	_internal_routines = dct

def add_routine(name, func):
	_routines[name] = func

def default(name):
	global _default
	_default = name

def invoke(argv, *args, **kwargs):
	if len(argv) != 0:
		name = argv[0]
	else:
		name = _default

	func = None

	if name in _routines:
		func = _routines[name]
	elif name in _internal_routines:
		func = _internal_routines[name]
	else: 
		print("Bad routine")
		sys.exit(-1) 

	ins = inspect.getargspec(func)
	nargs = len(ins.args)
	return func(*args[:nargs]) 

