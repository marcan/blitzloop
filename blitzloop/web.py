#!/usr/bin/python

from PIL import Image
from bottle import route, static_file, request, response, hook, HTTPError, HTTPResponse, Bottle, ServerAdapter
from urllib.parse import urljoin
from urllib.request import urlopen
from paste import httpserver
import bottle
import io
import json
import os
import random
import sys
import threading
import time
import jaconv
import unicodedata

from blitzloop import songlist, util

LANGUAGES = ("en-gb", "es-es", "ja-jp", "de-de", "es-eu", "fr-fr", "sk-sk")

nonce = random.randint(0, 2**32)

DEFAULT_WIDTH = 1024

# Will be set by script/main.py
database = None
queue = None
audio_config = None

normalize_tbl = dict.fromkeys(i for i in range(sys.maxunicode)
                              if unicodedata.category(chr(i))[0] in "PMSZ")

# Fixed version of Bottle redirect
def redirect(url):
    res = response.copy(cls=HTTPResponse)
    res.status = 302
    res.body = b"Redirect"
    res.set_header('Location', urljoin(request.url, url))
    raise res

@hook("before_request")
def pre_req():
    request.lang = request.get_cookie('lang')
    if not request.lang or request.lang not in LANGUAGES:
        request.lang = 'en-gb'
        response.set_cookie("lang", "en-gb", path="/")
    if "-" in request.lang:
        request.lc = request.lang.split("-")[0]
    else:
        request.lc = request.lang
    request.latin = request.get_cookie('latin') == "1"

@route("/cfg/latin/<val:int>")
def cfg_set_latin(val):
    response.set_cookie("latin", str(val), path="/")
    return "OK"

@route("/cfg/lang/<val>")
def cfg_set_lang(val):
    response.set_cookie("lang", val, path="/")
    return "OK"

@route("/cfg.js")
def index():
    response.content_type = 'text/javascript; charset=UTF-8'
    cfg = json.dumps({
        "lang": request.lang,
        "lc": request.lc,
        "latin": request.latin,
        "nonce": nonce,
        "normalize_tbl": normalize_tbl,
    })
    fp = util.get_webres_path('i18n/%s.json') % request.lang
    with open(fp, encoding='utf-8') as fd:
        i18n = fd.read()
    return "g_cfg = %s;\ng_i18n = %s;" % (cfg, i18n)

def get_cover(filename, size):
    stats = os.stat(filename)
    lm = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stats.st_mtime))
    response.headers['Last-Modified'] = lm
    response.content_type = "image/png"
    if request.method != 'HEAD':
        im = Image.open(filename).resize((size, size), Image.ANTIALIAS)
        fd = io.BytesIO()
        im.save(fd, "PNG")
        fd.seek(0)
        return fd
    else:
        fd = io.BytesIO("TEST")
        return fd  # FIXME: this sets content-length: 0 and I don't know how to avoid that

@route("/s/no_cover/<size:int>")
def get_nocover(size):
    return get_cover(util.get_webres_path('img/no_cover.png'), size)

@route("/s/<filename:path>")
def send_static(filename):
    return static_file(filename, root=util.get_webres_path(''))

@route("/")
def index():
    return index_xw(DEFAULT_WIDTH)

@route("/xs")
def index_xs():
    return index_xw(DEFAULT_WIDTH, True)

@route("/xw=<width:int>")
def index_xw(width, user_scalable=False):
    fp = util.get_webres_path('index.html')
    with open(fp, encoding='utf-8') as fd:
        data = fd.read()
    data = data.replace("%SCALABLE%", "1" if user_scalable else "0")
    data = data.replace("%WIDTH%", str(width))
    response.content_type = "text/html; charset=UTF-8"
    return data

def normalize(s):
    val = jaconv.h2z(s)
    val = jaconv.hira2kata(val)
    val = val.translate(normalize_tbl)
    return val

def get_song_meta(song):
    d = {}
    search = set()
    for k, v in song.meta.items():
        if request.latin:
            d[k] = v[(request.lc, "l")]
        else:
            d[k] = v[request.lc]
    for k in ("title", "artist", "seenon", "album"):
        if k in song.meta:
            v = song.meta[k]
            search.add(normalize(v[request.lc]))
            search.add(normalize(v["k"]))
            search.add(normalize(v["l"]))
            search.add(normalize(jaconv.kana2alphabet(jaconv.kata2hira(v["k"]))).replace("ー",""))
    for k in ("genre",):
        if k in song.meta:
            v = song.meta[k]
            search.add(normalize(v[request.lc]))
    d["search"] = list(search)
    if request.latin:
        d["sort"] = song.meta["title"][(request.lc, "l")]
        if ord(d["sort"][0:1]) > 0x100:
            # Try again with kana-to-romaji, might help manufacture some sensible sort order
            d["sort"] = jaconv.kana2alphabet(jaconv.kata2hira(song.meta["title"][(request.lc, "l", "k")]))
    else:
        d["sort"] = song.meta["title"][(request.lc, "k")]
    return d

def get_song_variants(song):
    return [{"id": i, "name": v.name, "default": v.default,
             "snippet": song.get_lyric_snippet(k)}
            for i, (k, v) in enumerate(song.variants.items())]

