# -*- coding: utf-8 -*-

import itertools
import random
import math

import numpy as np

from hashlib import sha1

NUM_PERM = 100

# We truncate sha1 for now
# We should probably replace this with a proper hash function.
M_PRIME  = (1 << 89) - 1
MAX_HASH = (1 << 64) - 1 

random.seed(427)

A, B = np.array([(random.randint(1, M_PRIME), random.randint(0, M_PRIME)) for _ in range(NUM_PERM)]).T

def get_permuted_hashes(token):
    """
    Get a hash value
    Abusing sha1 and truncating to 12 digit number
    """
    hv = int(sha1(token).hexdigest(), 16) % (10 ** 12)

    # Do Carter and Wegman like hashing.
    return np.bitwise_and((A * hv + B) % M_PRIME, MAX_HASH)

def get_lsh(sig, nbands):
    for i, band in enumerate(np.array_split(sig, nbands)):
        yield sha1("ab{band}ba{i}".format(band=band, i=i).encode('utf-8')).digest()

def get_bandwidth(n, tr):
        """
        Threshold:
            tr = (1/b) ** (1/r)
        Where:
            b: bands
            r: rows per band
        And:
            n = b * r
        Elements in signature
        """
        best       = n, 1
        min_error  = float("inf")
        for r in range(1, n + 1):
            try:
                b = 1. / (tr ** r)
            except: 
                return best
            err = abs(n - b * r)
            if err < min_error:
                best, min_error = r, err

        return best

def jaccard(h1, h2):
    """
    Compute Jaccard Similarity between two minhash signatures.

    Make sure to only compute jaccard similarity for hashes created with same hash functions
    (i.e. same seed for random permutation)
    """
    return np.float(np.count_nonzero(h1 == h2)) /np.float(h2.size)

def run_jaccard_list(obj):
    """
    Compute jaccard similarity between two hash signatures

    Input
    -----
    Two hash signatures
    """
    x1, x2 = obj['signatures']

    return jaccard(np.array(x1), np.jaccard(x2))

def run_jaccard_array(obj):
    """
    Compute Jaccard Similarity between two hash signatures
    input:
        two hash signatures
    """
    x1, x2 = obj['signatures']
    return jaccard(x1, x2)

def run_near_duplicates(obj):
    '''
    Get near duplicates for a seed

    Input Dictionary
    ----------------
    :param hashcorp: dict
        minhash
    :param doc2lsh: dict
        lsh_signatures
    :param lshdict: dict
        lsh_signature
    :param seed: int
        seed document id
    :param threshold:
        jaccard similarity threshold

    Output
    ------
    :return: Document ID's
    :rtype:  set
    '''

    cluster = set([obj['seed']])

    # Get candidates and flatten list
    iterable   = [obj['lsh_dict'][sig] for sig in obj['doc_to_lsh'][obj['seed']]]
    candidates = set(itertools.chain.from_iterable(iterable))

    m1 = obj['hashcorp'][obj['seed']]

    for cand in candidates:

        if cand in cluster:
            continue

        m2 = obj['hashcorp'][cand]

        if jaccard(m2, m1) >= obj['threshold']:
            cluster.add(cand)

    return cluster

def run_getminhash(node):
    '''
    Compute minhash signatures for raw text.
    This functions takes a document and documentID as input and returns, the documentID and the corresponding minhash signature.
    The minhash signature is a set of NUM_PERM positiv integer values created with NUM_PERM hash functions.
    The minhash signature allows for a fast Jaccard similariy estimation of two documents. 
    input:
        node: dictionary with id,text
    output:
        node: dicionary with id,hashvalues (id,hashv)
    '''
    #compute hashes
    output_node={
            'id'    :   node['id'],
            'hashv' :   None
            }
    #compute minhash signature
    hashvalues=np.empty(NUM_PERM)
    hashvalues.fill(MAX_HASH)
    for token in node['text'].lower().split(): 
        hashvalues = np.minimum(get_permuted_hashes(token.encode('utf-8','ignore')), hashvalues)
    output_node['hashv']=hashvalues
    return output_node

def run_lsh_batch(obj):
    """
    Compute the Locality sensitive hashing signatures for a particular threshold.
    Utilize the fact that similar items generate similar hashcodes. 
    LSH signatures help to get a small set of candidates to which a document needs to be compared.
    To get an accurate estimate of Jaccard similarity, the similariy still needs to be computed using the minhash integer signature. 
    input:
        obj with threshold (default 0.9),id,hashvalues
    """
    if 'threshold' in obj:
        thr=obj['threshold']
    else:
        thr=0.8
    bandwidth=get_bandwidth(NUM_PERM, thr)#r
    bands=int(math.ceil(float(NUM_PERM)/float(bandwidth)))#b
    doc_to_lsh={}
    lsh_dict={}
    for node in obj['data']:
        key=node['id']
        hashvalues=node['hashv']
        #compute lsh 
        signatures = [sig for sig in get_lsh(hashvalues,bands)]
        #store signatures for this document
        doc_to_lsh[key]=signatures
        #store lsh signature to key
        for sig in signatures:
            if sig in lsh_dict:
                lsh_dict[sig].append(key)
            else:
                lsh_dict[sig]=[key]
    return doc_to_lsh,lsh_dict


def run_lsh(obj):
    """
    Compute the Locality sensitive hashing signatures for a particular threshold.
    Utilize the fact that similar items generate similar hashcodes. 
    LSH signatures help to get a small set of candidates to which a document needs to be compared.
    To get an accurate estimate of Jaccard similarity, the similariy still needs to be computed using the minhash integer signature. 
    input:
        obj with threshold (default 0.9),id,hashvalues
    """
    if 'threshold' in obj:
        thr=obj['threshold']
    else:
        thr=0.8
    bandwidth=get_bandwidth(NUM_PERM, thr)#r
    bands=int(math.ceil(float(NUM_PERM)/float(bandwidth)))#b
    doc_to_lsh={}
    lsh_dict={}
    key,hashvalues = obj['data']['id'],obj['data']['hashv']
    #compute lsh 
    signatures = [sig for sig in get_lsh(hashvalues,bands)]
    #store signatures for this document
    doc_to_lsh[key]=signatures
    #store lsh signature to key
    for sig in signatures:
        lsh_dict[sig]=[key]
    return doc_to_lsh,lsh_dict