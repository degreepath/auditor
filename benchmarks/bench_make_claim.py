import pytest
from collections import defaultdict

from degreepath.context import RequirementContext
from degreepath.data import course_from_str


def do_claim(*, course, path, context, allow_claimed):
    context.claims = defaultdict(list)
    claim = context.make_claim(course=course, path=path, allow_claimed=allow_claimed)
    assert claim.failed is False


def init_kwargs(*, course='AMCON 101', path):
    return {
        'context': RequirementContext(),
        'course': course_from_str(course),
        'allow_claimed': False,
        'path': tuple(path),
    }


@pytest.mark.benchmark(group="unclaimed")
def test_claims__unclaimed_long_path(benchmark):
    kwargs = init_kwargs(path=["$", "%Common Requirements", ".count", "[2]", "%Credits outside the major", ".query", ".assertions", "[0]", ".assert", '*AMCON 101'])
    benchmark(do_claim, **kwargs)


@pytest.mark.benchmark(group="unclaimed")
def test_claims__unclaimed_absurd_path(benchmark):
    initial = ["$", "%Common Requirements", ".count", "[2]", "%Credits outside the major", ".query", ".assertions", "[0]", ".assert"]
    kwargs = init_kwargs(path=[*initial, *initial, *initial, *initial, *initial, '*AMCON 101'])
    benchmark(do_claim, **kwargs)


@pytest.mark.benchmark(group="unclaimed")
def test_claims__unclaimed_short_path(benchmark):
    kwargs = init_kwargs(path=["$", "%Common Requirements", '*AMCON 101'])
    benchmark(do_claim, **kwargs)


@pytest.mark.benchmark(group="unclaimed")
def test_claims__unclaimed_empty_path(benchmark):
    kwargs = init_kwargs(path=[])
    benchmark(do_claim, **kwargs)


def do_claim_2(*, course, path, context, allow_claimed):
    claim = context.make_claim(course=course, path=path, allow_claimed=allow_claimed)
    assert claim.failed is True


@pytest.mark.benchmark(group="claimed")
def test_claims__claimed(benchmark):
    course = course_from_str('AMCON 101')

    context = RequirementContext()
    kwargs = {
        'course': course,
        'allow_claimed': False,
        'path': tuple(["$", "%Common Requirements", ".count", "[2]", "%Credits outside the major", ".query", ".assertions", "[0]", ".assert", '*AMCON 101']),
    }

    context.make_claim(**kwargs)

    benchmark(do_claim_2, context=context, **kwargs)
