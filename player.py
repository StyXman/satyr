# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import pyqtSignal, QObject

# dbus
import dbus.service

# std python
import time

# local
from common import SatyrObject, BUS_NAME, configBoolToBool
from model import Song

class Player (SatyrObject):
    finished= pyqtSignal ()
    stopAfterChanged= pyqtSignal (bool)

    def __init__ (self, parent, playlist, busName, busPath):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.configValues= (
            ('playing', configBoolToBool, False),
            ('paused', configBoolToBool, False),
            ('stopAfter', configBoolToBool, False),
            ('quitAfter', configBoolToBool, False),
            )
        self.loadConfig ()

        self.playlist= playlist
        self.filepath= None

        self.media= Phonon.MediaObject ()
        # god bless PyQt4.5
        self.media.finished.connect (self.next)
        self.media.stateChanged.connect (self.stateChanged)
        self.media.metaDataChanged.connect (self.printMetaData)

        self.ao= Phonon.AudioOutput (Phonon.MusicCategory, parent)
        Phonon.createPath (self.media, self.ao)

    def stateChanged (self, new, old):
        # print "state changed from %d to %d" % (old, new)
        if new==Phonon.ErrorState:
            print "ERROR: %d: %s" % (self.media.errorType (), self.media.errorString ())
            # just skip it
            self.next ()

    def printMetaData (self):
        # Song (self.filepath)
        pass

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def prev (self):
        try:
            self.playlist.prev ()
            self.filepath= self.playlist.filepath
            if self.playing:
                self.play ()
        except IndexError:
            print "playlist empty"
            self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def play (self, index=None):
        if self.paused:
            self.pause ()
        else:
            self.playing= True
            time.sleep (0.2)
            # FIXME: self.filepath should never be None
            # which implies that self.playlist.filepath should always point
            # to a filepath (or index, if we change the API)
            if self.filepath is None:
                if self.playlist.filepath is None:
                    self.next ()

            if index is not None:
                self.playlist.jumpTo (index)

            self.filepath= self.playlist.filepath

            print "playing", self.filepath
            self.media.setCurrentSource (Phonon.MediaSource (self.filepath))
            self.media.play ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def pause (self):
        """toggle"""
        if self.playing:
            if not self.paused:
                print "pa!..."
                self.media.pause ()
                self.paused= True
            else:
                print "...use!"
                self.media.play ()
                self.paused= False

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def stop (self):
        print "*screeeech*! stoping!"
        self.media.stop ()
        self.playing= False

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def next (self):
        try:
            self.playlist.next ()
            self.filepath= self.playlist.filepath
            # FIXME: this should not be here
            if self.stopAfter:
                print "stopping after!"
                # stopAfter is one time only
                self.toggleStopAfter ()
                self.stop ()
            # FIXME: this should not be here
            if self.quitAfter:
                print "quiting after!"
                # quitAfter is one time only
                self.toggleQuitAfter ()
                self.quit ()
            # FIXME: this should not be here
            elif self.playing:
                self.play ()
        except IndexError:
            print "playlist empty"
            self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleStopAfter (self):
        """toggle"""
        print "toggle: stopAfter",
        self.stopAfter= not self.stopAfter
        print self.stopAfter
        self.stopAfterChanged.emit (self.stopAfter)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleQuitAfter (self):
        """I need this for debugging"""
        print "toggle: quitAfter",
        self.quitAfter= not self.quitAfter
        print self.quitAfter

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def quit (self):
        self.stop ()
        self.saveConfig ()
        # FIXME: is this the right API?
        self.playlist.saveConfig ()
        for collection in self.playlist.collections:
            collection.saveConfig ()
        print "bye!"
        self.finished.emit ()

# end
