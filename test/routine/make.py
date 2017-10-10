#!/usr/bin/env python

import sys
sys.path.insert(0, "../..")

from licant.routine import add_routine, invoke

add_routine("hello", lambda: print("HelloWorld"))

invoke(sys.argv[1:])

