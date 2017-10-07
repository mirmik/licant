import sys
import os
import licant.util
from licant.core import core
from licant.make import source

class ScriptQueue:
	def __init__(self):
		self.stack = [sys.argv[0]]
		licant.make.source(sys.argv[0])

	def __execute(self, path):
		licant.make.source(path)
		self.stack.append(path)
		exec(open(path).read(), globals())
		self.stack.pop()

	def execute(self, path):
		path = os.path.join(self.curdir(), path)
		self.__execute(path)

	def last(self):
		return self.stack[-1]

	def curdir(self):
		return os.path.dirname(self.last())

	def execute_recursive(self, root, pattern, hide=None, debug=False):
		root = os.path.join(self.curdir(), root)
		#print(root)
		flst = licant.util.find_recursive(root, pattern, hide, debug)
		for f in flst:
			self.__execute(f)

scriptq = ScriptQueue()

#def script_target(tgt, execfrom):
#	licant.make.source(tgt, deps=[execfrom])