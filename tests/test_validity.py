from degreepath import *
import pytest
import io


def test_load():
    test_data = io.StringIO(
        """
        name: foo
        catalog: 2018-19
        type: major
        degree: Bachelor of Arts

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

    area = load(test_data)
    area.validate()


def test_invalid():
    with pytest.raises(Exception):
        test_data = io.StringIO(
            """
            name: foo
            catalog: 2018-19
            type: major
            degree: Bachelor of Arts

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

        area = load(test_data)
        area.validate()
