import asyncio
from .debounce import debounce

def debounce_async(secs):
    def decorator(func):

        @debounce(secs)
        def intermediate_function(*args, **kwargs):
            asyncio.run(func(*args, **kwargs))

        # TODO: make the wrapper async as well
        def wrapper(*args, **kwargs):
            intermediate_function(*args, **kwargs)

        return wrapper
    return decorator