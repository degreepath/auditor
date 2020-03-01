from typing import Any, Dict

from .operator import str_operator


def str_clause(clause: Dict[str, Any], *, nested: bool = False, raw_only: bool = False) -> str:
    if clause["type"] == "single-clause":
        key = clause["key"]

        if key == 'attributes':
            key = 'bucket'
        elif key == 'is_in_progress':
            key = 'in-progress'
        elif key == 'is_stolaf':
            key = 'from STOLAF'

        resolved_with = clause.get('resolved_with', None)
        if resolved_with is not None:
            resolved = f" [{repr(resolved_with)}]"
        else:
            resolved = ""

        expected = clause['expected']

        if raw_only:
            expected = clause['expected_verbatim']
            postscript = f""
        if str(expected) != str(clause['expected_verbatim']):
            postscript = f" [via {repr(clause['expected_verbatim'])}]"
        else:
            postscript = ""

        label = clause['label']
        if label:
            postscript += f' [label: "{label}"]'

        op = str_operator(clause['operator'])

        if clause['operator'] == 'EqualTo' and expected is True:
            return f'{key}{resolved}{postscript}'
        elif clause['operator'] == 'EqualTo' and expected is False:
            return f'not "{key}"{resolved}{postscript}'

        return f'{key}{resolved} {op} {expected}{postscript}'

    elif clause["type"] == "or-clause":
        text = " or ".join(str_clause(c, nested=True, raw_only=raw_only) for c in clause["children"])
        if not nested:
            return text
        else:
            return f'({text})'

    elif clause["type"] == "and-clause":
        text = " and ".join(str_clause(c, nested=True, raw_only=raw_only) for c in clause["children"])
        if not nested:
            return text
        else:
            return f'({text})'

    raise Exception('not a clause')
