import unittest
from unittest.mock import MagicMock, call
from Selector import *
from rdflib import URIRef


class HypothesisTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_push(self):
        m1 = MagicMock(Selector)
        m2 = MagicMock(Selector)
        h = Hypothesis()
        h.push(m1)
        h.push(m2)
        self.assertEqual(list(h), [m1, m2])
        self.assertEqual(len(h), 2)
        x = h.pop()
        self.assertEqual(x, m2)
        self.assertEqual(list(h), [m1])
        self.assertEqual(len(h), 1)

    def test_emptypop(self):
        h = Hypothesis()
        self.assertIsNone(h.pop())

    def test_slice(self):
        selectors = [MagicMock(Selector) for i in range(0, 5)]
        h = Hypothesis()
        for s in selectors:
            h.push(s)
        self.assertIsInstance(h[2:4], Hypothesis)
        self.assertEqual(selectors[2], h[2])
        self.assertEqual(selectors[-1], h[-1])
        self.assertEqual(selectors[2:4], h[2:4])


class NamesGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.gen = NamesGenerator("?s", "?prefix")

    def test_root(self):
        self.assertEqual(self.gen[Selector.placeholder], "?s")

    def test_var(self):
        var1 = MagicMock(Variable)
        name1 = self.gen[var1]
        var2 = MagicMock(Variable)
        name2 = self.gen[var2]
        self.assertTrue(name1.startswith("?prefix"))
        self.assertTrue(name2.startswith("?prefix"))
        self.assertNotEqual(name1, name2)
        self.assertEqual(name1, self.gen[var1])
        self.assertEqual(name2, self.gen[var2])

    def test_n3(self):
        uri = MagicMock(URIRef)
        name = self.gen[uri]
        expected = call.n3().call_list()
        actual = uri.mock_calls
        self.assertEqual(expected, actual)
        self.assertEqual(name, uri.n3())


if __name__ == '__main__':
    unittest.main()
