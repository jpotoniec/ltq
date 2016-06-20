from Selector import *
import itertools


class ContingencyMatrix:
    def __init__(self):
        self.tp = 0
        self.tn = 0
        self.fp = 0
        self.fn = 0

    def __str__(self):
        return 'tp={} fp={} fn={} tn={}'.format(self.tp, self.fp, self.fn, self.tn)


class Engine:
    def __init__(self, graph, positive, negative):
        self.graph = graph
        self.positive = positive
        self.negative = negative
        self.hypothesis = Hypothesis()
        self.hypothesis_cm = ContingencyMatrix()
        self.ex_positive = None
        self.ex_negative = None

    def _sparql_list(self, l, sep=" "):
        return sep.join([item.n3() for item in l])

    def _sparql_positive(self, sep=" "):
        return self._sparql_list(self.positive, sep)

    def _sparql_negative(self, sep=" "):
        return self._sparql_list(self.negative, sep)

    def _sparql_measure(self, tp="?tp", fp="?fp"):
        args = {
            'tp': tp,
            'fp': fp,
            'n_pos': len(self.positive),
            'n_neg': len(self.negative)
        }
        # return "({tp}/{n_pos}-{fp}/{n_neg} as ?measure)".format_map(args)
        return "({tp}/({tp}+{fp}) as ?precision) ({tp}/{n_pos} as ?recall) (2/((1/?precision)+(1/?recall)) as ?measure)".format_map(
            args)

    def _args(self, root):
        s_gen = NamesGenerator("?s", "?s_anon")
        t_gen = NamesGenerator("?t", "?t_anon")
        return {
            'positive': self._sparql_positive(),
            'negative': self._sparql_negative(),
            's_selector': self.hypothesis.sparql(s_gen),
            't_selector': self.hypothesis.sparql(t_gen),
            'n_pos': len(self.positive),
            'n_neg': len(self.negative),
            'measure': self._sparql_measure(),
            's_root': s_gen[root],
            't_root': t_gen[root]
        }

    def p(self, root):
        query = '''
        select *
        where
        {{
            filter(?measure = max(?measure))
            {{
                select distinct ?p (count(distinct ?s) as ?tp) (count(distinct ?t) as ?fp) {measure}
                where
                {{
                    {{
                        {s_selector}
                        {s_root} ?p [] .
                        values ?s {{ {positive} }}
                    }}
                    union
                    {{
                        {t_selector}
                        {t_root} ?p [] .
                        values ?t {{ {negative} }}
                    }}
                }}
                group by ?p
                having (?measure > .5)
                order by desc(?measure)
            }}
        }}
        '''.format_map(self._args(root))
        for row in self.graph.select(query):
            s = TriplePatternSelector(root, row['p'], Variable())
            if s not in self.hypothesis:
                yield s, row['measure']

    def po(self, root):
        query = '''
        select *
        where
        {{
            filter(?measure = max(?measure))
            {{
                select distinct ?p ?o (count(distinct ?s) as ?tp) (count(distinct ?t) as ?fp) {measure}
                where
                {{
                    {{
                        {s_selector}
                        {s_root} ?p ?o .
                        values ?s {{ {positive} }}
                    }}
                    union
                    {{
                        {t_selector}
                        {t_root} ?p ?o .
                        values ?t {{ {negative} }}
                    }}
                }}
                group by ?p ?o
                having (?measure > .5)
                order by desc(?measure)
            }}
        }}
        '''.format_map(self._args(root))
        print(query)
        for row in self.graph.select(query):
            s = TriplePatternSelector(root, row['p'], row['o'])
            if s not in self.hypothesis:
                yield s, row['measure']

    def sp(self, root):
        query = '''
        select *
        where
        {{
            filter(?measure = max(?measure))
            {{
                select distinct ?p ?o (count(distinct ?s) as ?tp) (count(distinct ?t) as ?fp) {measure}
                where
                {{
                    {{
                        {s_selector}
                        ?o ?p {s_root} .
                        values ?s {{ {positive} }}
                    }}
                    union
                    {{
                        {t_selector}
                        ?o ?p {t_root} .
                        values ?t {{ {negative} }}
                    }}
                }}
                group by ?p ?o
                having (?measure > .5)
                order by desc(?measure)
            }}
        }}
        '''.format_map(self._args(root))
        for row in self.graph.select(query):
            s = TriplePatternSelector(row['o'], row['p'], root)
            if s not in self.hypothesis:
                # print(row)
                yield s, row['measure']

    def comp(self, root):
        args = self._args(root)
        for op in '<=', '>=':
            args['op'] = op
            query = '''
                select ?p ?l ?measure
                where
                {{
                    filter(?measure=max(?measure))
                    {{
                        select distinct ?p ?l (count(distinct ?s) as ?tp) (count(distinct ?t) as ?fp) {measure}
                        where
                        {{
                            {{
                                {s_selector}
                                {s_root} ?p ?xl.
                                values ?s {{ {positive} }}
                                filter(isLiteral(?xl))
                            }}
                            union
                            {{
                                {t_selector}
                                {t_root} ?p ?xl.
                                values ?t {{ {negative} }}
                                filter(isLiteral(?xl))
                            }}
                            filter(?xl {op} ?l)
                            {{
                                select distinct ?p ?l
                                where
                                {{
                                    {s_selector}
                                    {s_root} ?p ?l.
                                    values ?s {{ {positive} }}
                                    filter(isLiteral(?l))
                                }}
                            }}
                        }}
                        group by ?p ?l
                        having (?measure > .5)
                    }}
                }}
            '''.format_map(args)
            # print(query)
            for row in self.graph.select(query):
                s = FilterOpSelector(root, row['p'], op, row['l'])
                if s not in self.hypothesis:
                    # print(row)
                    yield s, row['measure']

    def _new_positive_examples(self):
        args = {
            'known': self._sparql_list(itertools.chain(self.positive, self.negative), sep=", "),
            'selector': self.hypothesis.sparql(NamesGenerator('?uri', '?anon'))
        }
        query = '''select ?uri ?comment
                where {{
                    {selector}
                    filter(?uri not in ({known}))
                    optional {{?uri rdfs:comment ?comment}}
                }}
                limit 3
        '''.format_map(args)
        return [row for row in self.graph.select(query)]

    def _new_negative_examples(self):
        selector = self.hypothesis[:-1].sparql(NamesGenerator('?uri', '?plus'))
        if len(selector.strip()) == 0:
            selector = '?uri ?p ?o.'
        args = {
            'known': self._sparql_list(itertools.chain(self.positive, self.negative), sep=", "),
            'selector': selector,
            'minus': self.hypothesis.sparql(NamesGenerator('?uri', '?minus')),
        }
        query = '''select ?uri ?comment
                where {{
                    {{
                        {{
                            {selector}
                        }}
                        minus
                        {{
                            {minus}
                        }}
                    }}
                    filter(?uri not in ({known}))
                    optional {{?uri rdfs:comment ?comment}}
                }}
                limit 3
        '''.format_map(args)
        return [row for row in self.graph.select(query)]

    def new_examples(self):
        return self._new_positive_examples(), self._new_negative_examples()

    def final_query(self):
        args = {
            'selector': self.hypothesis.sparql(NamesGenerator('?uri', '?anon'))
        }
        query = "select distinct ?uri\nwhere\n{{\n{selector}}}".format_map(args)
        return query

    def hypothesis_good_enough(self):
        query = '''
            select distinct (count(distinct ?s) as ?tp) (count(distinct ?t) as ?fp) {measure}
            where
            {{
                {{
                    {s_selector}
                    values ?s {{ {positive} }}
                }}
                union
                {{
                    {t_selector}
                    values ?t {{ {negative} }}
                }}
            }}
        '''.format_map(self._args(Selector.placeholder))
        result = [row for row in self.graph.select(query)]
        assert len(result) == 1
        if 'measure' not in result[0]:  # znaczy obliczenia sie nie powiodly
            return False
        measure = result[0]['measure'].value
        # print(query)
        print("measure={}".format(measure))
        return measure > .99

    def label_examples(self, lab_positive, lab_negative):
        self.hypothesis_cm = ContingencyMatrix()
        assert len(lab_positive) == len(self.ex_positive)
        assert len(lab_negative) == len(self.ex_negative)
        n = len(lab_positive) + len(lab_negative)
        for ex, label in zip(self.ex_positive, lab_positive):
            if label:
                self.positive.append(ex['uri'])
                self.hypothesis_cm.tp += 1.0 / n
            else:
                self.negative.append(ex['uri'])
                self.hypothesis_cm.fp += 1.0 / n
        for ex, label in zip(self.ex_negative, lab_negative):
            if label:
                self.positive.append(ex['uri'])
                self.hypothesis_cm.fn += 1.0 / n
            else:
                self.negative.append(ex['uri'])
                self.hypothesis_cm.tn += 1.0 / n
        print(self.hypothesis_cm)

    def _variables(self, source=None):
        if source is None:
            source = self.hypothesis
        result = []
        for x in source:
            result += x.variables
        if len(result) == 0:
            result.append(Selector.placeholder)
        return set(result)

    def step(self):
        if self.hypothesis_cm.fn > 0:
            if len(self.hypothesis) > 0:
                self.hypothesis = self.hypothesis[:-1]
            else:
                raise Exception("I can not make an empty hypothesis even more general!")
        restarted = False
        while True:
            print("Variables", self._variables())
            candidates = []
            for var in self._variables():
                candidates += self.po(var)
                candidates += self.sp(var)
                candidates += self.comp(var)
                candidates += self.p(var)
            candidates = sorted(candidates, key=lambda x: -x[1].value)
            pprint(candidates)
            candidates = [cand[0] for cand in candidates]
            for cand in candidates:
                self.hypothesis.append(cand)
                print("#positive = {} #negative = {}".format(len(self.positive), len(self.negative)))
                print("Refined hypothesis is:")
                for item in self.hypothesis:
                    print("\t", item)
                self.ex_positive, self.ex_negative = self.new_examples()
                if self.hypothesis_good_enough():
                    return
                if len(self.ex_positive) > 0 and len(self.ex_negative) > 0:
                    return
                while True:
                    print("Can not find new examples")
                    self.hypothesis.pop()
                    if len(self.hypothesis) > 0:
                        p, n = self.new_examples()
                        if len(p) > 0 and len(n) > 0:
                            break
                    else:
                        break
            if self.hypothesis.pop() is None:
                if restarted:
                    raise Exception("Uh-huh, and what now?")
                else:
                    restarted = True
