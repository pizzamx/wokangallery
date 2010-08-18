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

from google.appengine.ext import db

from datetime import tzinfo, timedelta, datetime

import hashlib, urlparse, string, urllib2, logging, re, string

class Thumbnail(db.Model):
    name      = db.StringProperty()                   #文件名
    data      = db.BlobProperty()     

class Album(db.Model):
    name    = db.StringProperty()
    desc    = db.TextProperty()
    cover   = db.ReferenceProperty(Thumbnail)
    cr_time = db.DateTimeProperty(auto_now_add=True)

class Photo(db.Model):
    src     = db.StringProperty()                     #保留字段，来自网络的图片才赋值
    name    = db.StringProperty()                     #文件名
    desc   = db.StringProperty()                      #标题
    data    = db.BlobProperty()     
    thumb   = db.ReferenceProperty(Thumbnail)         #缩略图
    cr_time = db.DateTimeProperty(auto_now_add=True)  #创建时间
    album   = db.ReferenceProperty(Album)             #所属相册
    
    def fetch(self):
        try:
            stream = urllib2.urlopen(self.src)
            self.data = db.Blob(stream.read())
            stream.close()
            self.put()
            return True
        except:
            logging.error('Image fetch failed: ' + self.src)
            return False
    
    