from degreepath.area import AreaOfStudy
from degreepath.constants import Constants
import pytest
import io
import yaml

c = Constants(matriculation_year=2000)


def test_load():
    test_data = io.StringIO(
        """
        name: foo
        catalog: 2018-19
        type: major
        degree: B.A.

        result:
          all:
            - requirement: Foo

        requirements:
          Foo:
            result:
              count: 2
              of:
                - course: CSCI 121
                - course: CSCI 125
                - requirement: FooBar
            requirements:
              FooBar:
                result:
                  both:
                    - course: CSCI 121
                    - course: CSCI 251
    """
    )

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)
    area.validate()


def test_invalid():
    with pytest.raises(Exception):
        test_data = io.StringIO(
            """
            name: foo
            catalog: 2018-19
            type: major
            degree: B.A.

            result:
                count: 1
                of:
                    - requirement: Foo

            requirements:
                - name: Foo
                  result:
                    count: 2
                    of:
                        - CSCI 121
                        - CSCI 125
                        - requirement: FooBar
        """
        )

        area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)
        area.validate()
