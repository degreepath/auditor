from textwrap import dedent


def autop(data: str) -> str:
    data = dedent(data)

    chunks = (chunk for chunk in data.split('\n\n'))

    chunks = (para.strip() for para in chunks)

    chunks = (' '.join(para.split('\n')) for para in chunks)

    return ''.join(wrap_untagged(chunk) for chunk in chunks)


def wrap_untagged(chunk: str) -> str:
    if chunk.startswith('<'):
        return chunk
    else:
        return f"<p>{chunk}</p>"
