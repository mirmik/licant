#coding: utf-8

import licant.util
import threading
import time

class WrongAction(Exception): pass

class NoneDictionary(dict):
	def __init__(self): dict.__init__(self)
	def __getitem__(self, idx): 
		try: return dict.__getitem__(self, idx)
		except: return None 

class Target:
	def __init__(self, tgt, deps, **kwargs):
		self.tgt = tgt
		self.deps = set(deps)
		for k, v in kwargs.items(): setattr(self, k, v)
		
	def invoke(self, func, critical = False, **kwargs):
		"""Invoke func function or method, or mthod with func name for this target

		Поддерживается несколько разных типов func.
		В качестве func может быть вызвана внешняя функция с параметром текущей цели,
		или название локального метода.
		critical -- Действует для строкового вызова. Если данный attr отсутствует у цели,
		то в зависимости от данного параметра может быть возвращен None или выброшено исключение.
		"""
		if core.runtime["trace"]:
			print("TRACE: invoke {} with action {}".format(self.tgt, func))

		if (isinstance(func, str)):
			func = getattr(self, func, None)
			if (func == None):
				if (critical): raise WrongAction(func)
				return None
		
		return licant.util.cutinvoke(func, self, **kwargs)

	def __repr__(self):
		"""По умолчанию вывод Target на печать возвращает идентификатор цели"""
		return self.tgt

class Routine(Target):
	def __init__(self, func, deps=[], tgt = None, **kwargs):
		if tgt == None: tgt = func.__name__
		Target.__init__(self, tgt = tgt, deps = deps, func = func, 
			default_action = func, **kwargs
		)

class Core:
	def __init__(self):
		self.targets = {}
		self.runtime = NoneDictionary()

	def add(self, target):
		"""Add new target"""
		self.targets[target.tgt] = target

	def get(self, tgt):
		"""Get target object"""
		if tgt in self.targets:
			return self.targets[tgt]
		licant.util.error("unregistred target " + licant.util.yellow(tgt))
	
	def subtree(self, root):
		"""Construct Subtree accessor for root target"""
		return SubTree(self, root)
	
	def depends_as_set(self, tgt, incroot=True):
		""""""
		res = set()
		if incroot:
			res.add(tgt)
		
		target = self.get(tgt)
		
		for d in target.deps:
			if not d in res:
				res.add(d)
				subres = self.depends_as_set(d)
				res = res.union(subres)
		return res

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
			target = self.core.get(d)
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
			for dname in t.deps:
				dtarget = self.core.get(dname)
				dtarget.rdepends.append(t.tgt)
	
	
	def reverse_recurse_invoke_single(self, ops, threads=None, cond=licant.util.always_true):
		if core.runtime["debug"]: print("SINGLE THREAD MODE")
		targets = [self.core.get(t) for t in self.depset]
		#sum = 0
	
		self.__generate_rdepends_lists(targets)
		
		works = licant.util.queue()
	
		for t in targets:
			if t.rcounter == len(t.deps):
				works.put(t)

		while(not works.empty()):
			w = works.get()
	
			if cond(self, w):
				ret = w.invoke(ops)
				if ret == False:
					print(licant.util.red("runtime error"))
					exit(-1)
				#if ret == 0:
				#	sum += 1
	
			for r in [self.core.get(t) for t in w.rdepends]:
				r.rcounter = r.rcounter + 1
				if r.rcounter == len(r.deps):
					works.put(r)
	
		#return sum

	def reverse_recurse_invoke_threads(self, ops, threads, cond=licant.util.always_true):
		if core.runtime["debug"]: print("THREADS MODE(threads = {}, ops = {})".format(threads, ops))
		targets = [self.core.get(t) for t in self.depset]
		
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
			if t.rcounter == len(t.deps):
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

					#print("thread {} get work {}".format(index, w.tgt))

					if cond(self, w):
						try:
							ret = w.invoke(ops)
						except:
							info.err = True
							return
						if ret == False:
							info.err = True
							return
						if ret == 0:
							info.sum += 1

					for r in [get_target(t) for t in w.rdepends]:
						r.rcounter = r.rcounter + 1
						if r.rcounter == len(r.deps):
							works.put(r)

					#print("thread {} fini work {}".format(index, w.tgt))
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
			print(licant.util.red("runtime error (multithreads mode)"))
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
			t = self.core.get(d)
			s = "{}: {}\n".format(d, sorted(t.deps))
			ret += s
		ret = ret[:-1]
		return ret

def subtree(root):
	return SubTree(core, root)

def do(tgt, act = None):
	if act == None:
		return core.get_target(tgt).invoke(core.get_target(tgt).default_action)	
	return core.get_target(tgt).invoke(act)

#Объект ядра с которым библиотеки работают по умолчанию.
core = Core()