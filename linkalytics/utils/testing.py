from nose.tools import nottest

def check_fields(result, expected):
    for key in expected:
        if key in result:
            assert result[key] == expected[key], "{} != {} for key '{}'".format(result[key], expected[key], key)
        else:
            assert False, "Could not find expected key '{}'".format(key)

def check_all_results(results, expected_results, field):
    if expected_results:
        for result, expected in zip(results[field], expected_results):
            return check_fields(result, expected)
    else:
        assert results[field] == expected_results, "Expected empty results; got {}".format(results[field])

@nottest
def with_test(func_under_test, field):
    def decorator(f):
        """ Decorator for running a test case for enhancers.

            :param func_under_test:     the function to test
            :param field:               the expected output field
            :param f:                   a generator for tuples of input
                                            and expected output
        """
        def test_case():
            for node, result in f():
                yield check_all_results, func_under_test(node), result, field
        return test_case
    return decorator
