import phonenumbers
from phonenumbers import geocoder, carrier, timezone

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
    return {"phonenumbers": results}
