#coding: utf-8

import licant.util
from licant.core import WrongAction

import sys
from optparse import OptionParser

#_default = None

def routine_decorator(*args, **kwargs):
	if len(kwargs) > 0:
		return routine_decorator

	global _routines
	func = args[0]
	deps = getattr(kwargs, "deps", [])
	licant.core.core.add(licant.core.Routine(func, deps = deps))
	return func

#def default_routine_decorator(func):
#	global _default
#	_default = func.__name__
#	return routine_decorator(func)	

def cli_argv_parse(argv):
	parser = OptionParser()
	parser.add_option("-d", "--debug", action="store_true", default=False, help="print full system commands")
	parser.add_option("-j", "--threads", default=1, help="amount of threads for executor")
	parser.add_option("-t", "--trace", action="store_true", default=False, help="print trace information")
	
	parser.add_option("--printruntime", action="store_true", default=False)
	
	opts, args = parser.parse_args(argv)
	return opts, args

def cliexecute(default, colorwrap = False, argv = sys.argv[1:], core = licant.core.core):
	if colorwrap: print(licant.util.green("[start]"))

	opts, args = cli_argv_parse(argv)

	core.runtime["debug"] = opts.debug or opts.trace
	core.runtime["trace"] = opts.trace
	core.runtime["threads"] = int(opts.threads)

	if opts.printruntime:
		print("PRINT RUNTIME:", core.runtime)
	

	if len(args) == 0:
		if default == None:
			licant.util.error("default target isn't set")

		try:
			target = core.get(default)
			ret = target.invoke(target.default_action, critical = True)
		except licant.core.WrongAction as e:
			print(e)
			licant.util.error("Enough default action " + licant.util.yellow(target.default_action) + " in default target " + licant.util.yellow(_default))
			
	
	if len(args) == 1:
		fnd = args[0]
		if fnd in core.targets:
			try:
				target = core.get(fnd)
				ret = target.invoke(target.default_action, critical = True)
			except licant.core.WrongAction as e:
				print(e)
				licant.util.error("target.default_action")
		else:
			try:
				target = core.get(default)
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
	
	
	if colorwrap: print(licant.util.yellow("[finish]"))