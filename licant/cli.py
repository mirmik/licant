#coding: utf-8

import licant.util
from licant.core import WrongAction

import sys
from optparse import OptionParser

import os


def cli_argv_parse(argv):
	parser = OptionParser()
	parser.add_option("-d", "--debug", action="store_true",
					  default=False, help="print full system commands")
	parser.add_option("-t", "--trace", action="store_true",
					  default=False, help="print trace information")
	parser.add_option("-j", "--threads", default=1,
					  help="amount of threads for executor")
	parser.add_option("-q", "--quite", action="store_true",
					  default=False, help="don`t print shell operations")

	parser.add_option("--printruntime", action="store_true", default=False)

	opts, args = parser.parse_args(argv)
	return opts, args


def execute_with_default_action(target):
	if not hasattr(target, "default_action"):
		licant.util.error("target {} hasn't default_action (actions: {})"
			.format(licant.util.yellow(args[0]), licant.util.get_actions(target)))
	return target.invoke(target.default_action, critical=True)
	

def cliexecute(default, colorwrap=False, argv=sys.argv[1:], core=licant.core.core):
	if colorwrap:
		print(licant.util.green("[start]"))

	opts, args = cli_argv_parse(argv)

	core.runtime["debug"] = opts.debug or opts.trace
	core.runtime["trace"] = opts.trace
	core.runtime["quite"] = opts.quite

	cpu_count = os.cpu_count()
	core.runtime["threads"] = cpu_count if opts.threads == 'j' else int(opts.threads)

	if opts.printruntime:
		print("PRINT RUNTIME:", core.runtime)

	if len(args) == 0:
		if default is None:
			licant.util.error("default target isn't set")

		target = core.get(default)
		execute_with_default_action(target)

	elif len(args) == 1:
		fnd = args[0]
		if fnd in core.targets:
			target = core.get(fnd)
			execute_with_default_action(target)
		else:
			target = core.get(default)
			
			if not target.hasaction(fnd):
				licant.util.error("Can't find routine " + licant.util.yellow(fnd) +
				  ". Enough target or default target's action with same name.")


			target.invoke(fnd, critical=True)
			
	elif len(args) >= 2:
		tgt = args[0]
		act = args[1]
		act_args = args[2:] 

		if core.runtime["debug"]:
			print("licant.ex: tgt:{}, act:{}, args:{}".format(tgt, act, act_args))

		target = licant.core.core.get(tgt)
		
		if not target.hasaction(act):
			licant.util.error("Can't find action " + licant.util.yellow(args[1]) +
				" in target " + licant.util.yellow(args[0]))

		target.invoke(act, *act_args, critical=True)
			
	if colorwrap:
		print(licant.util.yellow("[finish]"))
