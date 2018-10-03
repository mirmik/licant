#coding: utf-8

from __future__ import print_function

import licant
from licant.core import Target, UpdatableTarget, UpdateStatus, core, subtree
from licant.cache import fcache
from licant.util import red, green, yellow, purple, quite
import threading
from licant.util import deprecated
import os
import sys

_rlock = threading.RLock()


def do_execute(target, rule, msgfield, prefix=None):
    def sprint(*args, **kwargs):
        with _rlock:
            print(*args, **kwargs)

    rule = rule.format(**target.__dict__)

    message = getattr(target, msgfield, None)

    if not core.runtime["debug"] and message != None:
        if not isinstance(message, quite):
            if prefix != None:
                sprint(prefix, message.format(**target.__dict__))
            else:
                sprint(message.format(**target.__dict__))

    else:
        sprint(rule)

    ret = os.system(rule)

    if target.isfile == True:
        target.update_info(target)

    return True if ret == 0 else False


class MakeFileTarget(UpdatableTarget):
    def __init__(self, tgt, deps, **kwargs):
        UpdatableTarget.__init__(self, tgt, deps, **kwargs)

    def clean(self):
        stree = subtree(self.tgt)
        stree.invoke_foreach(ops="need_if_exist")
        return stree.invoke_foreach(ops="clr", cond=if_need_and_file)

    def makefile(self):
        stree = subtree(self.tgt)
        stree.invoke_foreach(ops="dirkeep")
        stree.reverse_recurse_invoke(
            ops="update_if_need", threads=core.runtime["threads"])


class FileTarget(MakeFileTarget):
    def __init__(self, tgt, deps, force=False, **kwargs):
        MakeFileTarget.__init__(self, tgt, deps, **kwargs)
        self.isfile = True
        self.force = force
        self.clrmsg = "DELETE {tgt}"
        self.default_action = "makefile"

    def update_info(self, _self):
        fcache.update_info(self.tgt)
        return True

    def mtime(self):
        curinfo = fcache.get_info(self.tgt)
        if curinfo.exist == False:
            return 0
        else:
            return curinfo.mtime

    def dirkeep(self):
        dr = os.path.normpath(os.path.dirname(self.tgt))
        if (not os.path.exists(dr)):
            print("MKDIR %s" % dr)
            os.system("mkdir -p {0}".format(dr))
        return True

    def is_exist(self):
        curinfo = fcache.get_info(self.tgt)
        return curinfo.exist

    def need_if_exist(self):
        curinfo = fcache.get_info(self.tgt)
        if curinfo.exist:
            self.need = True
        else:
            self.need = False

        return 0

    def clr(self):
        do_execute(self, "rm -f {tgt}", "clrmsg")

    def self_need(self):
        if self.force or self.is_exist() == False:
            return True

        maxtime = 0
        for dep in self.get_deplist():
            if dep.mtime() > maxtime:
                maxtime = dep.mtime()

        if maxtime > self.mtime():
            return True

        return False

    def update(self):
        return self.invoke("build")


class FileSet(MakeFileTarget):
    def __init__(self, tgt, targets):
        MakeFileTarget.__init__(
            self, tgt=tgt, deps=targets, default_action="makefile")
        self.targets = targets
        self.__mtime = None

    def self_need(self):
        return False

    def update(self):
        pass

    def mtime(self):
        if (self.__mtime is None):
            maxtime = 0
            for dep in self.get_deplist():
                if dep.mtime() > maxtime:
                    maxtime = dep.mtime()
            self.__mtime = maxtime

        return self.__mtime


def fileset(tgt, targets):
    core.add(FileSet(
        tgt=tgt,
        targets=targets
    ))


class Executor:
    def __init__(self, rule, msgfield='message'):
        self.rule = rule
        self.msgfield = msgfield

    def __call__(self, target, **kwargs):
        return do_execute(target, self.rule, self.msgfield, **kwargs)


def copy(tgt, src, adddeps=[], message="COPY {src} {tgt}"):
    core.add(FileTarget(
        tgt=tgt,
        build=Executor("cp {src} {tgt}"),
        src=src,
        deps=[src] + adddeps,
        message=message
    ))


def source(tgt, deps=[]):
    target = FileTarget(
        build=warn_if_not_exist,
        deps=deps,
        tgt=tgt,
    )
    target.clr = None
    target.dirkeep = None
    target.update_status = UpdateStatus.Keeped
    core.add(target)


def if_need_and_file(context, target):
    need = getattr(target, "need", None)
    if need == None:
        return False
    return need and isinstance(target, FileTarget)


def warn_if_not_exist(target):
    info = fcache.get_info(target.tgt)
    if info.exist == False:
        print("Warn: file {} isn`t exist".format(purple(target.tgt)))
