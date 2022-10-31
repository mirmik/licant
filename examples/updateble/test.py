#!/usr/bin/env python3
# coding: utf-8

from licant import UpdatableTarget
import licant
import os
import sys

sys.path.insert(0, "../..")


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
        update=copy
    )
)
core.add(
    UpdatableTarget(
        tgt="hello_world_0",
        deps=[],
        update=hello_world_0
    )
)
core.add(
    UpdatableTarget(
        tgt="hello_world_1",
        deps=["hello_world_0", "copy"],
        update=hello_world_1
    )
)

core.do("hello_world_1", "recurse_update")
