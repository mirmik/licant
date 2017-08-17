import sys
import os
import glink.util
from glink.core import core
from glink.make import source

class ScriptQueue:
	def __init__(self):
		self.stack = [sys.argv[0]]
		glink.make.source(sys.argv[0])

	def execute(self, path):
		glink.make.source(path)
		self.stack.append(path)
		exec(open(path).read(), globals())
		self.stack.pop()

	def last(self):
		return self.stack[-1]

	def curdir(self):
		return os.path.dirname(self.last())

	def execute_recursive(self, root, pattern, hide):
		flst = glink.util.find_recursive(os.path.join(self.curdir(), root), pattern, hide)
		for f in flst:
			self.execute(f)

scriptq = ScriptQueue()

#def script_target(tgt, execfrom):
#	glink.make.source(tgt, deps=[execfrom])