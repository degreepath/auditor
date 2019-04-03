from degreepath import __version__, load


def test_version():
    assert __version__ == "0.1.0"


def test_load():
    import io

    test_data = io.StringIO("""
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
                count: 3
                of:
                    - CSCI 121
    """)

    print(load(test_data))

    raise TabError
