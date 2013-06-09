# -*- coding: utf-8 -*-
# Copyright (c) <2010> pizzamx <pizzamx@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import webapp2, logging, re

from google.appengine.ext import webapp, db, blobstore
from google.appengine.api import users, images, memcache
from google.appengine.ext.webapp import blobstore_handlers

from mako.template import Template
from mako.lookup import TemplateLookup

from model import Photo, Album, Thumbnail
from util import adminOP

import os, logging, urllib2, math, calendar, re, string, base64, urllib

from datetime import tzinfo, timedelta, datetime, date

class UpdateBase(object):
    def getTemplate(self, name):
        #读取模板文件
        mylookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'template')], 
                                  format_exceptions=True)
        return mylookup.get_template(name)
        
class Upload(blobstore_handlers.BlobstoreUploadHandler, UpdateBase):
    @adminOP
    def get(self):
        template = self.getTemplate('upload.html')
        url = blobstore.create_upload_url('/upload')
        allAlbums = Album.all()
        self.response.write(template.render_unicode(url=url, aas=allAlbums))
        
    def post(self):
        upload_files = self.get_uploads('Filedata')
        blob_info = upload_files[0]

        name = self.request.get('Filename')
        folder = self.request.get('folder')
        width = self.request.get('width')
        height = self.request.get('height')
        folder = urllib.unquote(folder.encode('utf-8')).decode("utf-8")
        abn = folder[folder.rfind('/') + 1:]
        
        gImg = images.Image(blob_info.key())

        album = Album.get_by_key_name('_' + abn)
        if not album:
            album = Album(name=abn, cover=blob_info.key(), key_name='_' + abn)
            album.put()
        
        p = Photo(src='', name=name, blob=blob_info.key(), album=album, width=int(width), height=int(height))
        p.put()
        self.response.set_status(200)   
        self.response.write({"thumbUrl": p.genThumbURL(), "id": str(p.key().id())})
        #self.redirect('/_dummy/xxx' % blob_info.key())

class APIUpload(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('Filedata')
        blob_info = upload_files[0]

        name = self.request.get('Filename')
        abn = self.request.get('album')
        abn = unicode(base64.b64decode(abn), 'utf-8')
        desc = self.request.get('desc')
        width = self.request.get('width')
        height = self.request.get('height')
        
        dtstr = self.request.get('datetime')
        if dtstr.find('+') != -1:
            dtstr = dtstr[:dtstr.find('+')]
        try:
            dt = datetime.strptime(dtstr, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            dt = datetime.strptime(dtstr, '%Y-%m-%dT%H:%M:%S')
        captureDatetime = dt
        
        #logging.info(self.request)
        
        """
        好像是 Lightroom 的问题。如果 LrHttp.postMultipart 里面 content 的某个字段超过
        255 字节，他就会把它 multipart，比如：（为了方便阅读换行了，实际上是一行）
        
        5qiq5ruo77yM5qiq5ruo5piv5Liq5aSn5riv5Y+j77yM5omA5Lul5a+55aSW6LS45piT5b6I5aS
        a77yM5pyJ5b6I5aSa6KW/5rSL5bu6562R44CC5Zu95YaF6L+Z56eN5pmv54K55Lmf5aSa77yM5L
        iN6L+H6Lef5pel5pys5q+U6LW35p2l5pW05L2T5bCx5beu5aSa5LqG77yM5Lq65a625pW055qE5
        aSq5bmy5YeA5LqG44CC5Zyw5LiK5piv5qix6Iqx77yMM+aciDMw5Y+355qE5pe25YCZ5YWz5Lic
        55qE5qix6Iqx5bey57uP5byA5aeL6JC95LqG77yM5b6I576O        
        
        变成了：
        
        5qiq5ruo77yM5qiq5ruo5piv5Liq5aSn5riv5Y+j77yM5omA5Lul5a+55aSW6LS45piT5b6I5aS=
        a77yM5pyJ5b6I5aSa6KW/5rSL5bu6562R44CC5Zu95YaF6L+Z56eN5pmv54K55Lmf5aSa77yM5L=
        iN6L+H6Lef5pel5pys5q+U6LW35p2l5pW05L2T5bCx5beu5aSa5LqG77yM5Lq65a625pW055qE5=
        aSq5bmy5YeA5LqG44CC5Zyw5LiK5piv5qix6Iqx77yMM+aciDMw5Y+355qE5pe25YCZ5YWz5Lic=
        55qE5qix6Iqx5bey57uP5byA5aeL6JC95LqG77yM5b6I576O
        
        所以把 =\r 全部去掉（换行是试出来的）
        """
        desc = re.sub(r'(=\r)', '', desc)
        desc = unicode(base64.b64decode(desc), 'utf-8')
        
        gImg = images.Image(blob_info.key())

        album = Album.get_by_key_name('_' + abn)
        if not album:
            album = Album(name=abn, cover=blob_info.key(), key_name='_' + abn)
            album.put()
        else:
            memcache.delete(str(album.key()))
        
        p = Photo(src='', name=name, blob=blob_info.key(), desc=desc, album=album, width=int(width), height=int(height), captureDatetime=captureDatetime)
        p.put()
        
        self.response.set_status(200)   
        self.response.write({"thumbUrl": p.genThumbURL(), "id": str(p.key().id())})

class EditDesc(webapp2.RequestHandler):
    @adminOP
    def post(self):
        keys = self.request.arguments()
        result = []
        for k in keys:
            v = self.request.get(k)
            p = Photo.get_by_id(int(k))
            if p:
                p.desc = v
                p.put()
                result.append(k)
        self.response.write(string.join(result) if len(result) else '')
