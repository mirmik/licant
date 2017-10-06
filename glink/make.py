from glink.core import Target, core, subtree, get_target
from glink.cache import fcache
from glink.util import red, green, yellow, quite
import os
import sys

def do_execute(target, rule, msgfield, prefix = None):
	rule = rule.format(**target.__dict__)

	message = getattr(target, msgfield, None)
	if core.runtime["infomod"] == 'info' and message != None:
		if not isinstance(message, quite):
			if prefix != None:
				print(prefix, message.format(**target.__dict__))
			else:
				print(message.format(**target.__dict__))
	else:
		print(rule)
	
	
	ret = os.system(rule)
	return ret

class FileTarget(Target):
	def __init__(self, tgt, deps, **kwargs):
		Target.__init__(self, tgt, deps, **kwargs)
		self.isfile = True
		self.need = True
		self.clrmsg = "DELETE {tgt}"

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

	def need_if_exist(self, _self):
		curinfo = fcache.get_info(self.tgt)
		if curinfo.exist:
			self.need = True
		else:
			self.need = False

		return 0

	def clr(self, _self):
		do_execute(self, "rm -f {tgt}", "clrmsg")

def ftarget(tgt, deps=[], **kwargs):
	core.targets[tgt] = FileTarget(
		tgt=tgt, 
		deps=deps,
		**kwargs
	)

class Executor:
	def __init__(self, rule, msgfield='message'):
		self.rule = rule
		self.msgfield = msgfield
		
	def __call__(self, target, **kwargs):
		return do_execute(target, self.rule, self.msgfield, **kwargs)

def execute(*args, **kwargs):
	return Executor(*args, **kwargs)

def copy(src, tgt, adddeps=[], message="COPY {src} {tgt}"):
	core.targets[tgt] = FileTarget(
		tgt=tgt, 
		build=execute("cp {src} {tgt}"),
		src=src,
		deps=[src] + adddeps,
		message=message
	)

def source(tgt, deps=[]):
	target = FileTarget(
		build=error_if_not_exist,
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

def clean(root):	
	stree = subtree(root)
	stree.invoke_foreach(ops = "update_info")
	stree.invoke_foreach(ops = "need_if_exist")
	return stree.invoke_foreach(ops="clr", cond=if_need_and_file)

def make(root, rebuild = False, threads = 1):
	stree = subtree(root)

	#Создать директории, если они не существуют
	stree.invoke_foreach(ops = "dirkeep")
	
	#Считать в кэш информацию о файлах
	stree.invoke_foreach(ops = "update_info")
	
	#Установить каждому файлу время его последнего изменения
	stree.reverse_recurse_invoke(ops = "timestamp")
	
	if not rebuild:
		#Операция вычисления устаревших файлов
		stree.invoke_foreach(ops = need_if_timestamp_compare, cond = files_only)
		stree.reverse_recurse_invoke(ops = need_spawn)
	else:
		#Если установлина опция rebuild, все файлы помечаются для сборки
		stree.invoke_foreach(ops = set_need)

	#Непосредственно операция всех файлов, имеющих метку need 
	ret = stree.reverse_recurse_invoke(ops = "build", cond = if_need, threads = threads)
	
	#Возвращает информацию о том, сколько файлов было пересобрано
	return ret

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
		raise Exception("Файл не существует")

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
	for dep in [get_target(t) for t in target.depends]:
		if dep.tstamp > maxtime:
			maxtime = dep.tstamp
	
	if maxtime > target.tstamp:
		target.need = True
	else:
		target.need = False

	return 0

def doit(target, argv=sys.argv[1:]):
	opts, args = core.parse_argv(argv)

	if opts.debug:
		core.runtime["infomod"] = "debug"

	if len(args) == 0:
		result = make(target, threads = int(opts.threads))
	else:
		if args[0] == "clean":
			result = clean(target)
		else:
			print("Плохая рутина")
			sys.exit(-1)

	print_result_string(result)