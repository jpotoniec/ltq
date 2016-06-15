from pycnic.pycnic.core import WSGI, Handler
from pycnic.pycnic.errors import HTTP_400
from wsgiref.simple_server import make_server
from Engine import Engine
from rdflib import URIRef
from SparqlGraph import SparqlGraph

eng = Engine(SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql'), [], [])


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
        return {'positive': eng.positive, 'negative': eng.negative}


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
        return {'positive': eng.positive, 'negative': eng.negative}


class App(WSGI):
    routes = [
        ('/', Hello()),
        ('/add/(positive|negative)', AddExample()),
        ('/remove', RemoveExample())
    ]


def main():
    srv = make_server('127.0.0.1', 23456, App)
    srv.serve_forever()


if __name__ == '__main__':
    main()
