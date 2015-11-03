from .. tdm import lsh

class Arguments():

    def __init__(self, query, size):
        self.query = [query]
        self.size  = [size]

def run(node):
    query, size = node.get('text', 'cali'), node.get('size', 1000)

    args = Arguments(query, size)

    return lsh(args)
