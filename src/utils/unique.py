
def uniq_lod(lod, key):
    """ This function returns a list of unique dictionaries using the
        given key.

        :param lod:     a list of dictionaries to 'uniq'
        :param key:     the key to use for the dictionary identity
    """
    return list({v[key]:v for v in lod}.values())
