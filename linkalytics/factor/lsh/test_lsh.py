from unittest import TestCase

from . import nearduplicates

corpus = (
    'Vice President Biden announced that he will not enter the race for the 2016 presidential nomination',
    'Vice President Joe Biden said that he will not enter the race for the 2016 presidential nomination',
    'This is exactly the probability of collision we would expect if the hash function assigned truly random hash codes to every key',
    'This is exactly the probability of collision one would expect if our hash function assigned a truly random hash to every key'
)

class TestNearDuplicates(TestCase):

    def test_duplicates(self):

        hashcorpus = [
            nearduplicates.run_getminhash({'id': i, 'text': x})
            for i, x in enumerate(corpus)
            ]
        doc_to_lsh, lsh_dict = nearduplicates.run_lsh_batch(
            {
                'threshold': 0.7,
                'data': hashcorpus
            }
        )
        hashdict = {
            obj['id']: obj['hashv'] for obj in hashcorpus
        }
        for i in range(4):

            cluster = nearduplicates.run_near_duplicates(
                {
                    'seed': i,
                    'hashcorp': hashdict,
                    'doc_to_lsh': doc_to_lsh,
                    'lsh_dict': lsh_dict,
                    'threshold': 0.7
                }
            )

            dup = (cluster - {i}).pop()


            self.assertEqual(corpus[dup], corpus[-(i-1)])
