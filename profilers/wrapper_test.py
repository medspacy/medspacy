from functools import wraps


class wrapper_test(object):
    def __init__(self, nm: str = ""):
        self.name = nm

    def _inner(self, fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            print("before func", self.name)
            retval = fun(self, *args, **kwargs)
            print("after func", self.name)
            return retval

        return wrapper

    def _decor(self, n):
        n = self.name
        print(n)

        def inner(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                print("before func", n)
                retval = func(*args, **kwargs)
                print("after func", n)
                return retval

            return wrapper

        return inner

    @_decor()
    def hello(self):
        print(self.name)


w = wrapper_test("HELLO!")
w.hello
