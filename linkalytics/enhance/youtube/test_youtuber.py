from ... utils import with_test

from . youtuber import run

@with_test(run, 'youtube')
def data():
    yield (
        {
            "text": "Have you seen this https://www.youtube.com/watch?t=3&v=ToyoBTiwZ6c youtube video with Super Marioll"
        }, [
            {
                'username': 'IGNentertainment',
                'video_id': 'toyobtiwz6c'
            }
        ]
    )