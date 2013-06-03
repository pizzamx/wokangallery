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

from google.appengine.ext import db, blobstore
from google.appengine.api import images

from datetime import tzinfo, timedelta, datetime

import hashlib, urlparse, string, urllib2, logging, re, string

class Thumbnail(db.Model):
    name      = db.StringProperty()                   #文件名
    data      = db.BlobProperty()     

class Album(db.Model):
    name     = db.StringProperty()
    desc     = db.TextProperty()
    cover    = blobstore.BlobReferenceProperty()
    cr_time  = db.DateTimeProperty(auto_now_add=True)
    
    def genURL(self):
        return images.get_serving_url(str(self.cover.key()), size=196, crop=True)

class Photo(db.Model):
    src     = db.StringProperty()                     #保留字段，来自网络的图片才赋值
    name    = db.StringProperty()                     #文件名
    desc    = db.StringProperty(multiline=True)       #标题
    blob    = blobstore.BlobReferenceProperty()     
    width   = db.IntegerProperty()
    height  = db.IntegerProperty()
    #thumb   = db.ReferenceProperty(Thumbnail)         #缩略图
    cr_time = db.DateTimeProperty(auto_now_add=True)  #创建时间
    captureDatetime = db.DateTimeProperty()           #拍摄时间
    album   = db.ReferenceProperty(Album)             #所属相册
    
    def genThumbURL(self, size=196):
        return images.get_serving_url(str(self.blob.key()), size=int(size), crop=True)

    def genURL(self):
        return images.get_serving_url(str(self.blob.key()), size=0)
