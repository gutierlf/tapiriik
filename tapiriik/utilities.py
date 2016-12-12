import itertools

def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def get_list_of_dicts_from_dict_of_lists(d):
    return list(map(lambda a: dict(filter(None, a)),
                    itertools.zip_longest(*[[(k, v) for v in value]
                                            for k, value in d.items()])))