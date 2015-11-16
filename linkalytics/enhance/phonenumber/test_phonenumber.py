from ... utils import with_test

from . import phonenumber

@with_test(phonenumber.run, 'phonenumbers')
def data():
    yield (
        { 'text': '1800295 408-291-2521' }, [
            {
                'carrier': '',
                'location': 'California',
                'number': '+14082912521',
                'time_zone': ('America/Los_Angeles',)
            }
        ]
    )

