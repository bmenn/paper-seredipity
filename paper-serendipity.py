import time
import json
from flask import Response, render_template, request, abort
import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
import networkx as nx
import scraper
from settings import app


sse_connections = []
count = 0
graph = nx.DiGraph()
nodes = []
links = []


def add_node(node):
    global nodes
    print "Node added!"
    graph.add_node(node['id'],
                   abstract=node['abstract'],
                   authors=node['authors'],
                   date=node['date'],
                   title=node['title']
                   )

    for c in node['citations']:
        graph.add_edge(node['id'], c, weight=1)
    for c in node['cited by']:
        graph.add_edge(c, node['id'], weight=1)

    nodes.append({'id': node['id'],
                  'abstract': node['abstract'],
                  'authors': node['authors'],
                  'date': node['date'],
                  'title': node['title']
                  })


@app.route('/api/node', methods=['POST'])
def create_node():
    if not request.json or not 'doi' in request.json:
        abort(400)

    node = scraper.fetch(request.json['doi'])
    add_node(node)

    return json.dumps(node, separators=(',', ':')), 201


@app.route('/debug')
def debug():
    global count
    return "Pushed %d SSEs" % count


@app.route('/search')
def search():
    r = scraper.search(request.args.get('qs', None, type=str))
    j = json.dumps(r, separators=(',', ':'))
    return j


@app.route('/')
def start_app():
    return render_template('index.html')


@app.route('/sse')
def sse_request():
    def event_stream():
        global count
        global nodes
        global links
        while True:
            gevent.sleep(0)
            try:
                n = nodes.pop(0)
                yield "data: %s\n\n" % json.dumps(n, separators=(',', ':'))
            except (IndexError, GeneratorExit):
                pass
            else:
                print "Created SSE"
                count = count + 1

    return Response(event_stream(), mimetype='text/event-stream')


if __name__ == '__main__':
    server = WSGIServer(("", 5000), app)
    server.serve_forever()
