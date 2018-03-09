import licant.util
import threading
import sys
import time
from optparse import OptionParser

class licantCore:
	def __init__(self):
		self.targets = {}
		self.runtime = { 'infomod': "info" }
		self.glbopts = {}

	def parse_argv(self, argv=sys.argv[1:]):
		parser = OptionParser()
		parser.add_option("-d", "--debug", action="store_true", default=False, 
			help="print full system commands")
		parser.add_option("-j", "--threads", default=1, help="amount of threads for executor")
		opts = parser.parse_args(argv)
		return opts

	def add_target(self, tgt, deps=[], **kwargs):
		self.targets[tgt] = Target(tgt=tgt, deps=deps, **kwargs)

	def subtree(self, root):
		return SubTree(self, root)

	def get_target(self, tgt):
		if tgt in self.targets:
			return self.targets[tgt]
		print("Unregistred target: {0}".format(tgt))
		exit(-1)
	
	def depends_as_set(self, tgt, incroot=True):
		res = set()
		if incroot:
			res.add(tgt)
		
		target = self.get_target(tgt)
		
		for d in target.depends:
			if not d in res:
				res.add(d)
				subres = self.depends_as_set(d)
				res = res.union(subres)
		return res

core = licantCore()

class Target:
	def __init__(self, tgt, deps, **kwargs):
		#print("deps", tgt, deps)
		self.depends = set()
		self.tgt = tgt

		for d in deps:
			self.depends.add(d)
		
		for k, v in kwargs.items():
			setattr(self, k, v)

		self.deps = self.depends

	def invoke(self, func, **kwargs):
		if (isinstance(func, str)):
			res = getattr(self, func, None)
			if (res == None):
				return None
			ret = res(self, **kwargs)
			return ret
		else:
			return func(self, **kwargs)

	def __repr__(self):
		return self.tgt

def target(tgt, deps=[], **kwargs):
	core.targets[tgt] = Target(tgt=tgt, deps=deps, **kwargs)

def get_target(tgt):
	if tgt in core.targets:
		return core.targets[tgt]
	print("Unregistred target: {0}".format(tgt))
	exit(-1)

def depends_as_set(tgt, incroot=True):
	res = set()
	if incroot:
		res.add(tgt)
	
	target = get_target(tgt)
	
	for d in target.depends:
		if not d in res:
			res.add(d)
			subres = depends_as_set(d)
			res = res.union(subres)
	return res

def invoke_foreach(func):
	save = dict(core.targets)
	for k, v in save.items():
		v.invoke(func)

class SubTree:
	def __init__(self, core, root):
		self.root = root
		self.core = core
		self.depset = core.depends_as_set(root)

	def update(self):
		SubTree.__init__(self, root)

	def invoke_foreach(self, ops, cond=None):
		sum = 0
		ret = None

		for d in self.depset:
			target = self.core.get_target(d)
			if cond==None:
				ret = target.invoke(ops)
			else:
				if cond(self, target):
					ret = target.invoke(ops)
			
			if ret != None:
				sum+=1
	
		return sum	

	def __generate_rdepends_lists(self, targets):
		for t in targets:
			t.rdepends = []
			t.rcounter = 0
	
		for t in targets:
			for dname in t.depends:
				dtarget = self.core.get_target(dname)
				dtarget.rdepends.append(t.tgt)
	
	
	def reverse_recurse_invoke_single(self, ops, threads=None, cond=licant.util.always_true):
		targets = [self.core.get_target(t) for t in self.depset]
		sum = 0
	
		self.__generate_rdepends_lists(targets)
		
		works = licant.util.queue()
	
		for t in targets:
			if t.rcounter == len(t.depends):
				works.put(t)

		while(not works.empty()):
			w = works.get()
	
			if cond(self, w):
				ret = w.invoke(ops)
				if not (ret == 0 or ret == None):
					print(licant.util.red("runtime error"))
					exit(-1)
				if ret == 0:
					sum += 1
	
			for r in [self.core.get_target(t) for t in w.rdepends]:
				r.rcounter = r.rcounter + 1
				if r.rcounter == len(r.depends):
					works.put(r)
	
		return sum

	def reverse_recurse_invoke_threads(self, ops, threads, cond=licant.util.always_true):
		targets = [self.core.get_target(t) for t in self.depset]
		
		self.__generate_rdepends_lists(targets)
		works = licant.util.queue()
		
		class info_cls:
			def __init__(self):
				self.have_done = 0
				self.need_done = len(targets)
				self.sum = 0
				self.err = False
		info = info_cls()

		for t in targets:
			if t.rcounter == len(t.depends):
				works.put(t)
	
		lock = threading.Lock()
		def thread_func(index):
			while info.have_done != info.need_done:
				if info.err:
					break

				lock.acquire()
				if not works.empty():
					w = works.get()
					lock.release()

					if cond(self, w):
						try:
							ret = w.invoke(ops)
						except:
							info.err = True
							return
						if not (ret == 0 or ret == None):
							info.err = True
							return
						if ret == 0:
							info.sum += 1

					for r in [get_target(t) for t in w.rdepends]:
						r.rcounter = r.rcounter + 1
						if r.rcounter == len(r.depends):
							works.put(r)

					info.have_done += 1
					continue
				lock.release()
				#time.sleep(0.01) 


		threads_list = [threading.Thread(target = thread_func, args = (i,)) for i in range(0, threads)]	
		for t in threads_list:
			t.start()

		for t in threads_list:
			t.join()

		if info.err:
			print(licant.util.red("runtime error"))
			exit(-1)	
		return info.sum

	def reverse_recurse_invoke(self, *args, **kwargs):
		if "threads" in kwargs:
			if kwargs["threads"] == 1:
				return self.reverse_recurse_invoke_single(*args, **kwargs)
			else:
				return self.reverse_recurse_invoke_threads(*args, **kwargs)
		else:
			return self.reverse_recurse_invoke_single(*args, **kwargs)

	def __str__(self):
		ret = ""
		for d in sorted(self.depset):
			t = self.core.get_target(d)
			s = "{}: {}\n".format(d, sorted(t.deps))
			ret += s
		ret = ret[:-1]
		return ret

def subtree(root):
	return SubTree(core, root)