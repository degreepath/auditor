from degreepath.requirement import Requirement
from degreepath.rule.given import FromRule
import pytest
import io
import logging


def c(s):
    return CourseSolution(course=s)