def get_qe_config(qe):
    return {
        "variant": qe.variant,
        "channels": qe.channels,
        "speed": qe.speed,
        "pitch": qe.pitch,
        "pause": qe.pause,
    }

@route("/songlist")
def get_songlist():
    songs = []
    for i, song in enumerate(database.songs):
        songs.append({"id": i, "meta": get_song_meta(song)})
    return {"songs": songs}

@route("/song/<id:int>")
def get_song(id):
    song = database.songs[id]
    variants = ((k, v.name) for k, v in song.variants.items())
    return {
        "id": id,
        "meta": get_song_meta(song),
        "variants": get_song_variants(song),
        "channels": song.channel_defaults,
        "channel_names": song.channel_names,
    }

@route("/song/<id:int>/cover/<size:int>")
def get_songcover(id, size):
    song = database.songs[id]
    coverfile = song.coverfile
    if coverfile is None:
        return redirect("/s/no_cover/%d" % size)
    else:
        return get_cover(coverfile, size)

@route("/queue")
def get_queuelist():
    q = []
    for i, qe in enumerate(queue):
        q.append({"idx": i, "id": qe.song.id, "qid": qe.qid, "meta": get_song_meta(qe.song)})
    return {"queue": q}

@route("/queue/now")
def queue_get_now():
    try:
        return queue_get(queue[0].qid)
    except IndexError:
        return HTTPError(404)

@route("/queue/<qid:int>")
def queue_get(qid):
    try:
        qe = queue.get(qid)
        index = queue.index(qid)
    except KeyError:
        return HTTPError(404)
    variants = ((k, v.name) for k, v in qe.song.variants.items())
    return {
        "idx": index,
        "id": qe.song.id,
        "qid": qid,
        "meta": get_song_meta(qe.song),
        "variants": get_song_variants(qe.song),
        "channels": qe.song.channel_defaults,
        "channel_names": qe.song.channel_names,
        "config": get_qe_config(qe),
    }

def apply_qe(qe, json):
    for attr in ("variant", "channels", "speed", "pitch", "pause"):
        if attr in json:
            setattr(qe, attr, json[attr])

@route("/queue/add/<id:int>", method="POST")
def queue_add(id):
    song = database.songs[id]
    qe = songlist.SongQueueEntry(song)
    apply_qe(qe, request.json)
    queue.add(qe)
    return {"qid": qe.qid}

@route("/queue/remove/<qid:int>", method="POST")
def queue_remove(qid):
    try:
        queue.remove(qid)
    except KeyError:
        return HTTPError(404)
    except ValueError:
        return HTTPError(500)
    return "OK"

@route("/queue/change/<qid:int>", method="POST")
def queue_change(qid):
    try:
        qe = queue.get(qid)
    except KeyError:
        return HTTPError(404)
    except ValueError:
        return HTTPError(500)

    apply_qe(qe, request.json)
    return {"qid": qe.qid}

@route("/queue/now/seek", method="POST")
def now_seek():
    try:
        qe = queue[0]
    except KeyError:
        return HTTPError(404)

    if "offset" in request.json:
        qe.commands.append(("seek", float(request.json["offset"])))
    if "position" in request.json:
        qe.commands.append(("seekto", float(request.json["position"])))
    return "OK" # bug in paste for python3 with empty replies, give it something

@route("/settings")
def settings_get():
    return {
        "volume": audio_config.volume,
        "headstart": audio_config.headstart,
        "mic_channels": audio_config.mic_channels,
        "mic_feedback": audio_config.mic_feedback,
        "mic_delay": audio_config.mic_delay,
    }

@route("/settings/change", method="POST")
def settings_change():
    for attr in ("volume", "headstart", "mic_channels", "mic_feedback", "mic_delay"):
        if attr in request.json:
            setattr(audio_config, attr, request.json[attr])
    return "OK"

def queue_change(qid):
    try:
        qe = queue.get(qid)
    except KeyError:
        return HTTPError(404)
    except ValueError:
        return HTTPError(500)

    apply_qe(qe, request.json)
    return {"qid": qe.qid}

class ServerThread(threading.Thread):
    def __init__(self, host, port, **kwargs):
        self.running = False
        self.kwargs = kwargs
        self.host = host
        self.dhost = self.host
        if self.dhost == "::":
            self.dhost = "::1"
        elif self.dhost == "0.0.0.0":
            self.dhost = "127.0.0.1"
        self.port = port
        threading.Thread.__init__(self)

    def run(self):
        handler = bottle.default_app()
        self.server = httpserver.serve(handler, host=self.host, port=self.port, start_loop=False, use_threadpool=False, **self.kwargs)
        print("web: serving on %s:%d at http://%s:%d" % (self.host, self.port, self.dhost, self.port))
        #print(self.server.thread_pool)
        self.running = True
        try:
            self.server.serve_forever(poll_interval = 0.5)
        finally:
            self.running = False
        print("web: Server thread exited")

    def stop(self):
        if self.running:
            self.server.shutdown()

if __name__ == "__main__":
    opts = util.get_opts()
    database = songlist.SongDatabase(sys.argv[1])
    bottle.run(reloader=True, host="0.0.0.0", port=opts.port, server="paste")
