import gzip
from rdflib import Graph, URIRef
import re
from SparqlGraph import SparqlGraph
import urllib
from urllib.parse import unquote_plus
from random import Random

r_select = re.compile(r'select\s+\?S+\s+where', re.I)
r_var = re.compile(r'(?:\?|\$)\w+', re.I)
dbpedia = SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql')


def process_query(q, output):
    q = unquote_plus(q)
    if 'select' not in q.lower():
        return False
    m = r_select.search(q)
    if m is None:
        vars = set(r_var.findall(q))
        if len(vars) == 0:
            return False
        if len(vars) > 1:
            return False
    try:
        # result = dbpedia.select(q)
        # result = list(result)
        # print(len(result), file=output)
        print(q, file=output)
        return True
    except urllib.error.HTTPError as e:
        return False


def extract_queries():
    g = Graph()
    r = re.compile(r'^\s*sp:text "(.*)"\s*.\s*$')
    with gzip.open('queries.txt.gz', 'wt') as output:
        with gzip.open('LSQ-DBpedia351.ttl.gz', 'rt') as f:
            for n, line in enumerate(f):
                # if n > 10000:
                #     return
                if n % 1000 == 0:
                    print(n)
                m = r.match(line)
                if m is not None:
                    q = m.group(1)
                    process_query(q, output)


def select_queries():
    with gzip.open('queries.txt.gz', 'rt') as f:
        queries = [line.strip() for line in f]
    r = Random(0xbeef)
    r.shuffle(queries)
    n = 0
    with gzip.open('selected_queries.txt.gz', 'wt') as f:
        for q in queries:
            try:
                result = set()
                for row in dbpedia.select(q):
                    if len(row.values()) != 1:
                        continue
                    uri = list(row.values())[0]
                    if isinstance(uri, URIRef):
                        result.add(uri)
                result = list(result)
                if len(result) >= 20:
                    print(len(result), file=f)
                    print(q, file=f)
                    n += 1
                    print(n)
                    if n >= 50:
                        break
            except urllib.error.HTTPError as e:
                pass


if __name__ == '__main__':
    select_queries()

# for data from http://aksw.github.io/LSQ/
