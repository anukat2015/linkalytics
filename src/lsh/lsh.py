from .. tdm import lsh
from .. tdm import Arguments

def run(node):
    query, size = node.get('text', 'cali'), node.get('size', 1000)

    args = Arguments(query, size)

    return lsh(args)
