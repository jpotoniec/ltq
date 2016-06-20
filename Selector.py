class Variable(str):
    counter = 0

    def __new__(cls, name=None):
        if name is None:
            Variable.counter += 1
            return str.__new__(cls, "?anon{}".format(Variable.counter))
        else:
            return str.__new__(cls, name)

    def n3(self):
        return self


class NamesGenerator:
    def __init__(self, root, prefix):
        self._root = root
        self._prefix = prefix
        self._map = {}

    def __getitem__(self, item):
        if isinstance(item, Variable):
            if item == Selector.placeholder:
                return self._root
            if item in self._map:
                return self._map[item]
            else:
                name = self._prefix + str(len(self._map) + 1)
                self._map[item] = name
                return name
        else:
            return item.n3()


class Selector:
    placeholder = Variable("?var")

    def __init__(self, params):
        self._params = params
        self._text = self.sparql(NamesGenerator("?var", "?anon"))
        self._variables = set()
        for p in self._params:
            if isinstance(p, Variable):
                self._variables.add(p)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return 'Selector({})'.format(self._text)

    def __eq__(self, other):
        if isinstance(other, Selector):
            return self._text == other._text
        return False

    def __hash__(self):
        return hash(self._text)

    @property
    def variables(self):
        return self._variables


class TriplePatternSelector(Selector):
    def __init__(self, s, p, o):
        super().__init__((s, p, o))

    def sparql(self, gen: NamesGenerator):
        (s, p, o) = self._params
        return "{} {} {}.".format(gen[s], p.n3(), gen[o])


class FilterOpSelector(Selector):
    counter = 0

    def __init__(self, s, p, op, l):
        super().__init__((s, p, Variable(), op, l))

    def sparql(self, gen: NamesGenerator):
        (s, p, var, op, l) = self._params
        return "{0} {1} {2}. filter({2} {3} {4}).".format(gen[s], p.n3(), gen[var], op, l.n3())


class Hypothesis(list):
    push = list.append

    def __new__(cls, *args, **kwargs):
        return list.__new__(cls, *args, **kwargs)

    def pop(self):
        if len(self) > 0:
            return list.pop(self)
        else:
            return None

    def __getitem__(self, item):
        item = list.__getitem__(self, item)
        if isinstance(item, Selector):
            return item
        else:
            return Hypothesis(item)

    def sparql(self, gen=NamesGenerator("?s", "?anon_"), prefix="    ", suffix="\n"):
        result = ""
        for s in self:
            result += prefix + s.sparql(gen) + suffix
        return result
