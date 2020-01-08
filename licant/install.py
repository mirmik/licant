import os
import sys
import licant.make

path_list = os.environ["PATH"].split(":")

if "/usr/local/bin" in path_list:
	path = "/usr/local/bin"
else:
	for p in path_list:
		if "/usr/bin" in p:
			path = p 
	else:
		sys.exit(0)

def install_application(src, newname=None):
	if newname is None:
		newname = os.path.basename(src)
	tgt = os.path.join(path, newname)
	licant.make.copy(tgt=tgt, src=src)

	return tgt