import itertools
from Engine import Engine
from rdflib import URIRef
from SparqlGraph import SparqlGraph
from pprint import pprint
from EngineTests import urize, evaluate


def wrap(line, prefix=""):
    line = line.split()
    n = 0
    result = ""
    for word in line:
        if n >= 160:
            result += '\n'
            n = 0
        if n == 0:
            result += prefix
        result += word + ' '
        n += len(word)
    return result


class FeatureStats:
    def __init__(self):
        self._data = {}

    def add(self, key, pos_hits, positive, neg_hits, negative):
        args = (pos_hits, positive, neg_hits, negative, 1)
        if key not in self._data:
            self._data[key] = [0, 0, 0, 0, 0]
        assert len(self._data[key]) == len(args)
        for i in range(len(args)):
            self._data[key][i] += args[i]
        return self._data[key]

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)


def simulate_user(target, questions):
    result = []
    for n, ex in enumerate(questions):
        if ex['uri'] in target:
            result.append(str(n + 1))
    result = " ".join(result)
    print("Selected:", result)
    return result


def evaluate(graph, query, target):
    tp = 0
    fp = 0
    missing = target.copy()
    unexpected = []
    for row in graph.select(query):
        if row['uri'] in target:
            tp += 1
            del missing[missing.index(row['uri'])]
        else:
            fp += 1
            unexpected.append(row['uri'])
    prec = tp / (tp + fp)
    recall = tp / len(target)
    return {'prec': prec, 'recall': recall, 'f1': 2 / (1 / prec + 1 / recall), 'missing': missing,
            'unexpected': unexpected}


def from_wikipedia(graph, links):
    result = []
    import re
    r = re.compile('^https://', re.I)
    for link in links:
        link = r.sub('http://', link)
        query = '''
        select distinct ?uri
        where
        {{
            ?uri foaf:isPrimaryTopicOf {}.
        }}
        '''.format(URIRef(link).n3())
        uri = [row['uri'] for row in graph.select(query)]
        assert len(uri) == 1, (uri, link)
        result.append(uri[0])
    return result


def main():
    graph = SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql')

    eng = Engine(graph, positive, negative)
    while not eng.hypothesis_good_enough():
        print("================")
        print("Current selectors:", eng.hypothesis)
        eng.step()
        for n, ex in enumerate(eng.ex_positive):
            print("{}. {}".format(n + 1, ex['uri']))
            if 'comment' in ex:
                print(wrap(ex['comment'], "    "))
        for n, ex in enumerate(eng.ex_negative):
            print("{}. {}".format(n + 1 + len(eng.ex_positive), ex['uri']))
            if 'comment' in ex:
                print(wrap(ex['comment'], "    "))
        # new_positive = input('positive> ')
        new_positive = simulate_user(target, itertools.chain(eng.ex_positive, eng.ex_negative))
        new_positive = [int(item) for item in new_positive.split()]
        labels = []
        for n in range(0, len(eng.ex_positive) + len(eng.ex_negative)):
            if n + 1 in new_positive:
                labels.append(True)
            else:
                labels.append(False)
        eng.label_examples(labels[:len(eng.ex_positive)], labels[len(eng.ex_positive):])
    print("I'm done for!")
    q = eng.final_query()
    print(q)
    pprint(evaluate(graph, q, target))


if __name__ == '__main__':
    # from EngineTests import EngineTests
    # EngineTests().test_capitals_of_EU()
    main()
