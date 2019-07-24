import itertools


class RequirementState(object):
    def __init__(self, iterable):
        # self.iterable = iterable
        self.iter = iter(iterable)
        self.done = False
        self.vals = []

    def iter_solutions(self):
        if self.done:
            return iter(self.vals)

        # chain vals so far & then gen the rest
        return itertools.chain(self.vals, self._gen_iter())

    def _gen_iter(self):
        # gen new vals, appending as it goes
        for new_val in self.iter:
            self.vals.append(new_val)
            yield new_val

        self.done = True
