
def ensure_type(type_):
    def decorator(func):
        def ensure(self, obj, **kwargs):
            if isinstance(obj, type_):
                func(self, obj, **kwargs)
            else:
                raise TypeError(
                    "Object obj=%s should be of type %s,"
                    "received a type=%s instead"
                    % (obj, type_, type(obj)))
        return ensure
    return decorator
