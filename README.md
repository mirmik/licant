# Licant

Licant is designed to build small modular projects with a complex dependency tree.

What is it?
-----------
Initially Likant was written as a system for assembling code for projects on microcontrollers.

The core of the Lycant system is a make-like assembly tree solver written in python.

But, the main feature of Licant in the system of modules.
The Likant paradigm consists in the description of a project by a set of modules that link to each other. Connecting the module automatically tightens the connection of dependent modules.

Modules can have several implementations, which allows flexible configuration of the project. (For example, you can change the initialization code of the microcontroller or the implementation of the input-output system simply by replacing the implementation of the corresponding module).

One of the goals of the project is to work with submodules located in remote directories. The library subsystem allows a project to refer to modules located in remote directories, which allows several projects to use the same code.

Installing
----------

```sh
python3 -m pip install licant
```

HelloWorld
----------
```python
#!/usr/bin/env python

import licant.make as lmake
import licant

lmake.source("a.txt")
lmake.copy(tgt = "build/b.txt", src = "a.txt")
lmake.copy(tgt = "build/c.txt", src = "build/b.txt")

print("licant targets list:" + str(licant.core.core.targets))

licant.ex(default = "build/c.txt")
```

Example projects
----------------
[https://github.com/mirmik/nos](https://github.com/mirmik/nos)  
[https://github.com/mirmik/igris](https://github.com/mirmik/igris)  
[https://github.com/mirmik/genos](https://github.com/mirmik/genos)  
