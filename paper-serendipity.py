from flask import Response, render_template, request, abort
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
import json
import scraper
from settings import app


sse_connections = []
count = 0
nodes = []


class Node():
    def __init__(self, doi):
        self.doi = doi


class ServerSentEvent(object):
    """Class for encapsulating server sent event data"""
    def __init__(self, data, event=None):
        self.data = data
        self.event = event
        self.id = None
        self.desc_map = {
            self.data: "data",
            self.event: "event",
            self.id: "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.iteritems() if k]
        return "%s\n\n" % "\n".join(lines)


@app.route('/api/node', methods=['POST'])
def create_node():
    if not request.json or not 'doi' in request.json:
        abort(400)
    docinfo = scraper.fetch(request.json['doi'])

    return json.dumps(docinfo, separators=(',', ':')), 201


@app.route('/debug')
def debug():
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
        q = Queue()
        sse_connections.append(q)
        try:
            while True:
                result = q.get()
                ev = ServerSentEvent(str(result))
                yield ev.encode()
                count = count + 1
        except GeneratorExit:
            sse_connections.remove(q)

    return Response(event_stream(), mimetype='text/event-stream')


if __name__ == '__main__':
    server = WSGIServer(("", 5000), app)
    server.serve_forever()
