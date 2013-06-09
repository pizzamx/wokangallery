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
import webapp2

from google.appengine.ext import db, blobstore
from google.appengine.api import users, images, memcache
from google.appengine.ext.webapp import blobstore_handlers

from mako.template import Template
from mako.lookup import TemplateLookup

import simplejson

from model import Photo, Album, Thumbnail
from util import memcached

import os, logging, urllib2, math, calendar, re, string, base64

from datetime import tzinfo, timedelta, datetime, date

class QueryBase(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        super(QueryBase, self).__init__(request=request, response=response)
        #页面标题
        self.title = ''
        
    def dumpMultiPage(self, posts, pageOffset, tplName):
        #baseUrl代表根域名，redirectUrl用于（可能的）跳转
        url = self.request.url
        baseUrl = url[:url.find('/', 8)]    #8 for https
        
        #分页
        pageOffset = 1 if pageOffset is None else int(pageOffset)
        pageCount = int(math.ceil(float(posts.count()) / util.POST_PER_PAGE))
        posts = posts.order('-date').fetch(util.POST_PER_PAGE, (pageOffset - 1) * util.POST_PER_PAGE)
        #分页按钮的链接前缀（最后要以/结束）
        if re.match(r'.*?/page/\d*', url, re.IGNORECASE):
            path = re.sub(r'(.*?/)page/\d*', r'\1', url)
        else:
            path = url if url.endswith('/') else url + '/'

        #输出
        template = self.getTemplate(tplName)
        self.response.write(template.render_unicode(baseUrl=baseUrl, redirectUrl=url, posts=posts, isAdmin=users.is_current_user_admin(), calendar=widget.Calendar(path), 
                                                        widgets=[widget.BlogUpdates(), widget.RecentComment(), widget.TagCloud()],
                                                        pageCount=pageCount, currentPage=pageOffset, pagePath=path, title = self.title))
    
    def getTemplate(self, name):
        #读取模板文件
        mylookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'template')], 
                                  format_exceptions=True)
        return mylookup.get_template(name)
    
    #知道啥意思不……four O four……lol
    def fof(self):
        template = self.getTemplate('404.html')
        self.response.set_status(404)
        logging.info('Invalid request: %s' % self.request.path)
        self.response.write(template.render_unicode(title = u'出错啦', uri=self.request.path))

class Index(QueryBase):
    def get(self):
        allAlbums = Album.all().order('name')
        template = self.getTemplate('index.html')
        self.response.write(template.render_unicode(aas=allAlbums, isAdmin=users.is_current_user_admin()))
        
class ListAlbum(QueryBase):
    def get(self, k):
        album = Album.get_by_key_name('_' + urllib2.unquote(k).decode('utf-8'))
        template = self.getTemplate('album.html')
        self.response.write(template.render_unicode(album=album, isAdmin=users.is_current_user_admin()))
        
class DispThumbnail(webapp2.RequestHandler):
    def get(self, id):
        hkeys = self.request.headers.keys()
        """
        if 'Referer' in hkeys: 
            referer = self.request.headers['Referer']
            if referer:
                if re.search(r'https?:\/\/.*?\.wokanxing\.info.*', referer, re.I) or referer.find('lazybonereborn') != -1:
        """
        t = Thumbnail.get_by_id(long(id))
        if t:
            name = t.name
            self.response.headers['Content-Type'] = str('image/%s' % name[name.rfind('.') + 1:])
            self.response.write(t.data)
            
class ServePhoto(webapp2.RequestHandler):
    def get(self, id, size):
        #size = (t)iny, (s)mall, (m)edium, (l)arge, (f)ull
        p = Photo.get_by_id(long(id))
        if p:
            gImg = images.Image(p.data)
            size = (size if size else 's').lower()
            if size == 'f':
                limit = -1
            elif size == 'l':
                limit = 1024
            elif size == 'm':
                limit = 960
            elif size == 't':
                limit = 240
            else:
                limit = 480
            
            ##################################
            limit = -1
            ##################################
            stream = p.data
            if limit > 0:
                if gImg.width > gImg.height:
                    h = gImg.height * limit / gImg.width
                    stream = images.resize(stream, limit, h)
                else:
                    w = gImg.width * limit / gImg.height
                    stream = images.resize(stream, w, limit)
            name = p.name
            
            FMT = '%A, %d %B %Y %H:%M %Z'
            self.response.headers['Content-Type'] = str('image/%s' % name[name.rfind('.') + 1:])
            self.response.headers['Last-Modified'] = p.cr_time.strftime(FMT)
            self.response.headers['Expires'] = (datetime.now() + timedelta(days=365)).strftime(FMT)
            self.response.headers['Cache-Control']  = 'public, max-age=315360000'
            self.response.headers['Date'] = datetime.now().strftime(FMT)
            self.response.write(stream)

class GeneratePhotoURL(webapp2.RequestHandler):
    def get(self, key):
        self.response.write(key)

class DispPhoto(QueryBase):
    def getData(self):
        cachedData = memcache.get(str(self.album.key()))
        if cachedData is not None:
            return cachedData

        ids = []
        urls = []
        dimensions = []
        info = {}
        for p in self.album.photo_set.order('name'):
            ids.append(str(p.key().id()))
            urls.append(p.genURL())
            dimensions.append([int(p.width), int(p.height)])
            info[str(p.key().id())] = {
                'name': str(p.name),
                'desc': p.desc,
                'capTime': p.captureDatetime.strftime('%m/%d/%Y %H:%M')
            }
        memcache.add(str(self.album.key()), (ids, urls, dimensions, info))
        return (ids, urls, dimensions, info)

    def get(self, an):
        self.album = Album.get_by_key_name('_' + urllib2.unquote(an).decode('utf-8'))
        #album = Album.get_by_key_name('_' + base64.b64encode(urllib2.unquote(an).decode('utf-8')))
        #p = Photo.get_by_id(long(id))
        if self.album:
            template = self.getTemplate('photo.html')
            ids, urls, dimensions, info = self.getData()
            self.response.write(template.render_unicode(album=self.album, ids=ids, urls=urls, dimensions=dimensions, info=simplejson.dumps(info), isAdmin=users.is_current_user_admin()))
            
class Dummy(webapp2.RequestHandler):
    def get(self, anything):
        self.response.write(anything)
        
class makeURL(blobstore_handlers.BlobstoreUploadHandler):
    def get(self):
        url = blobstore.create_upload_url('/admin/api/upload')
        self.response.write(url)

class GetPhotoInfo(webapp2.RequestHandler):
    def get(self, id):
        p = Photo.get_by_id(long(id))
        if p:
            self.response.write(simplejson.dumps({
                'name': p.name,
                'desc': p.desc,
                'crTime': p.cr_time.strftime('%Y%m%d %H:%M:%S')
            }, ensure_ascii=False))

class ListAlbums(webapp2.RequestHandler):
    def get(self):
        albums = []
        for album in Album.all():
            albums.append({
                'name': album.name,
                'count': album.photo_set.count(),
                'crTime': album.cr_time.strftime('%Y-%m-%d- %H:%M:%S')
            })
        self.response.write(simplejson.dumps(albums))