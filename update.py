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

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images

from mako.template import Template
from mako.lookup import TemplateLookup

from model import Photo, Album, Thumbnail
from util import adminOP

import os, logging, urllib2, math, calendar, re, string

from datetime import tzinfo, timedelta, datetime, date

class UpdateBase(webapp.RequestHandler):
    def getTemplate(self, name):
        #读取模板文件
        mylookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'template')], 
                                  format_exceptions=True)
        return mylookup.get_template(name)
        
    def makeSquareThumbnail(self, stream, length):
        #返回一个边长为length的正方形缩略图
        #传入对象stream不会被修改
        gImg = images.Image(stream)
        if gImg.width <= length and gImg.height <= length:
            return stream
            
        if gImg.width > gImg.height:    #横版
            w = gImg.width * length / gImg.height   #先缩放到竖边长length，横边长一些
            tnstream = images.resize(stream, w, length)
            cut = float((w - length) / 2) / w
            tnstream = images.crop(tnstream, cut, 0.0, 1 - cut, 1.0)    #再裁掉横边超长的部分
        else:   #竖版
            h = gImg.height * length / gImg.width
            tnstream = images.resize(stream, length, h)
            cut = float((h - length) / 2) / h
            tnstream = images.crop(tnstream, 0.0, cut, 1.0, 1 - cut)
            
        return tnstream
        
    def makeThumbnail(self, stream, limit):
        #返回一个长边为limit的矩形缩略图（按比例缩小）
        #传入对象stream不会被修改
        gImg = images.Image(stream)
        if gImg.width > gImg.height:
            if gImg.width <= limit:
                return stream
            h = gImg.height * limit / gImg.width
            tnstream = images.resize(stream, limit, h)
        else:
            if gImg.height <= limit:
                return stream
            w = gImg.width * limit / gImg.height
            tnstream = images.resize(stream, w, limit)
        
        return tnstream

class Upload(UpdateBase):
    def get(self):
        template = self.getTemplate('upload.html')
        self.response.out.write(template.render_unicode())
        
    def post(self):
        stream = self.request.get('Filedata')
        name = self.request.get('Filename')
        abn = self.request.get('folder')[1:]
        
        gImg = images.Image(stream)

        album = Album.get_by_key_name('_' + abn)
        if not album:
            cover = Thumbnail(name='cover_' + name, data=db.Blob(self.makeSquareThumbnail(stream, 144)))
            cover.put()
            album = Album(name=abn, cover=cover, key_name='_' + abn)
            album.put()
        
        #d= date.today()
        #name= '%d_%d_%d_%s' % (d.year, d.month, d.day, name)
        p = Photo(src='', name=name, data=db.Blob(stream), album=album)
        p.put()
        
        #dotPos = name.rfind('.')
        #ext = name[dotPos:]
        #name = name[:dotPos] + '_resized' + ext
        thumb = Thumbnail(name=name, data=db.Blob(self.makeSquareThumbnail(stream, 128)))
        thumb.put()
        p.thumb = thumb
        p.put()

        self.response.out.write(p.key().id())
        
class APIUpload(UpdateBase):
    def post(self):
        stream = self.request.get('Filedata')
        name = self.request.get('Filename')
        abn = self.request.get('album')
        desc = self.request.get('desc')
        
        gImg = images.Image(stream)

        album = Album.get_by_key_name('_' + abn)
        if not album:
            cover = Thumbnail(name='cover_' + name, data=db.Blob(self.makeSquareThumbnail(stream, 144)))
            cover.put()
            album = Album(name=abn, cover=cover, key_name='_' + abn)
            album.put()
        
        #d= date.today()
        #name= '%d_%d_%d_%s' % (d.year, d.month, d.day, name)
        p = Photo(src='', name=name, data=db.Blob(stream), album=album, desc=desc)
        p.put()
        
        #dotPos = name.rfind('.')
        #ext = name[dotPos:]
        #name = name[:dotPos] + '_resized' + ext
        thumb = Thumbnail(name=name, data=db.Blob(self.makeSquareThumbnail(stream, 128)))
        thumb.put()
        p.thumb = thumb
        p.put()

        self.response.out.write(p.key().id())

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
