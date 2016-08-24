from pycnic.pycnic.core import WSGI, Handler
from pycnic.pycnic.errors import HTTP_400
from wsgiref.simple_server import make_server
from Engine import Engine
from rdflib import URIRef
from SparqlGraph import SparqlGraph
import uuid
import re

engine_db = {}


def engine_state(eng):
    return {'positive': list(eng.positive), 'negative': list(eng.negative)}


class CORSHandler(Handler):
    def _init_engine(self):
        id = str(uuid.uuid4())
        self.response.set_cookie('engine', id)
        self.eng = Engine(SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql'), [], [])
        engine_db[id] = self.eng

    def before(self):
        global engine_db
        print(self.request.cookies)
        self.eng = None
        if 'engine' in self.request.cookies:
            id = self.request.cookies['engine']
            if id in engine_db:
                self.eng = engine_db[id]
        if self.eng is None:
            self._init_engine()


class AddExample(CORSHandler):
    re_wiki = re.compile(r'^https?://(en.wikipedia.org/wiki/.*)$', re.I)

    def post(self, target):
        ex = self.request.data.get('example')
        if not ex:
            raise HTTP_400('`example` parameter required')
        m = AddExample.re_wiki.match(ex)
        if m is not None:
            q = 'select ?uri where {{?uri <http://xmlns.com/foaf/0.1/isPrimaryTopicOf> <{}>. }} limit 1'.format(
                'http://' + m.group(1))
            for row in self.eng.graph.select(q):
                ex = row['uri']
        ex = URIRef(ex)
        if ex in self.eng.positive:
            self.eng.positive -= set(ex)
        elif ex in self.eng.negative:
            self.eng.negative -= set(ex)
        if target == 'positive':
            self.eng.positive.add(ex)
        elif target == 'negative':
            self.eng.negative.add(ex)
        return engine_state(self.eng)


class RemoveExample(CORSHandler):
    def post(self):
        ex = self.request.data.get('example')
        if not ex:
            raise HTTP_400('`example` parameter required')
        ex = URIRef(ex)
        if ex in self.eng.positive:
            self.eng.positive -= set(ex)
        if ex in self.eng.negative:
            self.eng.negative -= set(ex)
        return engine_state(self.eng)


class GetState(CORSHandler):
    def get(self):
        return engine_state(self.eng)


class DoStep(CORSHandler):
    def get(self):
        if not self.eng.hypothesis_good_enough():
            self.eng.step()
            return {'new_positive': self.eng.ex_positive, 'new_negative': self.eng.ex_negative,
                    'hypothesis': self.eng.final_query()}
        else:
            results = [row['uri'] for row in self.eng.graph.select(self.eng.final_query())]
            return {'results': list(results), 'hypothesis': self.eng.final_query()}


class AssignLabels(CORSHandler):
    def post(self):
        labels = self.request.data.get('labels')
        if not labels:
            raise HTTP_400('`labels` parameter required')
        if len(labels) != len(self.eng.ex_positive) + len(self.eng.ex_negative):
            raise HTTP_400('`labels` has invalid length')
        self.eng.label_examples(labels[:len(self.eng.ex_positive)], labels[len(self.eng.ex_positive):])
        return engine_state(self.eng)


class RestartEngine(CORSHandler):
    def get(self):
        self._init_engine()
        return {}


class App(WSGI):
    routes = [
        ('/add/(positive|negative)', AddExample()),
        ('/remove', RemoveExample()),
        ('/state', GetState()),
        ('/step', DoStep()),
        ('/labels', AssignLabels()),
        ('/restart', RestartEngine())
    ]


def main():
    srv = make_server('127.0.0.1', 23456, App)
    srv.serve_forever()


if __name__ == '__main__':
    main()
