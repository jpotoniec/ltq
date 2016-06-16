from pycnic.pycnic.core import WSGI, Handler
from pycnic.pycnic.errors import HTTP_400
from wsgiref.simple_server import make_server
from Engine import Engine
from rdflib import URIRef
from SparqlGraph import SparqlGraph

eng = Engine(SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql'), [], [])


def engine_state(eng):
    return {'positive': eng.positive, 'negative': eng.negative}


class CORSHandler(Handler):
    def before(self):
        self.response.set_header('Access-Control-Allow-Origin', '*')


class Hello(CORSHandler):
    def get(self, name="World"):
        return {"message": "Hello, %s!" % (name)}

    def post(self, name=""):
        ex = self.request.data.get('example')
        if not ex:
            raise HTTP_400('Uh-huh')
        return self.get(ex)


class AddExample(CORSHandler):
    def post(self, target):
        ex = self.request.data.get('example')
        if not ex:
            raise HTTP_400('`example` parameter required')
        ex = URIRef(ex)
        if ex not in eng.positive and ex not in eng.negative:
            if target == 'positive':
                eng.positive.append(ex)
            elif target == 'negative':
                eng.negative.append(ex)
        return engine_state(eng)


class RemoveExample(CORSHandler):
    def post(self):
        ex = self.request.data.get('example')
        if not ex:
            raise HTTP_400('`example` parameter required')
        ex = URIRef(ex)
        if ex in eng.positive:
            del eng.positive[eng.positive.index(ex)]
        if ex in eng.negative:
            del eng.negative[eng.negative.index(ex)]
        return engine_state(eng)


class GetState(CORSHandler):
    def get(self):
        return engine_state(eng)


class DoStep(CORSHandler):
    def get(self):
        if not eng.hypothesis_good_enough():
            eng.step()
            return {'new_positive': eng.ex_positive, 'new_negative': eng.ex_negative, 'hypothesis': eng.final_query()}
        else:
            results = [row['uri'] for row in eng.graph.select(eng.final_query())]
            return {'results': list(results), 'hypothesis': eng.final_query()}


class AssignLabels(CORSHandler):
    def post(self):
        labels = self.request.data.get('labels')
        if not labels:
            raise HTTP_400('`labels` parameter required')
        if len(labels) != len(eng.ex_positive) + len(eng.ex_negative):
            raise HTTP_400('`labels` has invalid length')
        eng.label_examples(labels[:len(eng.ex_positive)], labels[len(eng.ex_positive):])
        return engine_state(eng)


class App(WSGI):
    routes = [
        ('/', Hello()),
        ('/add/(positive|negative)', AddExample()),
        ('/remove', RemoveExample()),
        ('/state', GetState()),
        ('/step', DoStep()),
        ('/labels', AssignLabels())
    ]


def main():
    srv = make_server('127.0.0.1', 23456, App)
    srv.serve_forever()


if __name__ == '__main__':
    main()
