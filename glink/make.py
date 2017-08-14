from glink.core import Target, core, subtree, get_target
from glink.cache import fcache
from glink.util import red, green, yellow
import os

def execute(target, rule, echo=False, message=None):
	rule = rule.format(**target.__dict__)

	if echo:
		print(rule)
	
	if message:
		print(self.message.format(**target.__dict__))

	ret = os.system(rule)
	return ret

class FileTarget(Target):
	def __init__(self, tgt, deps, **kwargs):
		Target.__init__(self, tgt, deps, **kwargs)
		self.isfile = True
		self.need = True

	def update_info(self, _self):
		fcache.update_info(self.tgt)

	def need_if_timestamp_compare(self, _self):
		curinfo = fcache.get_info(self.tgt)
		curmtime = curinfo.mtime
		if curmtime == None:
			self.need = True
			return 0

		maxmtime = 0
		for dep in [get_target(t) for t in self.depends]:
			if dep.isfile:
				info = fcache.get_info(dep.tgt)
				if info.exist == False:
					return True
				if info.mtime > maxmtime:
					maxmtime = info.mtime

		if maxmtime > curmtime:
			self.need = True
		else:
			self.need = False

		return 0

	def need_if_exist(self, _self):
		curinfo = fcache.get_info(self.tgt)
		if curinfo.exist:
			self.need = True
		else:
			self.need = False

		return 0

class executor:
	def __init__(self, rule, echo=False, message=None):
		self.rule = rule
		self.echo = echo
		self.message = message

	def __call__(self, target):
		return execute(target, self.rule, self.echo, self.message)

def copy(src, tgt, echo=True, message=None, rmmsg=None):
	core.targets[tgt] = FileTarget(
		tgt=tgt, 
		build=executor("cp {src} {tgt}", echo, message),
		clr=executor("rm -f {tgt}", echo, rmmsg),  
		src=src,
		deps=[src]
	)

def file(tgt):
	core.targets[tgt] = FileTarget(
		build=error_if_not_exist,
		tgt=tgt, 
		deps=[]
	)


def directories_keeper(stree):
	depset = stree.depset
	targets = [get_target(t) for t in depset]

	for target in targets:
		if isinstance(target, FileTarget):
			dr = os.path.normpath(os.path.dirname(target.tgt))
			if (not os.path.exists(dr)):
				print("MKDIR %s" % dr)
				os.system("mkdir -p {0}".format(dr))

def print_result_string(ret):
	if ret == 0:
		print(yellow("Nothing to do"))
	else:
		print(green("Success"))

def clean(root):
	stree = subtree(root)
	stree.invoke_foreach(ops = "update_info")
	stree.invoke_foreach(ops = "need_if_exist")
	return stree.invoke_foreach(ops="clr", cond=if_need_or_not_file)

def make(root):
	stree = subtree(root)
	directories_keeper(stree)
	stree.invoke_foreach(ops = "update_info")
	stree.invoke_foreach(ops = "need_if_timestamp_compare")
	stree.reverse_recurse_invoke(ops = need_spawn)
	return stree.reverse_recurse_invoke(ops = "build", cond = if_need_or_not_file)

def if_need_or_not_file(context, target):
	if (not isinstance(target, FileTarget)):
		return True
	else:
		return target.need

def need_spawn(target):
	deptgts = [get_target(t) for t in target.depends]
	for dt in deptgts:
		if dt.need == True:
			target.need = True
			return 

def error_if_not_exist(target):
	info = fcache.get_info(target.tgt)
	if info.exist == False:
		print("Файл не существует:", red(target.tgt))
		exit(-1)