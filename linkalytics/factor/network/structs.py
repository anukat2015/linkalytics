class AttrDict:
    """
    Helper class to provide attribute like access (read and write) to
    dictionaries. Used to provide a convenient way to access both results and
    nested dsl dicts.
    """
    def __init__(self, d):
        super(self.__class__, self).__setattr__('_d_', d)

    def __contains__(self, key):
        return key in self._d_

    def __nonzero__(self):
        return bool(self._d_)

    __bool__ = __nonzero__

    def __dir__(self):
        return list(self._d_.keys())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return other._d_ == self._d_
        return other == self._d_

    def __repr__(self):
        return repr(self._d_)

    def __getattr__(self, attr_name):
        try:
            return self.__class__(self._d_[attr_name])
        except KeyError:
            if attr_name.startswith('_'):
                raise AttributeError(
                    '%r object has no attribute %r' % (self.__class__.__name__, attr_name)
                )
            else:
                self._d_[attr_name] = {}
                return self.__getattr__(attr_name)

    def __delattr__(self, attr_name):
        try:
            del self._d_[attr_name]
        except KeyError:
            raise AttributeError(
                '%r object has no attribute %r' % (self.__class__.__name__, attr_name)
            )

    def __getitem__(self, key):
        if key in self._d_:
            return self.__class__(self._d_[key])
        else:
            self._d_[key] = self.__class__({})
            return self._d_[key]

    def __setitem__(self, key, value):
        self._d_[key] = value

    def __delitem__(self, key):
        del self._d_[key]

    def __setattr__(self, name, value):
        if name in self._d_ or not hasattr(self.__class__, name):
            self._d_[name] = value
        else:
            # there is an attribute on the class (could be property, ..)
            # don't add it as field
            super(self.__class__, self).__setattr__(name, value)

    def __iter__(self):
        return iter(self._d_)

    def to_dict(self):
        return self._d_

class Node:
    """
    Custom parametric data type.

    Has more consistent hashing behavior than integers
    and strings when used as keys to dictionaries.

    Example
    -------
    >>> hash(Node(500)) == hash(Node('500'))
    True

    >>> hash(500) == hash('500')
    False
    """
    def __init__(self, _id):
        self._id = _id

    def __repr__(self):
        return '<V|{id}|>'.format(
                clsname=self.__class__.__name__,
                id=self.id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    @property
    def id(self):
        return str(self._id)

class Messenger:
