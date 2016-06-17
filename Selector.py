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


class Selector:
    placeholder = Variable("?var")

    def __init__(self, text):
        self._text = text
        self._variables = []

    def get(self, var):
        return self._text.replace(Selector.placeholder, var)

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
        super().__init__("{} {} {}.".format(s.n3(), p.n3(), o.n3()))
        for x in (s, p, o):
            if isinstance(x, Variable):
                self._variables.append(x)


class FilterOpSelector(Selector):
    counter = 0

    def __init__(self, s, p, op, l):
        FilterOpSelector.counter += 1
        super().__init__(
            "{0} {1} ?filter{2}. filter(?filter{2} {3} {4}).".format(s.n3(), p.n3(), FilterOpSelector.counter,
                                                                     op, l.n3()))
        if isinstance(s, Variable):
            self._variables.append(s)


class FilterNotExistsSelector(Selector):
    def __init__(self, nested: Selector):
        super().__init__("filter not exists {{ {} }}".format(nested._text))
