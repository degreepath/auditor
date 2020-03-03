import os


def read(*, filepath):
    args = {}

    with open(filepath, 'r', encoding='UTF-8') as infile:
        for line in infile:
            line = line.strip()

            if line.startswith('#'):
                continue

            if not line:
                continue

            key, value = line.split('=')
            key = key.strip()
            value = value.strip()

            assert key

            args[key] = value

    return args


def load(filepath='./.env'):
    args = read(filepath=filepath)

    for key, value in args.items():
        os.environ[key] = value
