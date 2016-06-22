import json

def process(log):
    if 'log' not in log:
        return
    if log['log'] is None:
        return
    print(len(log['log']), log['query'])
    t = 0
    for epoch in log['log']:
        t += epoch['perf']['end'] - epoch['perf']['start']
    print(t)

def main():
    with open('log.json', 'rt') as f:
        for line in f:
            log = json.loads(line)
            process(log)

if __name__ == '__main__':
    main()
