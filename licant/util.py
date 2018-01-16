import sys
import os

class quite:
	pass

class queue:
	class DontHaveArg:
		pass

	def __init__(self):
		self.lst = []
		self.rdr = 0

	def put(self, obj):
		self.lst.append(obj)

	def get(self):
		if (len(self.lst) == 0):
			raise DontHaveArg()

		ret = self.lst[self.rdr]

		self.rdr += 1 
		if self.rdr >= len(self.lst):
			self.__init__()

		return ret

	def empty(self):
		return len(self.lst) == 0

	def __str__(self):
		return str(self.lst)

def textblock(str):
	return chr(27) + str + chr(27) + "[0m"

def black(str):
	return textblock("[30;1m" + str)

def red(str):
	return textblock("[31;1m" + str)

def green(str):
	return textblock("[32;1m" + str)

def yellow(str):
	return textblock("[33;1m" + str)

def purple(str):
	return textblock("[35;1m" + str)

def cyan(str):
	return textblock("[36;1m" + str)

def white(str):
	return textblock("[37;1m" + str)

def do_argv_routine(arg, default, locs):
	if len(sys.argv) <= arg:
		func = default
	else:
		func = sys.argv[arg]
	
	if func in locs:
		return locs[func]()
	else:
		print("Bad routine")
		exit(-1)



def always_true(context, work):
	return True

def changeext(path, newext):
	return os.path.splitext(path)[0]+"."+newext 

def flag_prefix(pref, lst):
	if lst and lst != []:
		return " ".join(map(lambda x: pref+x,lst))
	else:
		return ""


def as_list(src):
	if (not isinstance(src, list)):
		return [src]
	return src

def find_recursive(root, pattern, hide, debug):
	result = []
	
	if hide == None:
		for d, dirs, files in os.walk(root):
			for f in files:
				if pattern in f:
					path = os.path.join(d,f)
					if debug:
						print(path)
					result.append(path)

	else:
		for d, dirs, files in os.walk(root):
			if not hide in d:
				for f in files:
					if pattern in f:
						path = os.path.join(d,f)
						if debug:
							print(path)
						result.append(path)

	return result

import re
pattern = re.compile(r"[\w./-]+")
def cxx_read_depends(path):
	if not os.path.exists(path):
		return None
	else:
		f = open(path)
		text = f.read()
		lst = pattern.findall(text)
		#lst = re.split(r'[ \n\\]+', text)
		#print(lst)
		#exit(0)
		return lst[2:]
