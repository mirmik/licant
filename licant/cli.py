import licant.util
import licant.core

import sys
from optparse import OptionParser

_default = None

def routine_decorator(*args, **kwargs):
	if len(kwargs) > 0:
		return routine_decorator

	global _routines
	func = args[0]
	deps = getattr(kwargs, "deps", [])
	licant.core.add_target(licant.core.Routine(func, deps = deps))
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
	licant.core.core.runtime["infomod"] = "info" if not opts.debug else "debug"

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