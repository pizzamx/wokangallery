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

from google.appengine.ext import webapp, db, blobstore
from google.appengine.api import users, images
from google.appengine.ext.webapp import blobstore_handlers

from mako.template import Template
from mako.lookup import TemplateLookup

from model import Photo, Album, Thumbnail
from util import adminOP

import os, logging, urllib2, math, calendar, re, string, base64

from datetime import tzinfo, timedelta, datetime, date

class UpdateBase(object):
    def getTemplate(self, name):
        #读取模板文件
        mylookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'template')], 
                                  format_exceptions=True)
        return mylookup.get_template(name)
        
class Upload(blobstore_handlers.BlobstoreUploadHandler, UpdateBase):
    def get(self):
        template = self.getTemplate('upload.html')
        url = blobstore.create_upload_url('/upload')
        self.response.out.write(template.render_unicode(url=url))
        
    def post(self):
        upload_files = self.get_uploads('Filedata')
        blob_info = upload_files[0]

        name = self.request.get('Filename')
        folder = self.request.get('folder')
        abn = folder[folder.rfind('/') + 1:]
        
        gImg = images.Image(blob_info.key())

        album = Album.get_by_key_name('_' + abn)
        if not album:
            album = Album(name=abn, cover=blob_info.key(), key_name='_' + abn)
            album.put()
        
        p = Photo(src='', name=name, blob=blob_info.key(), album=album)
        p.put()
        self.redirect('/_dummy/%s' % blob_info.key())

class APIUpload(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('Filedata')
        blob_info = upload_files[0]

        name = self.request.get('Filename')
        abn = self.request.get('album')
        albm = unicode(base64.b64decode(abn), 'utf-8')
        desc = self.request.get('desc')
        desc = unicode(base64.b64decode(desc), 'utf-8')
        
        gImg = images.Image(blob_info.key())

        album = Album.get_by_key_name('_' + abn)
        if not album:
            album = Album(name=albm, cover=blob_info.key(), key_name='_' + abn)
            album.put()
        
        p = Photo(src='', name=name, blob=blob_info.key(), desc=desc, album=album)
        p.put()
        
        self.redirect('/_dummy/%s' % blob_info.key())

class EditDesc(webapp.RequestHandler):
    @adminOP
    def post(self):
        keys = self.request.arguments()
        result = []
        for k in keys:
            v = self.request.get(k)
            logging.info((k, v))
            p = Photo.get_by_id(long(k))
            if p:
                p.desc = v
                p.put()
                result.append(k)
        self.response.out.write(string.join(result) if len(result) else '')
