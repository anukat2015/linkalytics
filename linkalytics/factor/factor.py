from abc import ABCMeta, abstractmethod
import collections
import re

class FactorLookupDidNotReturnList(Exception):
    def __init__(self, values):
        self.values = values

    def __str__(self):
        return "Factor: Instead of a list, we got `%s` (type: %s)".format(str(self.values), type(self.values))

class FactorReverseLookupFailedToFindSelf(Exception):
    def __init__(self, ad_id, ads):
        self.ad_id = ad_id
        self.ads = ads

    def __str__(self):
        return "Factor: reverse_lookup did not return %s in %s".format(self.ad_id, self.ads)

class FactorBase(metaclass=ABCMeta):
    """ Factor defines the abstract functions required for a factor.

        A factor implements two functions:
            lookup
            reverse_lookup

        One must also use `super(Foo, self).__init__(field_name)` to
        initialize the class. This records the field to be used in the
        factor.

        The `lookup` function takes an ad_id (as a string) as an
        argument, and returns a list of the field values for this
        factor.

        The `reverse_lookup` function takes a field value and returns a
        list of ad_ids matching (exactly) the same field value.

        For instance, if a database contains the following records

        id |    email       | phone
        0  | foo@bar.com    | 123 456 789
        1  | bar@baz.com    | 123 456 789

        Then,

            email = Factor("email")
            email.lookup("0")
            # ["foo@bar.com"]
            email.lookup("1")
            # ["bar@baz.com"]
            email.reverse_lookup("foo@bar.com")
            # ["0"]
            phone = Factor("phone")
            phone.reverse_lookup("123 456 789")
            # ["0", "1"]
            phone.suggest("0")
            # {"0": {"phone": {"1": "123 456 789"}}}
    """
    def suggest(self, ad_id, field, debug=False):
        """ The suggest function suggests other ad_ids that share this
            field with the input ad_id.

            If the debug field is set to True, this will ensure that the
            returned ad_ids *actually* match the field values. The debug
            option can be expensive to run, since it makes multiple
            calls to self.lookup.

            The number of calls to reverse_lookup is O(N) where N is
            the expected number of values in the field for this factor.
            This number is typically very small.

            If debugging, the expected number of calls to either
            reverse_lookup or lookup is O(N*M) where N is the expected
            number of values in the field for this factor and M is the
            expected number of ads matching this field.
        """
        field_values = self.lookup(ad_id, field)
        suggestions = {
            ad_id : {
                field: collections.defaultdict(list)
            }
        }
        if isinstance(field_values, list):
            for field_value in field_values:
                ads = set(self.reverse_lookup(field, field_value))
                try:
                    ads.remove(ad_id)

                # Means that the reverse_lookup failed to find the originating ad itself.
                except KeyError:
                    raise KeyError("Did not find %s %s" % (ad_id, ads))

                for x in ads:
                    suggestions[ad_id][field][field_value].append(x)

                if debug:
                    for x in ads:
                        assert field_value == self.lookup(x)
        else:
            raise KeyError(field_values)

        return suggestions

    @abstractmethod
    def lookup(self, ad_id):
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
