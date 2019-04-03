from typing import TextIO
import yaml
from ..area import AreaOfStudy


def load(stream: TextIO) -> AreaOfStudy:
    data = yaml.load(stream=stream, Loader=yaml.SafeLoader)

    return AreaOfStudy.load(data)
