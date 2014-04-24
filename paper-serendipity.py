import json
from flask import render_template, request
from flask.ext.socketio import SocketIO, emit
import networkx as nx
import scraper
from settings import app


socketio = SocketIO(app)
graph = nx.DiGraph()


@socketio.on('add_node', namespace='/socket')
def on_add_node(doi):
    emit('status', 'Fetching node data...')
    node = scraper.fetch(doi)
    if not graph.has_node(node['id']):
        graph.add_node(node['id'])
        emit('add_node', {'id': node['id'],
                          'abstract': node['abstract'],
                          'authors': node['authors'],
                          'date': node['date'],
                          'title': node['title'],
                          'cluster': 0
                          })
    get_refs(node)


@socketio.on('add_links', namespace='/socket')
def on_add_links(id):
    if id[:4] == 'doi:':
        emit('status', 'Fetching node data...')
        node = scraper.fetch(id[4:])
        emit('status', 'Fetching node data...Done!')
        get_refs(node)


@socketio.on('cluster', namespace='/socket')
def on_cluster(msg):
    emit('status', 'Clustering nodes...')
    toggle_status = True
    # Betweenness-centrality score
    graph2 = graph.to_undirected()
    bc_score = nx.edge_betweenness_centrality(graph2)
    while bc_score[max(bc_score)] > 0.005:
        if toggle_status:
            emit('status', 'Clustering nodes......')
        else:
            emit('status', 'Clustering nodes...')
        toggle_status = False if toggle_status else True
        graph2.remove_edges_from([max(bc_score)])
        bc_score = nx.edge_betweenness_centrality(graph2)

    subgraphs = nx.connected_component_subgraphs(graph2)
    for i, sg in enumerate(subgraphs):
        emit('cluster', {'nodes': sg.nodes(),
                         'cluster': i})


def get_refs(node):
    total = len(node['citations'])
    for i, c in enumerate(node['citations']):
        if graph.has_edge(node['id'], c):
            continue

        emit('status', 'Getting citation (%d/%d)' % (i+1, total))
        if not (graph.has_node(c)):
            if c[:4] == 'doi:':
                cinfo = scraper.fetch(c[4:])
                emit('add_node', {'id': cinfo['id'],
                                  'abstract': cinfo['abstract'],
                                  'authors': cinfo['authors'],
                                  'date': cinfo['date'],
                                  'title': cinfo['title'],
                                  'cluster': 0})
            else:
                emit('add_node', {'id': c,
                                  'cluster': 0})
        graph.add_edge(node['id'], c)
        emit('add_link',
             {'source': node['id'],
              'target': c,
              'value': 1})
    emit('status', 'Getting citations...Done!')

    total = len(node['cited by'])
    for i, c in enumerate(node['cited by']):
        if graph.has_edge(c, node['id']):
            continue
        emit('status', 'Getting cited by (%d/%d)' % (i+1, total))
        if not (graph.has_node(c)):
            if c[:4] == 'doi:':
                cinfo = scraper.fetch(c[4:])
                emit('add_node', {'id': cinfo['id'],
                                  'abstract': cinfo['abstract'],
                                  'authors': cinfo['authors'],
                                  'date': cinfo['date'],
                                  'title': cinfo['title'],
                                  'cluster': 0})
            else:
                emit('add_node', {'id': c,
                                  'cluster': 0})
        graph.add_edge(c, node['id'])
        emit('add_link',
             {'source': c,
              'target': node['id'],
              'value': 1})
    emit('status', 'Getting cited by...Done!')


@app.route('/search')
def search():
    r = scraper.search(request.args.get('qs', None, type=str))
    j = json.dumps(r, separators=(',', ':'))
    return j


@app.route('/')
def start_app():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app)
