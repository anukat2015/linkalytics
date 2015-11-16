from ... utils import with_test
from . instagrammer import run

@with_test(run, 'instagram')
def data():
    yield ({"text": "https://instagram.com/instagram/"}, [
            {"id": "25025320", "username": "instagram"}
        ])
    yield ({"text": "Follow us on INSTAGRAM; instagram"}, [
            {"id": "25025320", "username": "instagram"}
        ])
    yield ({"text": "iNsTaGRAM@instagram"}, [
            {"id": "25025320", "username": "instagram"}
        ])
    yield ({"text": "my Instagram is INSTAGRAM"}, [
            {"id": "25025320", "username": "instagram"}
        ])
    yield ({"text": '<a rel="nofollow" target="_blank" href="http://instagram.com/instagram">Instagram.com/instagram</a>'}, [
            {"id": "25025320", "username": "instagram"}
        ])
    #yield ({"text": "no instagram username"}, [])
