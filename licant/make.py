# coding: utf-8

from __future__ import print_function

import licant
from licant.core import UpdatableTarget, UpdateStatus, Core, core
from licant.cache import fcache
from licant.util import purple, quite
import threading
import os
import time
import subprocess
import fcntl
import sys

_rlock = threading.RLock()


def do_execute(target, rule, msgfield, prefix=None):
    def sprint(*args, **kwargs):
        """print for multithread build"""
        with _rlock:
            print(*args, **kwargs)

    rule = rule.format(**target.__dict__)

    message = getattr(target, msgfield, None)

    if not core.runtime["quite"]:
        if not core.runtime["debug"] and message is not None:
            if not isinstance(message, quite):
                if prefix is not None:
                    sprint(prefix, message.format(**target.__dict__))
                else:
                    sprint(message.format(**target.__dict__))

        else:
            sprint(rule)

    proc = subprocess.Popen(
        rule, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = proc.stdout
    stderr = proc.stderr
    ret = proc.wait()

    sprint(stdout.read().decode("utf-8"), end="")
    sys.stdout.flush()
    sprint(stderr.read().decode("utf-8"), end="")
    sys.stderr.flush()

    if target.isfile:
        target.update_info(target)

    return True if ret == 0 else False


class Executor:
    def __init__(self, rule, msgfield="message"):
        self.rule = rule
        self.msgfield = msgfield

    def __call__(self, target, **kwargs):
        return do_execute(target, self.rule, self.msgfield, **kwargs)


class DirectoryKeeper():
    def __init__(self, msgfield="message"):
        self.msgfield = msgfield

    def __call__(self, target, **kwargs):
        print("MAKEDIRS", target.tgt)
        if not os.path.exists(target.tgt):
            os.makedirs(target.tgt)


class MakeFileTarget(UpdatableTarget):
    __actions__ = UpdatableTarget.__actions__.union(
        {"actlist", "makefile", "clean"})

    def __init__(self, tgt, deps, **kwargs):
        UpdatableTarget.__init__(self, tgt, deps, **kwargs)
        self.default_action = "makefile"

    def clean(self):
        stree = self.core.subtree(self.tgt)
        return stree.invoke_foreach(ops="clr", cond=if_file_and_exist)

    def makefile(self):
        return self.recurse_update()


class FileTarget(MakeFileTarget):
    __actions__ = MakeFileTarget.__actions__.union(
        {"build", "clr", "mtime_info"})

    def __init__(self, tgt, deps, force=False, use_dirkeep=True, **kwargs):
        if use_dirkeep:
            dirpath = os.path.normpath(os.path.dirname(tgt))
            if not os.path.exists(dirpath):
                dirkeep(dirpath)
                deps = deps + [dirpath]

        MakeFileTarget.__init__(self, tgt, deps, **kwargs)
        self.isfile = True
        self.force = force
        self.clrmsg = "DELETE {tgt}"

    def mtime_info(self):
        print("self mtime:")
        print("\t", self.tgt, self.mtime())
        print("deps mtime:")
        maxtime = 0
        for dep in self.get_deplist():
            if isinstance(dep, (FileTarget, FileSet)) and dep.mtime() > maxtime:
                print("\t", dep.tgt, dep.mtime())
            else:
                print("\t", dep.tgt, "not a file:", dep.__class__)
        print("is update needed:", self.self_need())

    def update_info(self, _self):
        fcache.update_info(self.tgt)
        return True

    def mtime(self):
        curinfo = fcache.get_info(self.tgt)
        return os.path.getmtime(self.tgt)
        #curinfo = fcache.get_info(self.tgt)
        # if not curinfo.exist:
        #    return 0
        # else:
        #    return curinfo.mtime

    def is_exist(self):
        #        print("is_exist", self.tgt, fcache.get_info(self.tgt).exist)
        curinfo = fcache.get_info(self.tgt)
        return curinfo.exist

    def warn_if_not_exist(self):
        """Print warn if file isn't exist"""
        info = fcache.get_info(self.tgt)
        if not info.exist:
            print("Warn: file {} isn`t exist".format(purple(self.tgt)))

    def clr(self):
        """Delete this file."""
        do_execute(self, "rm -f {tgt}", "clrmsg")

    def self_need(self):
        if self.force or not self.is_exist():
            return True

        maxtime = 0
        for dep in self.get_deplist():
            if isinstance(dep, (FileTarget, FileSet)) and dep.mtime() > maxtime:
                maxtime = dep.mtime()

        if maxtime > self.mtime():
            return True

        return False

    def needs_update(self):
        return self.self_need()

    def update(self):
        return self.build(self)

    def __lt__(self, other):
        return str(self) < str(other)

    def __gt__(self, other):
        return str(self) > str(other)


class DirectoryTarget(FileTarget):
    def self_need(self):
        if not self.is_exist():
            return True
        return False

    def mtime(self):
        return 0

    def update_if_need(self):
        #print(self.tgt, self.self_need())
        if self.self_need():  # self.invoke("self_need"):
            self.update_status = UpdateStatus.Updated
            return self.update()  # self.invoke("update")
        else:
            self.update_status = UpdateStatus.Keeped
            return True

    def clr(self):
        """Prevent directory deletion."""
        pass


class FileSet(MakeFileTarget):
    """Virtual file target`s set.

        For link a set of file objects to the licant tree
        without depend`s overhead."""

    def __init__(self, tgt, targets, deps, **kwargs):
        MakeFileTarget.__init__(self, tgt=tgt, deps=targets+deps, **kwargs)
        self.targets = targets
        self.__mtime = None

    def self_need(self):
        return False

    def update(self):
        pass

    def clean(self):
        for target in self.targets:
            target = self.core.get(target)
            target.invoke("clean")

    def mtime(self):
        if self.__mtime is None:
            maxtime = 0
            for dep in self.get_deplist():
                if dep.mtime() > maxtime:
                    maxtime = dep.mtime()
            self.__mtime = maxtime

        return self.__mtime

    def __lt__(self, other):
        return str(self) < str(other)

    def __gt__(self, other):
        return str(self) > str(other)


def source(tgt, deps=[]):
    """Index source file by licant core."""

    if core.exist(tgt):
        return

    target = FileTarget(
        build=lambda self: self.warn_if_not_exist(), deps=deps, tgt=tgt)
    target.clr = None
    target.dirkeep = licant.util.do_nothing
    target.update_status = UpdateStatus.Keeped
    return core.add(target)


def dirkeep(dirpath, message="MKDIR {tgt}"):
    """Create directory tree for this file if needed."""
    base_directory_path = os.path.normpath(os.path.dirname(dirpath))
    return core.add(
        DirectoryTarget(
            tgt=dirpath,
            build=DirectoryKeeper(),
            use_dirkeep=not os.path.exists(base_directory_path),
            message=message,
            deps=[]
        )
    )


def makedir(dirpath, message="MKDIR {tgt}"):
    return dirkeep(dirpath, message)


def copy(tgt, src, adddeps=[], message="COPY {src} {tgt}"):
    """Make the file copy target."""
    src = os.path.expanduser(str(src))
    tgt = os.path.expanduser(str(tgt))

    source(src)
    core.add(
        FileTarget(
            tgt=tgt,
            build=Executor("cp {src} {tgt}"),
            src=src,
            deps=[src] + adddeps,
            message=message,
        )
    )
    return tgt


def makefile(tgt, deps, do, **kwargs):
    """Makefile target."""
    return core.add(
        FileTarget(
            tgt=tgt,
            build=Executor(do),
            deps=deps,
            **kwargs
        )
    )


def fileset(tgt, targets, deps=[], **kwargs):
    """Make a fileset."""
    core.add(FileSet(tgt=tgt, targets=targets, deps=deps, **kwargs))
    return tgt


def if_file_and_exist(target):
    if not isinstance(target, FileTarget):
        return False

    curinfo = fcache.get_info(target.tgt)
    return curinfo.exist


class MakeCore(Core):
    def __init__(self, debug=False):
        super().__init__(debug=debug)

    def makedir(self, dirpath, deps, message="MKDIR {tgt}"):
        return self.add(
            DirectoryTarget(
                tgt=dirpath,
                build=DirectoryKeeper(),
                use_dirkeep=False,
                message=message,
                deps=deps
            )
        )

    def dirkeep(self, path):
        """Create directory tree for this file if needed."""
        base_directory_path = os.path.normpath(os.path.dirname(path))
        if not os.path.exists(base_directory_path):
            deps = self.dirkeep(base_directory_path)
            if not self.has(base_directory_path):
                self.makedir(base_directory_path, deps=deps)
            return [base_directory_path]
        else:
            return []

    def touch(self, out, content="", deps=[]):
        """Create file if not exist."""

        def create_file(self):
            with open(self.tgt, "w") as f:
                f.write(content)

        out = os.path.expanduser(str(out))
        dirdeps = self.dirkeep(out)
        return self.add(FileTarget(
            tgt=out,
            build=create_file,
            deps=deps + dirdeps,
            message="TOUCH {tgt}",
            use_dirkeep=False,
            content=content
        ))

    def copy(self, src, dst, deps=[], message="COPY {src} {tgt}"):
        """Make the file copy target."""
        src = os.path.expanduser(str(src))
        dst = os.path.expanduser(str(dst))
        dirdeps = self.dirkeep(dst)
        self.source(src)
        return self.add(FileTarget(
            tgt=dst,
            build=Executor("cp {src} {tgt}"),
            src=src,
            deps=[src] + dirdeps + deps,
            use_dirkeep=False,
            message=message,
        ))

    def source(self, src):
        """Index source file by licant core."""
        if self.has(str(src)):
            return self.get(str(src))

        src = os.path.expanduser(str(src))
        target = self.add(FileTarget(
            tgt=src,
            build=lambda self: self.warn_if_not_exist(),
            deps=[],
            use_dirkeep=False,
            message="SOURCE {tgt}"
        ))
        target.clr = None
        target.dirkeep = licant.util.do_nothing
        target.update_status = UpdateStatus.Keeped
        return target
