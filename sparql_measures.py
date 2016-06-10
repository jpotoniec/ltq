from SparqlGraph import SparqlGraph
from rdflib import URIRef
from pprint import pprint
import random
import itertools
import pickle
import gzip


def urize(strings):
    result = []
    for item in strings:
        result.append(URIRef(item))
    return result


def find_best_properties(graph, positive, negative):
    if len(positive) > 100:
        positive = random.sample(positive, 100)
    if len(negative) > 100:
        negative = random.sample(negative, 100)
    n_pos = len(positive)
    n_neg = len(negative)
    pos = " ".join([u.n3() for u in positive])
    neg = " ".join([u.n3() for u in negative])
    query = 'select distinct ?p  (count(distinct ?s)/' + str(n_pos) + '-count(distinct ?t)/' + str(n_neg) + ' as ?m)' + '''
where
{
  {
  ?s ?p [].
  values ?s {''' + pos + '''
  }
         filter(isIRI(?p))
         }
  union
  {
    ?t ?p [].
    values ?t { ''' + neg + '''
  }
         filter(isIRI(?p))
    }
}
group by ?p
having (?m > .75)
order by desc(?m)
'''
    print(query)
    properties = []
    for row in graph.select(query):
        properties.append(row['p'])
        # print(row)
    return properties[0]


def find_best_po(graph, positive, negative, prefix):
    if len(positive) > 100:
        positive = random.sample(positive, 100)
    if len(negative) > 100:
        negative = random.sample(negative, 100)
    n_pos = len(positive)
    n_neg = len(negative)
    pos = " ".join([u.n3() for u in positive])
    bgp = ""
    for p, o in prefix:
        bgp += "?s {} {} .\n".format(p.n3(), o.n3())
    if n_neg > 0:
        neg = " ".join([u.n3() for u in negative])
        query = 'select distinct ?p ?o (count(distinct ?s)/' + str(n_pos) + '-count(distinct ?t)/' + str(
            n_neg) + ' as ?m)' + '''
    where
    {
      { ''' + bgp + '''
      ?s ?p ?o.
      values ?s {''' + pos + '''
      }
             filter(isIRI(?p))
             }
      union
      {
        ?t ?p ?o.
        values ?t { ''' + neg + '''
      }
             filter(isIRI(?p))
        }
    }
    group by ?p ?o
    having (?m > .75)
    order by desc(?m)
    '''
    else:
        query = 'select distinct ?p ?o (count(distinct ?s)/' + str(n_pos) + ' as ?m)' + '''
    where
    {
      {''' + bgp + '''
      ?s ?p ?o.
      values ?s {''' + pos + '''
      }
             filter(isIRI(?p))
             }
    }
    group by ?p ?o
    having (?m > .75)
    order by desc(?m)
    '''
    result = graph.select(query)
    query = ""
    for row in result:
        query += "({} {})".format(row['p'].n3(), row['o'].n3())
    query = '''
    select ?p ?o (count(distinct ?s) as ?c)
where
{
  ?s ?p ?o.
  values (?p ?o) {''' + query + '''
  }
}
group by ?p ?o
order by asc(?c)'''
    result = []
    for row in graph.select(query):
        result.append((row['p'], row['o']))
    for item in result:
        if item not in prefix:
            return item
    return None, None


def pick_examples(graph, p, o, positive, negative):
    uris = " ".join([u.n3() for u in itertools.chain(positive, negative)])
    p = p.n3()
    if o is not None:
        o = o.n3()
    else:
        o = "[]"
    x = p + " " + o
    query = '''
    select distinct ?uri ?comment
where
{
  ?uri ''' + x + ''' .
  optional {?uri rdfs:comment ?comment}
  minus
  {
  ?uri ''' + x + ''' .
  values ?uri {''' + uris + ''' }
    }
  }
limit 3'''
    return [row for row in graph.select(query)]


def wrap(line, prefix=""):
    line = line.split()
    n = 0
    result = ""
    for word in line:
        if n >= 80:
            result += '\n'
            n = 0
        if n == 0:
            result += prefix
        result += word + ' '
        n += len(word)
    return result


def main():
    graph = SparqlGraph('https://semantic.cs.put.poznan.pl/blazegraph/sparql')
    # positive = urize(['http://dbpedia.org/resource/Buzz_Aldrin',
    #                   'http://dbpedia.org/resource/Michael_Collins_(astronaut)',
    #                   'http://dbpedia.org/resource/Neil_Armstrong'
    #                   ])
    # negative = urize([
    #     'http://dbpedia.org/resource/J._R._R._Tolkien'
    # ])
    # european capitals
    positive = urize(['http://dbpedia.org/resource/Warsaw',
                      'http://dbpedia.org/resource/Berlin'])
    negative = urize(['http://dbpedia.org/resource/New_York_City'])
    fn = "last.pickle.gz"
    try:
        with gzip.open(fn, 'rb') as f:
            positive, negative = pickle.load(f)
            print("+", " ".join([uri.n3() for uri in positive]))
            print("-", " ".join([uri.n3() for uri in negative]))
    except:
        pass
    prefix = []
    while True:
        with gzip.open(fn, 'wb') as f:
            pickle.dump([positive, negative], f)
        # pprint(positive)
        # pprint(negative)
        print("================")
        while True:
            p, o = find_best_po(graph, positive, negative, prefix)
            if p is None:
                print("Fallback!")
                p, o = find_best_po(graph, positive, [], prefix)
                assert p is not None
                prefix.append((p, o))
                print(prefix)
            else:
                break
        print(p, o)
        examples = pick_examples(graph, p, o, positive, negative)
        if len(examples) == 0:
            break
        for n, ex in enumerate(examples):
            print("{}. {}".format(n + 1, ex['uri']))
            if 'comment' in ex:
                print(wrap(ex['comment'], "    "))
        new_positive = input('positive> ')
        new_positive = [int(item) - 1 for item in new_positive.split()]
        for n, ex in enumerate(examples):
            uri = ex['uri']
            if n in new_positive:
                positive.append(uri)
                try:
                    del negative[negative.index(uri)]
                except:
                    pass
            else:
                negative.append(uri)
                try:
                    del positive[positive.index(uri)]
                except:
                    pass
    print("I'm done for!")


# q = """
#     select distinct ?p
# where
# {
#   ?s ?p ?o.
#   values ?s {
#                       <http://dbpedia.org/resource/Michael_Collins_(astronaut)>
#                       <http://dbpedia.org/resource/Neil_Armstrong>
#   }
# }
# limit 10
# """
#     for row in graph.select(q):
#         print(row)


if __name__ == '__main__':
    main()
