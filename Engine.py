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
        self.hypothesis = []
        self.history = []
        self.hypothesis_cm = ContingencyMatrix()
        self.ex_positive = None
        self.ex_negative = None

    def _sparql_selector(self, var, what=None):
        result = ""
        if what is None:
            what = self.hypothesis
        for item in what:
            result += item.get(var)
        return result

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

    def _args(self):
        return {
            'positive': self._sparql_positive(),
            'negative': self._sparql_negative(),
            's_selector': self._sparql_selector('?s'),
            't_selector': self._sparql_selector('?t'),
            'n_pos': len(self.positive),
            'n_neg': len(self.negative),
            'measure': self._sparql_measure()
        }

    def po(self):
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
                        ?s ?p ?o .
                        values ?s {{ {positive} }}
                    }}
                    union
                    {{
                        {t_selector}
                        ?t ?p ?o .
                        values ?t {{ {negative} }}
                    }}
                }}
                group by ?p ?o
                having (?measure > .5)
                order by desc(?measure)
            }}
        }}
        '''.format_map(self._args())
        for row in self.graph.select(query):
            s = POSelector(row['p'], row['o'])
            if s not in self.hypothesis:
                yield s
        # po = []
        # for row in self.graph.select(query):
        #     print(row)
        #     po.append('({} {})'.format(row['p'].n3(), row['o'].n3()))
        # args = self._args()
        # args['po'] = " ".join(po)
        # query = '''
        # select ?p ?o (count(distinct ?s) as ?measure)
        # where
        # {{
        #     {s_selector}
        #     ?s ?p ?o .
        #     values (?p ?o) {{ {po} }}
        # }}
        # group by ?p ?o
        # having (?measure > 0)
        # order by asc(?measure)
        # '''.format_map(args)
        # print(query)
        # for row in self.graph.select(query):
        #     s = POSelector(row['p'], row['o'])
        #     if s not in self.hypothesis:
        #         # print(row)
        #         return s, None  # (row['tp'].value, row['fp'].value, row['measure'].value)
        # return None

    def sp(self):
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
                        ?o ?p ?s .
                        values ?s {{ {positive} }}
                    }}
                    union
                    {{
                        {t_selector}
                        ?o ?p ?t .
                        values ?t {{ {negative} }}
                    }}
                }}
                group by ?p ?o
                having (?measure > .5)
                order by desc(?measure)
            }}
        }}
        '''.format_map(self._args())
        for row in self.graph.select(query):
            s = SPSelector(row['o'], row['p'])
            if s not in self.hypothesis:
                # print(row)
                yield s

    def comp(self):
        args = self._args()
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
                                ?s ?p ?xl.
                                values ?s {{ {positive} }}
                                filter(isLiteral(?xl))
                            }}
                            union
                            {{
                                {t_selector}
                                ?t ?p ?xl.
                                values ?t {{ {negative} }}
                                filter(isLiteral(?xl))
                            }}
                            filter(?xl {op} ?l)
                            {{
                                select distinct ?p ?l
                                where
                                {{
                                    {s_selector}
                                    ?s ?p ?l.
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
                s = FilterOpSelector(row['p'], op, row['l'])
                if s not in self.hypothesis:
                    # print(row)
                    yield s

    def _new_examples(self, base, new_selector: Selector):
        args = {
            'known': self._sparql_list(itertools.chain(self.positive, self.negative), sep=", "),
            'selector': self._sparql_selector('?uri', base),
            'new_selector': new_selector.get('?uri')
        }
        query = '''select distinct ?uri ?comment
        where {{
            {selector}
            {new_selector}
            optional {{?uri rdfs:comment ?comment}}
            filter(?uri not in ({known}))
        }}
        limit 3
        '''.format_map(args)
        return [row for row in self.graph.select(query)]

    def new_examples(self):
        negative = FilterNotExistsSelector(self.hypothesis[-1])
        return self._new_examples(self.hypothesis[:-1], self.hypothesis[-1]), \
               self._new_examples(self.hypothesis[:-1], negative)

    def final_query(self):
        args = {
            'selector': self._sparql_selector('?uri'),
        }
        query = '''select distinct ?uri
        where {{
            {selector}
        }}
        '''.format_map(args)
        return query

    def hypothesis_good_enough(self):
        if len(self.positive) < 10 or len(self.negative) < 10:
            return False
        query = '''
            select distinct (count(distinct ?s) as ?tp) (count(distinct ?t) as ?fp) {measure}
            where
            {{
                {{
                    {s_selector}
                    ?s ?p ?o .
                    values ?s {{ {positive} }}
                }}
                union
                {{
                    {t_selector}
                    ?t ?p ?o .
                    values ?t {{ {negative} }}
                }}
            }}
        '''.format_map(self._args())
        result = [row for row in self.graph.select(query)]
        assert len(result) == 1
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

    def step(self):
        if self.hypothesis_cm.fn > 0:
            if len(self.hypothesis) > 0:
                self.hypothesis = self.hypothesis[:-1]
            else:
                raise Exception("I can not make an empty hypothesis even more general!")
        restarted = False
        while True:
            for cand in itertools.chain(self.po(), self.sp(), self.comp()):
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
                    self.hypothesis = self.hypothesis[:-1]
                    if len(self.hypothesis) > 0:
                        p, n = self.new_examples()
                        if len(p) > 0 and len(n) > 0:
                            break
                    else:
                        break
            if len(self.hypothesis) > 0:
                self.hypothesis = self.hypothesis[:-1]
            else:
                if restarted:
                    raise Exception("Uh-huh, and what now?")
                else:
                    restarted = True
        # if self.hypothesis_cm.fp > 0 or len(self.hypothesis) == 0:
        #     self._refine_hypothesis()
        # while True:
        #     if len(self.hypothesis) == 0:
        #         self._refine_hypothesis()
        #     print("#positive = {} #negative = {}".format(len(self.positive), len(self.negative)))
        #     print("Refined hypothesis is:")
        #     for item in self.hypothesis:
        #         print("\t", item)
        #     self.ex_positive, self.ex_negative = self.new_examples()
        #     if len(self.ex_positive) == 0 or len(self.ex_negative) == 0:
        #         print("Can not find new examples")
        #         if len(self.hypothesis) > 0:
        #             self.hypothesis = self.hypothesis[:-1]
        #         else:
        #             raise Exception("Can not find new examples")
        #         print("Hypothesis contains {} items".format(len(self.hypothesis)))
        #     else:
        #         break
