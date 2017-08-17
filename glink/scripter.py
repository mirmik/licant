import sys

class ScriptQueue:
	def __init__(self):
		self.stack = [sys.argv[0]]
		#print(self.stack)

	def execute(self, path):
		self.stack.append(path)
		exec(open(path).read(), globals())
		self.stack.pop()

	def last(self):
		return self.stack[-1]

scriptq = ScriptQueue()