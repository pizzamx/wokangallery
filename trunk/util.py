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

from google.appengine.api import users
from google.appengine.api import memcache

def adminOP(func):
    def wrapper(self, *args, **kw):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        elif not users.is_current_user_admin():
            self.redirect('/')
        else:
            func(self, *args, **kw)
    return wrapper
    
def memcached(t):
    "decorate cachable calls"
    def w(func):
        def wrapper(self, *args):
            #so func_name should be unique
            cachedData = memcache.get(func.func_name)
            if cachedData is not None:
                #logging.debug('%s hit', func.func_name)
                return cachedData
            
            #logging.debug('%s missed', func.func_name)
            cachedData = func(self, *args)
            if t == -1:
                memcache.add(func.func_name, cachedData)
            else:
                memcache.add(func.func_name, cachedData, t)
            return cachedData
        return wrapper
    return w
