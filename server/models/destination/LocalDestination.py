#-*- coding: utf-8 -*-

import os

from django.db import models

from .Destination import Destination

class LocalDestination(Destination):
    directory = models.CharField(verbose_name=u'diretório',
                                 max_length=1024,
                                 blank=True,
                                 default=u'~')
    
    def backup(self, contents, subdir, filename, *args, **kwargs):
        print "Hello! This is %s's backup method" % self.__class__.__name__
        fd = os.path.join(self.directory, subdir)
        if not os.path.exists(fd):
            os.makedirs(fd)
        fn = os.path.join(fd,filename)
        try:
            with open(fn, 'wb+') as f:
                for data in iter(lambda: contents.read(64 * 1024), ''):
                    f.write(data)
        except Exception, e:
            print e
            return False
        return True
        
    def restore(self, subdir, filename, *args, **kwargs):
        print "Hello! This is %s's restore method" % self.__class__.__name__
        fn = os.path.join(self.directory,
                          subdir,
                          filename)
        try:
            with open(fn, 'rb') as f:
                return ((data for data in iter(lambda: f.read(64 * 1024), '')), True)
        except Exception, e:
            print e
            return None, False
    
    
    class Meta:
        verbose_name = u'destino local'
        verbose_name_plural = u'destinos locais'
        app_label = 'server'