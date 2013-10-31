#!/usr/bin/env python
"""This file is part of VideoBrowser.

Copyright (C) 2013   Sven Ludwig aka muhgatus

VideoBrowser is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

VideoBrowser is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with VideoBrowser.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, base64, hashlib, json, datetime

PATH='/recordings/hts'
KEY='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

HTML="""<html>
 <head>
  <title>Videobrowser</title>
  <link rel="stylesheet" type="text/css" href="/VideoBrowser.css">
  <script src="/jquery-2.0.3.min.js"></script>
  <script src="/jquery.base64.min.js"></script>
  <script src="/VideoBrowser.js"></script>
 </head>
 <body>
{0}
 </body>
</html>
"""

def walk(p, d, f):
    try:
        filelist=os.listdir(p)
    except:
        return
    for fn in filelist:
        if fn.startswith('.'): continue
        fqfn=os.path.join(p, fn)
        if os.path.isdir(fqfn):
            walk(fqfn, d, f)
        if f is not None and f not in fn.decode('utf8'): continue
        elif fn.rsplit('.',1)[-1] in ('bin','ts','mkv'):
            d.append((fn,os.path.getmtime(fqfn),os.path.getsize(fqfn),'/'.join(fqfn.split('/')[-2:])))


from flask import Flask, request, abort, redirect, url_for, Response
from werkzeug.contrib.fixers import ProxyFix
import urllib

app = Flask(__name__)
app.debug=True

def findVideos(startpath, filter_fn):
    l=[]
    walk(startpath, l, filter_fn)
    l.sort()
    return l

@app.route("/time")
@app.route("/size")
@app.route("/name")
@app.route("/reverse_time")
@app.route("/reverse_size")
@app.route("/reverse_name")
@app.route("/filter/<string:filter_fn>")
@app.route("/")
def index(filter_fn=None):
    sortorder = request.path[1:]
    files=[]
    for fn, mtime, size, fqfn in findVideos(PATH, filter_fn):
        if sortorder == 'time' or sortorder == 'reverse_time':
            sortkey=mtime
        elif sortorder == 'size' or sortorder == 'reverse_size':
            sortkey=size
        elif sortorder == 'name' or sortorder == 'reverse_name':
            sortkey=fn
        else:
            sortkey=fn
        delete_key=base64.b64encode(fqfn)
        files.append((
            sortkey,
            '''<div class="videofile">
<div class="link"><a href="/video/hts/{0}">{1}</a></div>
<div class="delete"><a href="/video/delete/{2}/{3}">[X]</a></div></div>'''.format(
                fqfn,
                '<br>\n'.join(fn.rsplit('.',3)[:-1]),
                hashlib.sha512('{0}/{1}'.format(KEY,delete_key)).hexdigest(),
                delete_key
            )
        ))
    files.sort()
    if 'reverse' in sortorder:
        files.reverse()
    return HTML.format("""  <div id="toolbar">Sort: [<a href="/video/time">by time</a> <a href="/video/reverse_time">(reverse)</a>] [<a href="/video/size">by size</a> <a href="/video/reverse_size">(reverse)</a>] [<a href="/video/name">by name</a> <a href="/video/reverse_name">(reverse)</a>]</div>
  <div id="toolbar_spacer">&nbsp;</div>
  <div class="videocontainer">
{0}
  </div>
""".format(
        '\n'.join([html for sortkey, html in files]),
    )
)

def unpack(packed):
    try:
        data=base64.b64decode(packed)
    except:
        abort(500)

    for encoding in ('utf8','iso8859-15', 'iso8859-1',):
        try:
            data=data.decode(encoding)
            break
        except:
            pass

    try:
        data=json.loads(data)
    except:
        if data.startswith('["'):
            abort(500)
        data=[data]
    return data

@app.route("/playlist")
@app.route("/hts/<path:fn>")
def hts(fn=None):
    mode=request.args.get('mode')
    if mode == 'file':
        return redirect('/hts/{0}'.format(fn))

    if fn is None:
        if 'files' in request.args:
            files=request.args.get('files')
        else:
            abort(500)
        files=unpack(files)
        orig_fn='{0}_{1}.pls'.format(request.environ['SERVER_NAME'], datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    else:
        orig_fn=fn
        files=[fn]

    l=[]
    for fn in files:
        try:
            fqfn=os.path.abspath(os.path.join(PATH,fn))
        except:
            continue

        if not fqfn.startswith(PATH) or fqfn.rsplit('.',1)[-1] not in ('bin','ts','mkv'):
            continue

        l.append(fn)

    if len(l) == 0: abort(404)

    playlist=[
        '[playlist]',
        'NumberOfEntries={0}'.format(len(l)),
        '',
    ]

    pos=1
    for fn in l:
        base='{0}{1}'.format(
            request.url_root.replace(request.script_root, ''),
            'hts',
        )
        fn=urllib.quote(fn.startswith('/') and fn[1:] or fn)

        playlist.append('File{0}={1}/{2}'.format(pos, base, fn))
        playlist.append('Title{0}={1}/{2}'.format(pos, base, fn))
        playlist.append('Length{0}=-1'.format(pos))
        playlist.append('')
        pos+=1

    playlist.append('Version=2')

    return Response(
    '\n'.join(playlist),
    headers={
        'Content-Disposition':'attachment; filename="{0}.pls"'.format(os.path.basename(orig_fn).rsplit('.',1)[0])
    },
    mimetype='audio/x-scpls'
) 

@app.route("/delete")
@app.route("/delete/<string:signature>")
@app.route("/delete/<string:signature>/<string:delete_key>")
def delete(signature=None,delete_key=None):
    if signature is None:
        if 'signature' in request.form:
            signature=request.form['signature']
        elif 'signature' in request.args:
            signature=request.args.get('signature')

    if delete_key is None:
        if 'delete_key' in request.form:
            delete_key=request.form['delete_key']
        elif 'delete_key' in request.args:
            delete_key=request.args.get('delete_key')
        else:
            abort(500)

    data=unpack(delete_key)

    if not request.args.get('sure'):
        if signature is None:
            signature=hashlib.sha512('{0}/{1}'.format(KEY,delete_key)).hexdigest()
        return HTML.format("""  <h1>Are you sure?</h1>
 <h2>{2}</h2>
 <h3><a href="{0}">Yes</a> <a href="{1}">No</a></h3>
""".format(
        '{0}?{1}'.format(
            url_for('delete'),
            urllib.urlencode({
                'delete_key':   delete_key,
                'signature':    signature,
                'sure':         'yes',
                'next':         request.referrer,
            }),
        ),
        request.referrer,
        u'<br>'.join(data).encode('utf8')
    )
)
    if signature != hashlib.sha512('{0}/{1}'.format(KEY,delete_key)).hexdigest():
        abort(401)

    for fqfn in data:
        try:
            fqfn=os.path.abspath(os.path.join(PATH,fqfn))
        except:
            continue
        if not fqfn.startswith(PATH) or fqfn.rsplit('.',1)[-1] not in ('bin','ts','mkv'):
            continue
        if os.path.exists(fqfn):
            os.unlink(fqfn)
    if request.args.get('next'):
        return redirect(request.args.get('next'))
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('index'))

app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == "__main__":
    app.run()
