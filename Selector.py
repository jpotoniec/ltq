class Selector:
    placeholder = "?var"

    def __init__(self, text):
        self._text = text

    def get(self, var):
        return self._text.replace(Selector.placeholder, var) + "\n"

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


class POSelector(Selector):
    def __init__(self, p, o):
        super().__init__("{} {} {}.".format(Selector.placeholder, p.n3(), o.n3()))


class SPSelector(Selector):
    def __init__(self, s, p):
        super().__init__("{} {} {}.".format(s.n3(), p.n3(), Selector.placeholder))


class FilterNotExistsSelector(Selector):
    def __init__(self, nested: Selector):
        super().__init__("filter not exists {{ {} }}".format(nested._text))
