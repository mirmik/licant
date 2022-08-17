#!/usr/bin/env python3

import licant.install
import licant

licant.source("a")
#tgtpath = licant.install.install_application("a")
headerstarget = licant.install.install_headers(tgtdir="testlicant", srcdir="headers")

libtgt = licant.install.install_library(libtgt="a", headers="headers", hroot="testlicant2")

licant.ex(libtgt)