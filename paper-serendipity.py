import json
import gevent
from flask import render_template, request
from flask.ext.socketio import SocketIO, emit
import networkx as nx
import scraper
from settings import app


socketio = SocketIO(app)
graph = nx.DiGraph()


@socketio.on('add_node', namespace='/socket')
def on_add_node(msg):
    g = gevent.spawn(scraper.fetch, msg)
    g.join()    # Wait to Greenlet finishes

    node = g.value
    graph.add_node(node['id'])
    emit('add_node', {'id': node['id'],
                      'abstract': node['abstract'],
                      'authors': node['authors'],
                      'date': node['date'],
                      'title': node['title']
                      })

    for c in node['citations']:
        gevent.sleep(0)
        graph.add_edge(node['id'], c)
        if c[:4] == 'doi:':
            cinfo = scraper.fetch(c[4:])
            emit('add_node', {'id': cinfo['id'],
                              'abstract': cinfo['abstract'],
                              'authors': cinfo['authors'],
                              'date': cinfo['date'],
                              'title': cinfo['title']})
        else:
            emit('add_node', {'id': c})
        emit('add_link',
             {'source': node['id'],
              'target': c,
              'value': 1})

    for c in node['cited by']:
        gevent.sleep(0)
        graph.add_edge(c, node['id'])
        if c[:4] == 'doi:':
            cinfo = scraper.fetch(c[4:])
            emit('add_node', {'id': cinfo['id'],
                              'abstract': cinfo['abstract'],
                              'authors': cinfo['authors'],
                              'date': cinfo['date'],
                              'title': cinfo['title']})
        else:
            emit('add_node', {'id': c})
        emit('add_link',
             {'source': c,
              'target': node['id'],
              'value': 1})


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
