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
    def setUp(self):
        pass

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

    def test_Polish_cities_above_200k_citizens(self):
        positive = urize(['http://dbpedia.org/resource/Gdańsk',
                          'http://dbpedia.org/resource/Kraków',
                          'http://dbpedia.org/resource/Lublin',
                          'http://dbpedia.org/resource/Poznań',
                          'http://dbpedia.org/resource/Toruń',
                          'http://dbpedia.org/resource/Bydgoszcz'
                          ])
        negative = urize([
            'http://dbpedia.org/resource/Lesser_Poland_Voivodeship',
            'http://dbpedia.org/resource/Silesian_Voivodeship',
            'http://dbpedia.org/resource/Masuria'
        ])
        # http://stat.gov.pl/statystyka-regionalna/rankingi-statystyczne/miasta-najwieksze-pod-wzgledem-liczby-ludnosci/, co najmniej 200 tys
        target = urize([
            'http://dbpedia.org/resource/Warsaw',
            'http://dbpedia.org/resource/Kraków',
            'http://dbpedia.org/resource/Łódź',
            'http://dbpedia.org/resource/Wrocław',
            'http://dbpedia.org/resource/Poznań',
            'http://dbpedia.org/resource/Gdańsk',
            'http://dbpedia.org/resource/Szczecin',
            'http://dbpedia.org/resource/Bydgoszcz',
            'http://dbpedia.org/resource/Lublin',
            'http://dbpedia.org/resource/Katowice',
            'http://dbpedia.org/resource/Białystok',
            'http://dbpedia.org/resource/Gdynia',
            'http://dbpedia.org/resource/Częstochowa',
            'http://dbpedia.org/resource/Radom',
            'http://dbpedia.org/resource/Sosnowiec',
            'http://dbpedia.org/resource/Toruń',
        ])
        result = run(positive, negative, target)
        self.assertAlmostEqual(result['f1'], 1)

# miasta mające powyżej 20000 os/km2 wg https://en.wikipedia.org/wiki/List_of_cities_by_population_density
# nie działa, bo w dbpedii nie ma takich danych, np http://dbpedia.org/resource/L'Hospitalet_de_Llobregat ma jako density wpisane auto, bo wikipedia je sama wylicza
#     target = ['https://en.wikipedia.org/wiki/Manila',
#               'https://en.wikipedia.org/wiki/Pateros,_Metro_Manila',
#               'https://en.wikipedia.org/wiki/Caloocan',
#               'https://en.wikipedia.org/wiki/Levallois-Perret',
#               'https://en.wikipedia.org/wiki/Le_Pré-Saint-Gervais',
#               'https://en.wikipedia.org/wiki/Neapoli,_Thessaloniki',
#               'https://en.wikipedia.org/wiki/Chennai',
#               'https://en.wikipedia.org/wiki/Vincennes',
#               'https://en.wikipedia.org/wiki/Delhi',
#               'https://en.wikipedia.org/wiki/Saint-Mandé',
#               'https://en.wikipedia.org/wiki/Dhaka',
#               'https://en.wikipedia.org/wiki/Bally,_Howrah',
#               'https://en.wikipedia.org/wiki/Kolkata',
#               'https://en.wikipedia.org/wiki/Bnei_Brak',
#               'https://en.wikipedia.org/wiki/Saint-Josse-ten-Noode',
#               'https://en.wikipedia.org/wiki/Montrouge',
#               'https://en.wikipedia.org/wiki/Malabon',
#               'https://en.wikipedia.org/wiki/Guttenberg,_New_Jersey',
#               'https://en.wikipedia.org/wiki/Pasig',
#               'https://en.wikipedia.org/wiki/Paris',
#               'https://en.wikipedia.org/wiki/Mislata',
#               'https://en.wikipedia.org/wiki/Macau',
#               'https://en.wikipedia.org/wiki/Kallithea',
#               'https://en.wikipedia.org/wiki/Nea_Smyrni',
#               'https://en.wikipedia.org/wiki/Howrah',
#               'https://en.wikipedia.org/wiki/Mumbai',
#               'https://en.wikipedia.org/wiki/Pasay',
#               'https://en.wikipedia.org/wiki/San_Juan,_Metro_Manila',
#               'https://en.wikipedia.org/wiki/Colombo',
#               'https://en.wikipedia.org/wiki/L\'Hospitalet_de_Llobregat',
#               'https://en.wikipedia.org/wiki/Union_City,_New_Jersey'
#               ]
#
#
# # positive = [
# #     'https://en.wikipedia.org/wiki/Manila',
# #     'https://en.wikipedia.org/wiki/Paris',
# #     'https://en.wikipedia.org/wiki/Union_City,_New_Jersey',
# #     'https://en.wikipedia.org/wiki/Dhaka',
# #     'https://en.wikipedia.org/wiki/Bally,_Howrah',
# #     'https://en.wikipedia.org/wiki/Kolkata',
# #     'https://en.wikipedia.org/wiki/Bnei_Brak',
# # ]
# positive = target.copy()
# negative = [
#     'https://en.wikipedia.org/wiki/Makati',
#     'https://en.wikipedia.org/wiki/West_New_York,_New_Jersey',
#     'https://en.wikipedia.org/wiki/Bydgoszcz'
# ]
# target = from_wikipedia(graph, target)
#     positive = from_wikipedia(graph, positive)
#     negative = from_wikipedia(graph, negative)

if __name__ == '__main__':
    unittest.main()
