#!/usr/bin/env python3

import licant.install
import licant

licant.source("a")
tgtpath = licant.install.install_application("a")

licant.ex(tgtpath)