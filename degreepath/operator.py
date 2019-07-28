from typing import Any
import enum
import logging

logger = logging.getLogger(__name__)


class Operator(enum.Enum):
    LessThan = "$lt"
    LessThanOrEqualTo = "$lte"
    GreaterThan = "$gt"
    GreaterThanOrEqualTo = "$gte"
    EqualTo = "$eq"
    NotEqualTo = "$neq"
    In = "$in"
    NotIn = "$nin"

    def __repr__(self):
        return str(self)


# @lru_cache(maxsize=256, typed=True)
def apply_operator(*, op: Operator, lhs: Any, rhs: Any) -> bool:  # noqa: C901
    """
    Applies two values (lhs and rhs) to an operator.

    `lhs` is drawn from the input data, while `rhs` is drawn from the area specification.

    {attributes: {$eq: csci_elective}}, then, is transformed into something like
    {[csci_elective, csci_systems]: {$eq: csci_elective}}, which is reduced to a set of
    checks: csci_elective == csci_elective && csci_systems == csci_elective.

    {count(courses): {$gte: 2}} is transformed into {5: {$gte: 2}}, which becomes
    `5 >= 2`.

    The additional complications are as follows:

    1. When the comparison is started, if only one of RHS,LHS is a string, the
       other is coerced into a string.

    2. If both LHS and RHS are sequences, an error is raised.

    3. If LHS is a sequence, and OP is .EqualTo, OP is changed to .In
    4. If LHS is a sequence, and OP is .NotEqualTo, OP is changed to .NotIn
    """
    logger.debug("lhs=`%s` op=%s rhs=`%s` (%s, %s)", lhs, op.name, rhs, type(lhs), type(rhs))

    if isinstance(lhs, tuple) and isinstance(rhs, tuple):
        if op is not Operator.In:
            raise Exception('both rhs and lhs must not be sequences when using %s; lhs=%s, rhs=%s', op, lhs, rhs)

        if len(lhs) == 0 or len(rhs) == 0:
            logger.debug("either lhs=%s or rhs=%s was empty; returning false", len(lhs) == 0, len(rhs) == 0)
            return False

        logger.debug("converting both %s and %s to sets of strings, and running intersection", lhs, rhs)
        lhs = set(str(s) for s in lhs)
        rhs = set(str(s) for s in rhs)
        logger.debug("lhs=%s; rhs=%s; intersection=%s", lhs, rhs, lhs.intersection(rhs))
        return bool(lhs.intersection(rhs))

    if isinstance(lhs, tuple) or isinstance(rhs, tuple):
        if op is Operator.EqualTo:
            if isinstance(lhs, tuple) and len(lhs) == 1:
                logger.debug("got lhs=%s with one item, lifting out of the tuple", lhs)
                lhs = lhs[0]
            elif isinstance(lhs, tuple) and len(lhs) == 0:
                logger.debug("got empty lhs, returning False")
                return False
            elif isinstance(rhs, tuple) and len(rhs) == 1:
                logger.debug("got rhs=%s with one item, lifting out of the tuple", rhs)
                rhs = rhs[0]
            elif isinstance(rhs, tuple) and len(rhs) == 0:
                logger.debug("got empty rhs, returning False")
                return False
            else:
                logger.debug("got lhs=%s / rhs=%s; switching to %s", type(lhs), type(rhs), Operator.In)
                return apply_operator(op=Operator.In, lhs=lhs, rhs=rhs)

        elif op is Operator.NotEqualTo:
            logger.debug("got lhs=%s / rhs=%s; switching to %s", type(lhs), type(rhs), Operator.NotIn)
            return apply_operator(op=Operator.NotIn, lhs=lhs, rhs=rhs)

        elif op is Operator.In:
            if isinstance(lhs, tuple):
                return any(apply_operator(op=Operator.EqualTo, lhs=v, rhs=rhs) for v in lhs)
            if isinstance(rhs, tuple):
                return any(apply_operator(op=Operator.EqualTo, lhs=lhs, rhs=v) for v in rhs)
            raise TypeError(f"{op}: expected either {type(lhs)} or {type(rhs)} to be a tuple")

        elif op is Operator.NotIn:
            if isinstance(lhs, tuple):
                return all(apply_operator(op=Operator.NotEqualTo, lhs=v, rhs=rhs) for v in lhs)
            if isinstance(rhs, tuple):
                return all(apply_operator(op=Operator.NotEqualTo, lhs=lhs, rhs=v) for v in rhs)
            raise TypeError(f"{op}: expected either {type(lhs)} or {type(rhs)} to be a tuple")

        else:
            raise Exception(f'{op} does not accept a list; got {lhs} ({type(lhs)})')

    if isinstance(lhs, str) and not isinstance(rhs, str):
        rhs = str(rhs)
    if not isinstance(lhs, str) and isinstance(rhs, str):
        lhs = str(lhs)

    if op is Operator.EqualTo:
        logger.debug("`%s` %s `%s` == %s", lhs, op, rhs, lhs == rhs)
        return lhs == rhs

    if op is Operator.NotEqualTo:
        logger.debug("`%s` %s `%s` == %s", lhs, op, rhs, lhs != rhs)
        return lhs != rhs

    if op is Operator.LessThan:
        logger.debug("`%s` %s `%s` == %s", lhs, op, rhs, lhs < rhs)
        return lhs < rhs

    if op is Operator.LessThanOrEqualTo:
        logger.debug("`%s` %s `%s` == %s", lhs, op, rhs, lhs <= rhs)
        return lhs <= rhs

    if op is Operator.GreaterThan:
        logger.debug("`%s` %s `%s` == %s", lhs, op, rhs, lhs > rhs)
        return lhs > rhs

    if op is Operator.GreaterThanOrEqualTo:
        logger.debug("`%s` %s `%s` == %s", lhs, op, rhs, lhs >= rhs)
        return lhs >= rhs

    raise TypeError(f"unknown comparison {op}")


def str_operator(op):
    if op == 'LessThan':
        return '<'
    elif op == 'LessThanOrEqualTo':
        return '≤'
    elif op == 'GreaterThan':
        return '>'
    elif op == 'GreaterThanOrEqualTo':
        return '≥'
    elif op == 'EqualTo':
        return '=='
    elif op == 'NotEqualTo':
        return '!='
    elif op == 'In':
        return '∈'
    elif op == 'NotIn':
        return '∉'
