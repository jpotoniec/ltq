from Engine import Engine
from rdflib import URIRef
from SparqlGraph import SparqlGraph
from itertools import chain
import unittest


def urize(strings):
    result = []
    for item in strings:
        result.append(URIRef(item))
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


def run(positive, negative, target):
    positive = urize(positive)
    negative = urize(negative)
    target = urize(target)
    graph = SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql')
    eng = Engine(graph, positive, negative)
    while not eng.hypothesis_good_enough():
        eng.step()
        labels = []
        for ex in chain(eng.ex_positive, eng.ex_negative):
            if ex['uri'] in target:
                labels.append(True)
            else:
                labels.append(False)
        eng.label_examples(labels[:len(eng.ex_positive)], labels[len(eng.ex_positive):])
    q = eng.final_query()
    return evaluate(graph, q, target)


class EngineTests(unittest.TestCase):
    def test_capitals_of_EU(self):
        target = [
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
        ]
        positive = ['http://dbpedia.org/resource/Warsaw',
                    'http://dbpedia.org/resource/Berlin',
                    'http://dbpedia.org/resource/Zagreb',
                    'http://dbpedia.org/resource/Nicosia',
                    'http://dbpedia.org/resource/Vilnius'
                    ]
        negative = ['http://dbpedia.org/resource/Oslo']
        result = run(positive, negative, target)
        self.assertAlmostEqual(result['f1'], 1)

    #ten przykład jest za mały, bo wymagam przynajmniej 10 zaetykietowanych przykładów
    # def test_Apollo11(self):
    #     target = ['http://dbpedia.org/resource/Neil_Armstrong',
    #               'http://dbpedia.org/resource/Buzz_Aldrin',
    #               'http://dbpedia.org/resource/Michael_Collins_(astronaut)'
    #               ]
    #     positive = ['http://dbpedia.org/resource/Neil_Armstrong', 'http://dbpedia.org/resource/Buzz_Aldrin']
    #     negative = ['http://dbpedia.org/resource/Clive_Owen',
    #                 'http://dbpedia.org/resource/Paul_Girvan_(judge)',
    #                 'http://dbpedia.org/resource/Phil_Lewis_(baseball)']
    #     result = run(positive, negative, target)
    #     self.assertAlmostEqual(result['f1'], 1)


if __name__ == '__main__':
    unittest.main()
