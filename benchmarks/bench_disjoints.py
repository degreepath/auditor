from itertools import combinations
import random
import pytest


def find_entirely_disjoint_sets(*sets):
    dis = set()
    joint = set()

    for a, b in combinations(sets, 2):
        if a.isdisjoint(b):
            dis.add(a)
            dis.add(b)
        else:
            joint.add(a)
            joint.add(b)

        if a in joint:
            dis.discard(a)
        if b in joint:
            dis.discard(b)

    return dis, joint


def disjoint_2(*sets):
    joint = set()
    disjoint = set()

    for a, b in combinations(sets, 2):
        if a.isdisjoint(b):
            if a in joint:
                disjoint.discard(a)
            else:
                disjoint.add(a)

            if b in joint:
                disjoint.discard(b)
            else:
                disjoint.add(b)
        else:
            joint.add(a)
            joint.add(b)
            disjoint.discard(a)
            disjoint.discard(b)

    return disjoint, joint


def disjoint_3(*sets):
    joint = set()
    disjoint = set()

    for a, b in combinations(sets, 2):
        if a.isdisjoint(b):
            disjoint.add(a)
            disjoint.add(b)
        else:
            joint.add(a)
            joint.add(b)

    for s in joint:
        disjoint.discard(s)

    return disjoint, joint


def disjoint_4(*sets):
    joint = set()
    disjoint = set()

    for a, b in combinations(sets, 2):
        if a.isdisjoint(b):
            disjoint.update((a, b))
        else:
            joint.update((a, b))

    for s in joint:
        disjoint.discard(s)

    return disjoint, joint


def disjoint_5(*sets):
    joint = set()
    disjoint = set()

    for a, b in combinations(sets, 2):
        if a.isdisjoint(b):
            disjoint.update((a, b))
        else:
            joint.update((a, b))

    disjoint = disjoint.difference(joint)

    return disjoint, joint


def setup():
    return tuple(
        frozenset(
            random.randrange(1, 501)
            for n in range(random.randrange(0, 50))
        )
        for _ in range(random.randrange(1, 101))
    )


data = setup()


def test_disjoint():
    dis_1, joint_1 = find_entirely_disjoint_sets(*data)
    dis_2, joint_2 = disjoint_2(*data)
    dis_3, joint_3 = disjoint_3(*data)
    dis_4, joint_4 = disjoint_4(*data)
    dis_5, joint_5 = disjoint_5(*data)

    assert dis_1 == dis_2 == dis_3 == dis_4 == dis_5
    assert joint_1 == joint_2 == joint_3 == joint_4 == joint_5


@pytest.mark.benchmark(group="disjoint")
def test_disjoint_1(benchmark):
    dis, joint = benchmark(find_entirely_disjoint_sets, *data)


@pytest.mark.benchmark(group="disjoint")
def test_disjoint_2(benchmark):
    dis_2, joint_2 = benchmark(disjoint_2, *data)


@pytest.mark.benchmark(group="disjoint")
def test_disjoint_3(benchmark):
    dis_3, joint_3 = benchmark(disjoint_3, *data)


@pytest.mark.benchmark(group="disjoint")
def test_disjoint_4(benchmark):
    dis_4, joint_4 = benchmark(disjoint_4, *data)


@pytest.mark.benchmark(group="disjoint")
def test_disjoint_5(benchmark):
    dis_5, joint_5 = benchmark(disjoint_5, *data)
