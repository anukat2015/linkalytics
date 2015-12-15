import sys

from collections import Mapping, Container, MutableSet, defaultdict
from functools import total_ordering
from abc import abstractmethod, ABCMeta

class propertycache:
    """
    Allows decoration
    """
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, obj, type=None):
        result = self.func(obj)
        self.cachevalue(obj, result)
        return result

    def cachevalue(self, obj, value):
        setattr(obj, self.name, value)

@total_ordering
class BaseFactor(metaclass=ABCMeta):
    """
    Factor Network Abstract Base Class
    ==================================

    Concrete implementations of FactorNodes should be easily
    hashable, recursive data structures.
    """
    def __init__(self, _id):
        self._id = str(_id)

    def __repr__(self):
        return '[{clsname} {id}]'.format(
            clsname=self.__class__.__name__,
            id=self.id
        )

    def __hash__(self):
        return self.id

    def __iter__(self):
        pass

    def __len__(self):
        pass

    def __contains__(self, other):
        pass

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    @propertycache
    def data(self):
        return self.suggest(_id, self.available(_id))

    @property
    def id(self):
        try:
            return int(self._id)
        except ValueError as e:
            msg = 'Provided node ID: {} cannot be cast as int'
            print(msg.format(self.id), file=sys.stderr)
            raise e

    @abstractmethod
    def lookup(self, ad_id, field):
        """ lookup takes an ad_id (as a string) and returns a list of
            field values for self.field.
        """
        pass

    @abstractmethod
    def reverse_lookup(self, field_value):
        """ reverse_lookup takes a field value and returns a list of
            ad_ids for ads having field_value in self.field.
        """
        pass

    @abstractmethod
    def available(self, ad_id):
        """
        Discover the set of factors available.
        """
        pass

    def suggest(self, ad_id, field, debug=False):
        field_values = self.lookup(ad_id, field)
        suggestions = {
            ad_id : {
                field: defaultdict(list)
            }
        }
        if not isinstance(field_values, list):
            raise KeyError(field_values)

        for field_value in field_values:
            ads = set(self.reverse_lookup(field, field_value))
            try:
                ads.remove(ad_id)
            # Means that the reverse_lookup failed to find the originating ad itself.
            except KeyError:
                continue

            for x in ads:
                suggestions[ad_id][field][field_value].append(x)
            if debug:
                for x in ads:
                    assert field_value == self.lookup(x)

        return suggestions

class DataNode(Container):

    def __init__(self):
        self._parent = None

    def __repr__(self):
        return '{parent}<DataNode>'.format(parent=self._parent)

    def __contains__(self):
        return None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

class FactorNode(BaseFactor):

    def __init__(self, _id):
        super().__init__(_id)
        self.data = DataNode()
        self.data.parent = self

    def __getitem__(self, item):
        return self.data[item]

    def traverse(self):