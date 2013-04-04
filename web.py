#!/usr/bin/python
import sys, os, os.path, json, time, threading, random
import bottle
from bottle import route, view, static_file, request, response, hook, HTTPResponse, HTTPError, redirect
from PIL import Image
import StringIO

import songlist

LANGUAGES = ("en-gb", "es-es", "ja-jp", "de-de", "es-eu")

nonce = random.randint(0, 2**32)

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
	return ""

@route("/cfg/lang/<val>")
def cfg_set_lang(val):
	response.set_cookie("lang", val, path="/")
	return ""

@route("/cfg.js")
def index():
	response.content_type = 'text/javascript'
	cfg = json.dumps({
		"lang": request.lang,
		"lc": request.lc,
		"latin": request.latin,
		"nonce": nonce,
	})
	with open("static/i18n/%s.json" % request.lang) as fd:
		i18n = fd.read()
	return "g_cfg = %s;\ng_i18n = %s;" % (cfg, i18n)

@route("/s/<filename:path>")
def send_static(filename):
	return static_file(filename, root="static")

@route("/")
def index():
	return static_file("index.html", root="static", mimetype="text/html; charset=UTF-8")

@route("/xs")
def index():
	with open("static/index.html") as fd:
		# horrible hack!
		data = fd.read().replace("user-scalable=0","user-scalable=1")
	response.content_type = "text/html; charset=UTF-8"
	return data

def get_song_meta(song):
	d = {}
	for k, v in song.meta.items():
		if request.latin:
			d[k] = v[(request.lc, "l")]
		else:
			d[k] = v[request.lc]
	return d

def get_song_variants(song):
	return [{"id": i, "name": v.name,
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
		"channels": int(song.song.get("channels", 1))
	}

@route("/song/<id:int>/cover/<size:int>")
def get_songcover(id, size):
	song = database.songs[id]
	if song.coverfile is None:
		return None
	else:
		stats = os.stat(song.coverfile)
		lm = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stats.st_mtime))
		response.headers['Last-Modified'] = lm
		response.content_type = "image/png"
		if request.method != 'HEAD':
			im = Image.open(song.coverfile).resize((size, size), Image.ANTIALIAS)
			fd = StringIO.StringIO()
			im.save(fd, "PNG")
			fd.seek(0)
			return fd
		else:
			fd = StringIO.StringIO("TEST")
			return fd  # FIXME: this sets content-length: 0 and I don't know how to avoid that

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
		"channels": int(qe.song.song.get("channels", 1)),
		"config": get_qe_config(qe)
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
	return ""

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

@route("/settings")
def settings_get():
	return {
		"volume": audio_config.volume,
		"headstart": audio_config.headstart,
		"mic_volume": audio_config.mic_volume,
		"mic_feedback": audio_config.mic_feedback,
		"mic_delay": audio_config.mic_delay,
	}

@route("/settings/change", method="POST")
def settings_change():
	for attr in ("volume", "headstart", "mic_volume", "mic_feedback", "mic_delay"):
		if attr in request.json:
			setattr(audio_config, attr, request.json[attr])

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
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs
		threading.Thread.__init__(self)

	def run(self):
		bottle.run(*self.args, **self.kwargs)

if __name__ == "__main__":
	database = songlist.SongDatabase(sys.argv[1])
	bottle.run(reloader=True, host="0.0.0.0", port=10111, server="paste")
