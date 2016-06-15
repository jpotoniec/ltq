import itertools
from Engine import Engine
from rdflib import URIRef
from SparqlGraph import SparqlGraph
from pprint import pprint


def urize(strings):
    result = []
    for item in strings:
        result.append(URIRef(item))
    return result


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


def main():
    graph = SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql')
    # european capitals
    target = urize([
        'http://dbpedia.org/resource/Athens',
        'http://dbpedia.org/resource/Budapest',
        'http://dbpedia.org/resource/Vienna',
        'http://dbpedia.org/resource/Brussels',
        'http://dbpedia.org/resource/Sofia',
        'http://dbpedia.org/resource/Zagreb',
        'http://dbpedia.org/resource/Nicosia',
        'http://dbpedia.org/resource/Prague',
        'http://dbpedia.org/resource/Copenhagen',
        'http://dbpedia.org/resource/Tallinn',
        'http://dbpedia.org/resource/Helsinki',
        'http://dbpedia.org/resource/Paris',
        'http://dbpedia.org/resource/Berlin',
        'http://dbpedia.org/resource/Dublin',
        'http://dbpedia.org/resource/Rome',
        'http://dbpedia.org/resource/Riga',
        'http://dbpedia.org/resource/Vilnius',
        'http://dbpedia.org/resource/Luxembourg_(city)',
        'http://dbpedia.org/resource/Valletta',
        'http://dbpedia.org/resource/Amsterdam',
        'http://dbpedia.org/resource/Warsaw',
        'http://dbpedia.org/resource/Lisbon',
        'http://dbpedia.org/resource/Bucharest',
        'http://dbpedia.org/resource/Bratislava',
        'http://dbpedia.org/resource/Ljubljana',
        'http://dbpedia.org/resource/Madrid',
        'http://dbpedia.org/resource/Stockholm',
        'http://dbpedia.org/resource/London',
    ])
    positive = urize(['http://dbpedia.org/resource/Warsaw',
                      'http://dbpedia.org/resource/Berlin',
                      'http://dbpedia.org/resource/Zagreb',
                      'http://dbpedia.org/resource/Nicosia',
                      'http://dbpedia.org/resource/Vilnius'
                      ])
    negative = urize(['http://dbpedia.org/resource/Oslo'])
    eng = Engine(graph, positive, negative)
    ctr = FeatureStats()
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
    main()
