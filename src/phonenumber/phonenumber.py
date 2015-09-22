import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from .. utils import uniq_lod

def run(node):
    """ This returns any US phone numbers in the text.

        :param node:    a python dictionary with the 'text' field
    """
    results = []
    for match in phonenumbers.PhoneNumberMatcher(node['text'], "US"):
        results.append({
            "number"    : phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164),
            "location"  : geocoder.description_for_number(match.number, "en"),
            "carrier"   : carrier.name_for_number(match.number, "en"),
            "time_zone" : timezone.time_zones_for_number(match.number)
        })
    # http://stackoverflow.com/questions/11092511/python-list-of-unique-dictionaries
    return {"phonenumbers": uniq_lod(results, 'number')}
