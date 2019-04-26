"""Util decorators for ReSDK."""
import wrapt


@wrapt.decorator
def return_first_element(wrapped, instance, args, kwargs):
    """Return only the first element of the list returned by the wrapped function.

    Raise error if wrapped function does not return a list or if a list
    contains none or more than one element.
    """
    result = wrapped(*args, **kwargs)

    if not isinstance(result, list):
        raise TypeError('Result of decorated function must be a list')

    if len(result) != 1:
        raise RuntimeError('Function returned more than one result')

    return result[0]
