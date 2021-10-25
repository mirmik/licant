# coding: utf-8

from __future__ import print_function

import licant
from licant.core import UpdatableTarget, UpdateStatus, core
from licant.cache import fcache
from licant.util import purple, quite
import threading
import os

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

    ret = os.system(rule)

    if target.isfile:
        target.update_info(target)

    return True if ret == 0 else False


class Executor:
    def __init__(self, rule, msgfield="message"):
        self.rule = rule
        self.msgfield = msgfield

    def __call__(self, target, **kwargs):
        return do_execute(target, self.rule, self.msgfield, **kwargs)


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
    __actions__ = MakeFileTarget.__actions__.union({"build", "clr"})

    def __init__(self, tgt, deps, force=False, **kwargs):
        MakeFileTarget.__init__(self, tgt, deps, **kwargs)
        self.isfile = True
        self.force = force
        self.clrmsg = "DELETE {tgt}"

    def update_info(self, _self):
        fcache.update_info(self.tgt)
        return True

    def mtime(self):
        curinfo = fcache.get_info(self.tgt)
        if not curinfo.exist:
            return 0
        else:
            return curinfo.mtime

    def dirkeep(self):
        """Create directory tree for this file if needed."""
        dr = os.path.normpath(os.path.dirname(self.tgt))
        if not os.path.exists(dr):
            print("MKDIR %s" % dr)
            os.system("mkdir -p {0}".format(dr))
        return True

    def is_exist(self):
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
            if dep.mtime() > maxtime:
                maxtime = dep.mtime()

        if maxtime > self.mtime():
            return True

        return False

    def update(self):
        self.dirkeep()
        return self.build(self)


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

    def mtime(self):
        if self.__mtime is None:
            maxtime = 0
            for dep in self.get_deplist():
                if dep.mtime() > maxtime:
                    maxtime = dep.mtime()
            self.__mtime = maxtime

        return self.__mtime


def source(tgt, deps=[]):
    """Index source file by licant core."""

    if core.exist(tgt):
        return

    target = FileTarget(
        build=lambda self: self.warn_if_not_exist(), deps=deps, tgt=tgt)
    target.clr = None
    target.dirkeep = licant.util.do_nothing
    target.update_status = UpdateStatus.Keeped
    core.add(target)
    return tgt


def copy(tgt, src, adddeps=[], message="COPY {src} {tgt}"):
    """Make the file copy target."""
    src = os.path.expanduser(src)
    tgt = os.path.expanduser(tgt)

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
    """Make the file copy target."""
    core.add(
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
