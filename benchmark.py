import gzip
from pprint import pprint
from SparqlGraph import SparqlGraph
from rdflib import URIRef
import random
from Engine import Engine
import itertools
import json
import time

dbpedia = SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql')


def load_queries():
    with gzip.open('selected_queries.txt.gz', 'rt') as f:
        for n, line in enumerate(f):
            if n % 2 == 1:
                yield line.strip()


def evaluate(graph, query, target):
    target = set(target)
    result = set([row['uri'] for row in graph.select(query)])
    missing = target - result
    unexpected = result - target
    tp = len(result & target)
    fp = len(unexpected)
    prec = tp / (tp + fp)
    recall = tp / len(target)
    return {'prec': prec, 'recall': recall, 'f1': 2 / (1 / prec + 1 / recall), 'missing': list(missing),
            'unexpected': list(unexpected)}


def benchmark(q):
    target = []
    for row in dbpedia.select(q):
        assert len(row.values()) == 1
        uri = list(row.values())[0]
        if isinstance(uri, URIRef):
            target.append(uri)
    target = list(set(target))
    if len(target) == 0:
        return None
    positive = random.sample(target, 5)
    negative = set(
        [URIRef('http://dbpedia.org/resource/Bydgoszcz'),
         URIRef('http://dbpedia.org/resource/Murmur_%28record_label%29'),
         URIRef('http://dbpedia.org/resource/Julius_Caesar'),
         URIRef('http://dbpedia.org/ontology/abstract'),
         URIRef('http://dbpedia.org/property/after'),
         URIRef('http://dbpedia.org/ontology/Agent'),
         ])
    negative = negative - set(target)
    assert len(negative) > 0
    eng = Engine(dbpedia, positive, list(negative))
    log = []
    for i in range(0, 10):
        n_steps = 0
        n_pos = 0
        n_neg = 0
        start = time.time()
        while not eng.hypothesis_good_enough():
            eng.step()
            n_steps += 1
            labels = []
            n_pos += len(eng.ex_positive)
            n_neg += len(eng.ex_negative)
            for ex in itertools.chain(eng.ex_positive, eng.ex_negative):
                labels.append(ex['uri'] in target)
            eng.label_examples(labels[:len(eng.ex_positive)], labels[len(eng.ex_positive):])
        end = time.time()
        print("Starting evaluation")
        e = evaluate(dbpedia, eng.final_query(), target)
        log_line = {'eval': e,
                    'runtime': {'steps': n_steps, 'requests_p': n_pos, 'requests_n': n_neg},
                    'query': eng.final_query(),
                    'perf': {'start': start, 'end': end}}
        print(e)
        missing = list(e['missing'])
        ue = list(e['unexpected'])
        if len(missing) > 0:
            if len(missing) > 5:
                missing = random.sample(missing, 5)
            eng.positive |= set(missing)
            log_line['added_positive'] = list(missing)
        if len(ue) > 0:
            if len(ue) > 5:
                ue = random.sample(ue, 5)
            eng.negative |= set(ue)
            log_line['added_negative'] = list(missing)
        log.append(log_line)
        if len(ue) == 0 and len(missing) == 0:
            break
    return log

def load_failed_queries():
    ok = set()
    failed = set()
    with open('log.json', 'rt') as f:
        for line in f:
            log = json.loads(line)
            if 'exception' in log:
                failed.add(log['query'])
            else:
                ok.add(log['query'])
    return failed-ok


def main():
    random.seed(12345)
    queries = load_queries()

    for q in queries:
        print(q)
        data = {'query': q}
        try:
            log = benchmark(q)
            data['log'] = log
        except Exception as e:
            data['exception'] = str(e)
        with open('log.json', 'at') as f:
            print(json.dumps(data), file=f)
        print("=============================================")
        # return


if __name__ == '__main__':
    main()
