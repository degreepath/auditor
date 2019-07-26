from degreepath import *
from degreepath.requirement import Requirement
from degreepath.rule.given import FromRule, FromInput
import pytest
import io
import logging


def c(s):
    return CourseSolution(course=s)
