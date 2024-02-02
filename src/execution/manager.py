class Manager(object):
    def __init__(self, func):
        self.func = func

    def __enter__(self):
        # Save a copy of the original globals() namespace
        self.original_globals = dict(globals())
        globals()['__name__'] = '__main__'
        return self
    
    def __exit__(self):
        # Restore the original globals() namespace
        globals().clear()
        globals().update(self.original_globals)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)