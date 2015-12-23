
from lightning import Lightning
lgn = Lightning(host='192.168.99.100')

def show(G):
    mat, labels = nx.attr_matrix(G)
    g = np.array(list(G.degree().values()))
    return lgn.force(mat, group=g, labels=[i for i in labels])