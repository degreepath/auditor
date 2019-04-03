from degreepath import __version__, load
import pytest
import io


def test_version():
    assert __version__ == "0.1.0"


def test_load():
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
              requirements:
                - name: FooBar
                  result:
                    both:
                        - CSCI 121
                        - CSCI 251
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
