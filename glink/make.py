from glink.core import Target, core, subtree, get_target
from glink.cache import fcache
from glink.util import red, green, yellow
import os

def do_execute(target, rule):
	rule = rule.format(**target.__dict__)

	if core.runtime["echo"]:
		print(rule)
	
	#if message:
	#	print(message.format(**target.__dict__))

	ret = os.system(rule)
	return ret

class FileTarget(Target):
	def __init__(self, tgt, deps, **kwargs):
		Target.__init__(self, tgt, deps, **kwargs)
		self.isfile = True
		self.need = True

	def update_info(self, _self):
		fcache.update_info(self.tgt)
	

	def timestamp(self, _self):
		curinfo = fcache.get_info(self.tgt)

		if curinfo.exist == False:
			self.tstamp = 0
		else:	
			self.tstamp = curinfo.mtime
	

	def dirkeep(self, _self):
		dr = os.path.normpath(os.path.dirname(self.tgt))
		if (not os.path.exists(dr)):
			print("MKDIR %s" % dr)
			os.system("mkdir -p {0}".format(dr))

	#def need_if_timestamp_compare(self, _self):
	#	curinfo = fcache.get_info(self.tgt)
	#	curmtime = curinfo.mtime
	#	if curmtime == None:
	#		self.need = True
	#		return 0
#
	#	maxmtime = 0
	#	for dep in [get_target(t) for t in self.depends]:
	#		if dep.isfile:
	#			info = fcache.get_info(dep.tgt)
	#			if info.exist == False:
	#				return True
	#			if info.mtime > maxmtime:
	#				maxmtime = info.mtime
#
	#	if maxmtime > curmtime:
	#		self.need = True
	#	else:
	#		self.need = False
#
	#	return 0

	def need_if_exist(self, _self):
		curinfo = fcache.get_info(self.tgt)
		if curinfo.exist:
			self.need = True
		else:
			self.need = False

		return 0

	def clr(self, _self):
		do_execute(self, "rm -f {tgt}")

def ftarget(tgt, deps=[], **kwargs):
	core.targets[tgt] = FileTarget(
		tgt=tgt, 
		deps=deps,
		**kwargs
	)

class Executor:
	def __init__(self, rule):
		self.rule = rule

	def __call__(self, target):
		return do_execute(target, self.rule)

def execute(*args, **kwargs):
	return Executor(*args, **kwargs)

def copy(src, tgt):
	core.targets[tgt] = FileTarget(
		tgt=tgt, 
		build=execute("cp {src} {tgt}"),
		src=src,
		deps=[src]
	)

def source(tgt):
	target = FileTarget(
		build=error_if_not_exist,
		tgt=tgt, 
		deps=[],		
	)
	target.clr = None
	target.dirkeep = None
	core.targets[tgt] = target

def print_result_string(ret):
	if ret == 0:
		print(yellow("Nothing to do"))
	else:
		print(green("Success"))

def clean(root, echo=True):
	core.runtime["echo"] = echo
	#core.runtime["debug"] = debug
	
	stree = subtree(root)
	stree.invoke_foreach(ops = "update_info")
	stree.invoke_foreach(ops = "need_if_exist")
	return stree.invoke_foreach(ops="clr", cond=if_need_and_file)

def make(root, rebuild = False, echo=True):
	core.runtime["echo"] = echo
	#core.runtime["debug"] = debug
	stree = subtree(root)
	#directories_keeper(stree)
	stree.invoke_foreach(ops = "dirkeep")
	stree.invoke_foreach(ops = "update_info")
	stree.reverse_recurse_invoke(ops = "timestamp")
	
	if not rebuild:
		stree.invoke_foreach(ops = need_if_timestamp_compare, cond = files_only)
		stree.reverse_recurse_invoke(ops = need_spawn)
	else:
		stree.invoke_foreach(ops = set_need)
	return stree.reverse_recurse_invoke(ops = "build", cond = if_need)

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

def error_if_not_exist(target):
	info = fcache.get_info(target.tgt)
	if info.exist == False:
		print("Файл не существует:", red(target.tgt))
		exit(-1)



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
	#print("{}::need_if_timestamp_compare {}".format(target.tgt, getattr(target, "tstamp", 0)))
	#curtime = getattr(target, "timestamp", None)
	if target.tstamp == 0:
		#print("\tresult: need=True")
		target.need = True
		return 0

	maxtime = 0
	for dep in [get_target(t) for t in target.depends]:
		if dep.tstamp > maxtime:
			maxtime = dep.tstamp
	
	if maxtime > target.tstamp:
		#print("\tresult: need=True")
		target.need = True
	else:
		#print("\tresult: need=False")
		target.need = False

	return 0
