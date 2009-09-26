# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

from PyQt4.QtCore import QObject
# from PyQt4.phonon import Phonon
from kaa import metadata

class Song (QObject):
    def __init__ (self, filepath):
        # sigsegv :(
        # KCrash: Application 'satyr.py' crashing...
        # sock_file=/home/mdione/.kde/socket-mustang/kdeinit4__0
        # satyr.py: Fatal IO error: client killed
        # ms= Phonon.MediaSource (filepath)
        # mo= Phonon.MediaObject ()
        # mo.setCurrentSource (ms)
        # print mo.metadata ()

        try:
            info= metadata.parse (filepath)
            # print info.artist, info.album, info.trackno, info.title
        except Exception, e:
            print filepath
            print e
            print '-----'

        for attr in ('artist', 'album', 'trackno', 'title'):
            setattr (self, attr, getattr (info, attr, None))
        self.filepath= filepath

# end
