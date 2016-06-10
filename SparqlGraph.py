import urllib.request
import urllib.parse
import defusedxml.pulldom
from xml.dom import pulldom
from rdflib import URIRef, Literal, BNode


class SparqlGraph:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    @staticmethod
    def _read_binding(doc):
        text = ""
        for event, node in doc:
            if event == pulldom.END_ELEMENT:
                text = text.strip()
                if node.tagName == 'uri':
                    return URIRef(text)
                elif node.tagName == 'literal':
                    if node.hasAttribute('xml:lang'):
                        lang = node.getAttribute('xml:lang')
                    else:
                        lang = None
                    if node.hasAttribute('datatype'):
                        dt = node.getAttribute('datatype')
                    else:
                        dt = None
                    return Literal(text, lang=lang, datatype=dt)
                elif node.tagName == 'bnode':
                    return BNode(text)
                else:
                    raise Exception("Unknown tag {} with value {}".format(node.tagName, text))
                    # return node.tagName, text
            elif event == pulldom.CHARACTERS:
                text += node.data
        raise Exception()

    @staticmethod
    def _read_result(doc):
        result = {}
        for event, node in doc:
            if event == pulldom.END_ELEMENT and node.tagName == 'result':
                return result
            if event == pulldom.START_ELEMENT and node.tagName == 'binding':
                var = node.getAttribute('name')
                if var[0] == '?' or var[0] == '!':
                    var = var[1:]
                val = SparqlGraph._read_binding(doc)
                result[var] = val
        raise Exception()

    def _query(self, text):
        # print(text)
        data = urllib.parse.urlencode({'query': text, 'format': 'text/xml'}).encode('utf-8')
        return urllib.request.urlopen(self.endpoint, data)

    def ask(self, text):
        with self._query(text) as f:
            text = f.read().decode('utf-8').strip().lower()
            if text == "true":
                return True
            elif text == "false":
                return False
            else:
                raise Exception()

    def select(self, text):
        with self._query(text) as f:
            doc = defusedxml.pulldom.parse(f)
            for event, node in doc:
                if event == pulldom.START_ELEMENT and node.tagName == 'result':
                    yield SparqlGraph._read_result(doc)

    def predicates(self, subject):
        for row in self.select('select distinct ?p where {{ {} ?p [].}}'.format(subject.n3())):
            yield row['p']

    def objects(self, subject, predicate):
        for row in self.select('select distinct ?o where {{ {} {} ?o.}}'.format(subject.n3(), predicate.n3())):
            yield row['o']

    def subjects(self, predicate, object):
        for row in self.select('select distinct ?s where {{ ?s {} {}.}}'.format(predicate.n3(), object.n3())):
            yield row['s']

    def __contains__(self, item):
        return self.ask('ask where {{ {} {} {}. }}'.format(item[0].n3(), item[1].n3(), item[2].n3()))

import re

class CachingGraph:

    def __init__(self, endpoint):
        self.sparql = SparqlGraph(endpoint)
        self.spo = {}
        self.pos = {}
        self.ignored_patterns = []

    def _is_ignored(self, p):
        for pattern in self.ignored_patterns:
            if pattern.match(p):
                return True
        return False

    def _fill_cache(self, subject):
        if subject not in self.spo:
            query = "select ?p ?o where {{ {} ?p ?o.}}".format(subject.n3())
            self.spo[subject] = {}
            for row in self.sparql.select(query):
                p = row['p']
                if self._is_ignored(p):
                    continue
                o = row['o']
                if p not in self.spo[subject]:
                    self.spo[subject][p] = []
                self.spo[subject][p].append(o)
                if p not in self.pos:
                    self.pos[p] = {}
                if o not in self.pos[p]:
                    self.pos[p][o] = []
                self.pos[p][o].append(subject)

    def predicates(self, subject):
        assert isinstance(subject, URIRef)
        self._fill_cache(subject)
        return self.spo[subject].keys()

    def objects(self, subject, predicate):
        assert isinstance(subject, URIRef), "{} is not literal".format(subject)
        self._fill_cache(subject)
        if predicate in self.spo[subject]:
            return self.spo[subject][predicate]
        else:
            return []

    def subjects(self, predicate, object):
        if predicate in self.pos and object in self.pos[predicate]:
            return self.pos[predicate][object]
        else:
            return []

    def __contains__(self, item):
        (s, p, o) = item
        self._fill_cache(s)
        return s in self.spo and p in self.spo[s] and o in self.spo[s][p]


if __name__ == '__main__':
    g = SparqlGraph('http://dbpedia.org/sparql')
    ha = URIRef('http://dbpedia.org/resource/Harps_and_Angels')
    rev = URIRef('http://dbpedia.org/property/rev')
    l = Literal('Blender', lang='en')
    am = URIRef('http://dbpedia.org/resource/AllMusic')
    # for i in g.subjects(rev, l):
    #     print(type(i), i)
    # print(g.ask('ask where {<http://dbpedia.org/resource/Harps_and_Angels> <http://dbpedia.org/property/rev> "Blender".}'))
    print((ha, rev, ha) in g)
