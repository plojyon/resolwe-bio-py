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
        raise TypeError("Result of decorated function must be a list")

    if len(result) != 1:
        raise RuntimeError("Function returned more than one result")

    return result[0]


@wrapt.decorator
def assert_object_exists(wrapped, instance, args, kwargs):
    """Verify that objects exists on server (e.g. has `id` defined)."""
    # Property decorator messes up things, so self is not given as
    # `instance` argment, but as the first element of *args
    if instance is None:
        instance = args[0]
        member = "attribute"
    else:
        member = "method"

    if instance.id is None:
        raise ValueError(
            "Instance must be saved before accessing `{}` {}.".format(
                wrapped.__name__,
                member,
            )
        )
    return wrapped(*args, **kwargs)
