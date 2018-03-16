import licant.util
import licant.core

import sys
from optparse import OptionParser

_default = None

def routine_decorator(func):
	global _routines
	licant.core.add_target(licant.core.Routine(func))
	return func

def default_routine_decorator(func):
	global _default
	_default = func.__name__
	return routine_decorator(func)	

def cli_argv_parse(argv):
	parser = OptionParser()
	parser.add_option("-d", "--debug", action="store_true", default=False, 
		help="print full system commands")
	parser.add_option("-j", "--threads", default=1, help="amount of threads for executor")
	opts, args = parser.parse_args(argv)
	return opts, args

def cliexecute(argv = sys.argv[1:], default = None):
	print(licant.util.green("[start]"))

	if default != None:
		global _default 
		_default = default
	opts, args = cli_argv_parse(argv)
	licant.core.core.runtime["threads"] = int(opts.threads)

	if len(args) == 0:
		if _default == None:
			licant.util.error("default target isn't set")

		try:
			target = licant.core.get_target(_default)
			ret = target.invoke(target.default_action, critical = True)
		except licant.core.WrongAction as e:
			print(e)
			licant.util.error("Enough default action " + licant.util.yellow(target.default_action) + " in default target " + licant.util.yellow(_default))
			
	
	if len(args) == 1:
		fnd = args[0]
		if fnd in licant.core.core.targets:
			try:
				target = licant.core.get_target(fnd)
				ret = target.invoke(target.default_action, critical = True)
			except licant.core.WrongAction as e:
				print(e)
				licant.util.error("target.default_action")
		else:
			try:
				target = licant.core.get_target(_default)
				ret = target.invoke(fnd, critical = True)
			except licant.core.WrongAction as e:
				print(e)
				licant.util.error("Can't find routine " + licant.util.yellow(fnd) + 
					". Enough target or default target action with same name.")
	
	if len(args) == 2:
		try:
			target = licant.core.get_target(args[0])
			ret = target.invoke(args[1], critical = True)
		except licant.core.WrongAction as e:
				print(e)
				licant.util.error("Can't find action " + licant.util.yellow(args[1]) + 
					" in target " + licant.util.yellow(args[0]))
	
	
	print(licant.util.yellow("[finish]"))


		#return target

	#return target

		#return do_routine(_default)

	#if not args[0] in _routines:
	#	licant.util.error("bad routine " + licant.util.yellow(args[0]))

	#return do_routine(_routines[args[0]])

#def do_routine(func):
#	ins = inspect.getargspec(_default)
#	nargs = len(ins.args)
#	if nargs == 0 : func()
#	if nargs == 1 : func(opts)
#	if nargs == 2 : func(opts, args)



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

