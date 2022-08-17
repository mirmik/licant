#!/usr/bin/env python3
# coding: utf-8

import os
import sys

sys.path.insert(0, "../..")

import licant
from licant import UpdateStatus, UpdatableTarget

core = licant.Core()


def hello_world_0(tgt):
    print("hw0")


def hello_world_1(tgt):
    print("hw1")


def copy(tgt):
    task = "cp {} {}".format(tgt.src, tgt.tgtpath)
    print(task)
    res = os.system(task)


core.add(
    UpdatableTarget(
        tgt="copy",
        src="a",
        tgtpath="b",
        deps=[],
        update=copy,
        update_status=UpdateStatus.Keeped,
    )
)
core.add(
    UpdatableTarget(
        tgt="hello_world_0",
        deps=[],
        update=hello_world_0,
        update_status=UpdateStatus.Keeped,
    )
)
core.add(
    UpdatableTarget(
        tgt="hello_world_1",
        deps=["hello_world_0", "copy"],
        update=hello_world_1,
        update_status=UpdateStatus.Keeped,
    )
)

stree = core.subtree("hello_world_1")

print("stree:")
print(stree)
print()

stree.reverse_recurse_invoke("update_if_need", threads=1)
