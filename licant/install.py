import os
import sys
import licant.make

error_in_install_library = False
path_list = os.environ["PATH"].split(":")

if "/usr/local/bin" in path_list:
	path = "/usr/local/bin"
else:
	print("DebugMode")
	for p in path_list:
		print(p)
		print("/usr/bin" in p)
		if "/usr/bin" in p:
			path = p
			print(f"path found: {path}")
			break 
	else:
		print("Warning: Install path not found")
		error_in_install_library = True
		
def install_application(src, newname=None):
	if error_in_install_library:
		return None

	if newname is None:
		newname = os.path.basename(src)
	tgt = os.path.join(path, newname)
	licant.make.copy(tgt=tgt, src=src)

	return tgt