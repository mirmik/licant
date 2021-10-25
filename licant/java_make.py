from licant.core import core
import licant.make
import os


class java_options:
    def __init__(
            self,
            toolchain=None,
            javac_flags=""
    ):
        self.toolchain = toolchain
        self.javac_flags = javac_flags
        self.javacrule = "{opts.toolchain.javac} {opts.javac_flags} {srcs}"
        self.dexrule = "{opts.toolchain.dx} --dex --output {tgt} {src}"


class java_toolchain:
    def __init__(self, javac):
        self.javac = javac


class android_toolchain:
    def __init__(self, javac, dx):
        self.javac = javac
        self.dx = dx


def javac(srcs, tgt, opts=java_options(), message="JAVA {tgt}", deps=[]):
    build = licant.make.Executor(opts.javacrule)

    for j in srcs:
        licant.make.source(j)

    core.add(
        licant.make.FileTarget(
            opts=opts,
            tgt=tgt,
            srcs=" ".join(srcs),
            deps=deps + srcs,
            build=build,
            message=message
        )
    )


def dex(src, tgt, opts=java_options(), message="DEX {tgt}", deps=[]):
    build = licant.make.Executor(opts.dexrule)

    # for j in srcs:
    #	licant.make.source(j) // scan class files

    core.add(
        licant.make.FileTarget(
            opts=opts,
            tgt=tgt,
            src=src,
            deps=deps,
            build=build,
            message=message
        )
    )
