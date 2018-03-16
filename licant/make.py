from __future__ import print_function 

import licant
from licant.core import Target, core, subtree, get_target
from licant.cache import fcache
from licant.util import red, green, yellow, purple, quite
import threading
import os
import sys

_rlock = threading.RLock()
	
def do_execute(target, rule, msgfield, prefix = None):
	def sprint(*args, **kwargs):
		with _rlock:
			print(*args, **kwargs) 

	rule = rule.format(**target.__dict__)

	message = getattr(target, msgfield, None)

	if core.runtime["infomod"] == 'info' and message != None:
		if not isinstance(message, quite):
			if prefix != None:
				sprint(prefix, message.format(**target.__dict__))
			else:
				sprint(message.format(**target.__dict__))
	else:
		sprint(rule)
	
	ret = os.system(rule)
	return True if ret == 0 else False 

class MakeFileTarget(Target):
	def __init__(self, tgt, deps, **kwargs):
		Target.__init__(self, tgt, deps, **kwargs)

	def clean(self, _self):	
		stree = subtree(self.tgt)
		stree.invoke_foreach(ops = "need_if_exist")
		return stree.invoke_foreach(ops="clr", cond=if_need_and_file)

	def makefile(self, _self):
		stree = subtree(self.tgt)
		if stree.invoke_foreach(ops = "dirkeep") == False: return False
		if stree.reverse_recurse_invoke(ops = "build_if_need", threads = core.runtime["threads"]) == False: return False

		

class FileTarget(MakeFileTarget):
	def __init__(self, tgt, deps, **kwargs):
		MakeFileTarget.__init__(self, tgt, deps, **kwargs)
		self.isfile = True
		#self.need = True
		self.clrmsg = "DELETE {tgt}"
		self.default_action = "makefile"

	def update_info(self, _self):
		fcache.update_info(self.tgt)

	def timestamp(self, _self):
		curinfo = fcache.get_info(self.tgt)

		if curinfo.exist == False:
			self.tstamp = 0
		else:	
			self.tstamp = curinfo.mtime
	
	def mtime(self):
		curinfo = fcache.get_info(self.tgt)
		if curinfo.exist == False:
			return 0
		else:	
			return curinfo.mtime
	
	def dirkeep(self, _self):
		dr = os.path.normpath(os.path.dirname(self.tgt))
		if (not os.path.exists(dr)):
			print("MKDIR %s" % dr)
			os.system("mkdir -p {0}".format(dr))
		return True

	def is_exist(self):
		curinfo = fcache.get_info(self.tgt)
		return curinfo.exist

	def need_if_exist(self, _self):
		curinfo = fcache.get_info(self.tgt)
		if curinfo.exist:
			self.need = True
		else:
			self.need = False

		return 0

	def clr(self, _self):
		do_execute(self, "rm -f {tgt}", "clrmsg")


	def build_if_need(self, _self):
		maxtime = 0
		force = False
		
		for dep in [get_target(t) for t in self.depends]:
			if not dep.is_exist():
				force = True
				break
			if dep.mtime() > maxtime:
				maxtime = dep.mtime()
	
		if maxtime > self.mtime() or force:
			return self.build(self)
		return True
		


	

def ftarget(tgt, deps=[], **kwargs):
	core.add_target(FileTarget(
		tgt=tgt, 
		deps=deps,
		**kwargs
	))

class Executor:
	def __init__(self, rule, msgfield='message'):
		self.rule = rule
		self.msgfield = msgfield
		
	def __call__(self, target, **kwargs):
		return do_execute(target, self.rule, self.msgfield, **kwargs)

def execute(*args, **kwargs):
	return Executor(*args, **kwargs)

def copy(tgt, src, adddeps=[], message="COPY {src} {tgt}"):
	core.add_target(FileTarget(
		tgt=tgt, 
		build=execute("cp {src} {tgt}"),
		src=src,
		deps=[src] + adddeps,
		message=message
	))

def source(tgt, deps=[]):
	target = FileTarget(
		build=warn_if_not_exist,
		deps=deps,
		tgt=tgt, 
	)
	target.clr = None
	target.dirkeep = None
	core.targets[tgt] = target

def print_result_string(ret):
	if ret == 0:
		print(yellow("Nothing to do"))
	else:
		print(green("Success"))

def if_need(context, target):
	return target.need

def files_only(context, target):
	return isinstance(target, FileTarget)

def if_need_and_file(context, target):
	need = getattr(target, "need", None)
	if need == None:
		return False
	return need and isinstance(target, FileTarget)

def need_spawn(target):
	deptgts = [get_target(t) for t in target.depends]
	for dt in deptgts:
		if dt.need == True:
			target.need = True
			return 0 
	target.need = getattr(target, "need", False)
		
def set_need(target):
	target.need = True

def warn_if_not_exist(target):
	info = fcache.get_info(target.tgt)
	if info.exist == False:
		print("Warn: file {} isn`t exist".format(purple(target.tgt)))
		#raise Exception("File  isn't exist")

def error_if_not_exist(target):
	info = fcache.get_info(target.tgt)
	if info.exist == False:
		print("File isn't exist:", red(target.tgt))
		raise Exception("File  isn't exist")

def do_function(target):
	target.func(*target.args, **target.kwargs)

def function(tgt, func, deps=[], args=[], kwargs={}):
	core.targets[tgt] = Target(
		tgt=tgt,
		build=do_function,
		func=func,
		deps=deps,
		args=args,
		kwargs=kwargs, 
		timestamp=timestamp_max_of_depends
	)

def timestamp_max_of_depends(target):
	maxtime = 0
	for dep in [get_target(t) for t in target.depends]:
		if dep.tstamp > maxtime:
			maxtime = dep.tstamp
	target.tstamp = maxtime	

def need_if_timestamp_compare(target):
	if target.tstamp == 0:
		target.need = True
		return 0

	maxtime = 0
	force = False
	for dep in [get_target(t) for t in target.depends]:
		if not dep.is_exist():
			force = True
			break
		if dep.tstamp > maxtime:
			maxtime = dep.tstamp
	
	if maxtime > target.tstamp or force:
		target.need = True
	else:
		target.need = False

	return 0

class VirtualMakeFileTarget(MakeFileTarget):
	def __init__(self, tgt, targets):
		MakeFileTarget.__init__(self, tgt = tgt, deps = targets,
			default_action = "makefile"
		)

def add_makefile_target(tgt, targets):
	licant.add_target(VirtualMakeFileTarget(tgt = tgt, targets = targets)) 


#import licant.routine
#def doit(target, argv=sys.argv[1:]):
#	opts, args = core.parse_argv(argv)
#	core.runtime["threads"] = int(opts.threads)
#
#	if opts.debug:
#		core.runtime["infomod"] = "debug"
#
#	licant.routine.internal_routines({"make" : makefile, "clean" : clean})
#	licant.routine.default("make")
#
#	result = licant.routine.invoke(args, target)
#
#	print_result_string(result)