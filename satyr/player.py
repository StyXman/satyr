# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

# This file is part of satyr.

# satyr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# satyr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with satyr.  If not, see <http://www.gnu.org/licenses/>.


# qt/kde related
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import pyqtSignal, QString

# dbus
import dbus.service

# std python
import time

# local
from satyr.common import SatyrObject, BUS_NAME, configEntryToBool
from satyr import utils

class Player (SatyrObject):
    finished= pyqtSignal ()
    stopAfterChanged= pyqtSignal (bool)
    nowPlaying= pyqtSignal (int)

    # constants
    STOPPED= 0
    PLAYING= 1
    PAUSED=  2

    def __init__ (self, parent, playlist, busName, busPath):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.configValues= (
            # actually it doesn't make much sense to save this one
            ('state', int, Player.STOPPED),
            ('stopAfter', configEntryToBool, False),
            # or this one...
            ('quitAfter', configEntryToBool, False),
            )
        self.loadConfig ()

        self.playlist= playlist

        self.media= Phonon.createPlayer (Phonon.MusicCategory)
        self.media.finished.connect (self.next)
        self.media.stateChanged.connect (self.stateChanged)

    def stateChanged (self, new, old):
        # print "state changed from %d to %d" % (old, new)
        if new==Phonon.ErrorState:
            print "ERROR: %d: %s" % (self.media.errorType (), self.media.errorString ())
            # just skip it
            self.next ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def prev (self):
        try:
            self.playlist.prev ()
            if self.state==Player.PLAYING:
                self.play ()
        except IndexError:
            print "playlist empty"
            self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def play (self, song=None):
        if self.state==Player.PAUSED:
            self.pause ()
        else:
            self.state= Player.PLAYING
            # FIXME? this should not be here, but right now seems to be needed
            # BUG: and it is still not enough
            time.sleep (0.4)

            # the QPushButton.clicked() emits a bool,
            # and it's False on normal (non-checkable) buttons
            # it's not false, it's 0, which is indistinguishable from play(0)
            # also, 0!=False is False?
            # >>> 0!=False
            # False
            if song is not None:
                print "player.play()", song
                self.playlist.jumpToSong (song)

            self.filepath= self.playlist.filepath

            print "playing", self.filepath
            url= utils.path2qurl (self.filepath)
            self.media.setCurrentSource (Phonon.MediaSource (url))
            self.media.play ()

            self.nowPlaying.emit (self.playlist.index)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def play_pause (self):
        """switches between play and pause"""
        if self.state in (Player.STOPPED, Player.PAUSED):
            # self.state= Player.PLAYING
            # self.media.play ()
            self.play ()
        else:
            # Player.PLAYING
            # self.state= Player.PAUSED
            # self.media.pause ()
            self.pause ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def pause (self):
        """toggle"""
        if self.state==Player.PLAYING:
            print "pa!..."
            self.media.pause ()
            self.state= Player.PAUSED
        elif self.state==Player.PAUSED:
            print "...use!"
            self.media.play ()
            self.state= Player.PLAYING

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def stop (self):
        print "*screeeech*! stoping!"
        self.media.stop ()
        self.state= Player.STOPPED

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def next (self):
        try:
            self.playlist.next ()
            # FIXME: this should not be here
            if self.stopAfter:
                print "stopping after!"
                # stopAfter is one time only
                # BUG: after switching to states, it stops in the wrong song
                self.toggleStopAfter ()
                self.stop ()
            # FIXME: this should not be here
            if self.quitAfter:
                print "quiting after!"
                # quitAfter is one time only
                self.toggleQuitAfter ()
                self.quit ()
            # FIXME: this should not be here
            elif self.state==Player.PLAYING:
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

    # @dbus.service.method (BUS_NAME, in_signature='', out_signature='s')
    # def nowPlaying (self):
    #     return self.playlist.formatSong (self.playlist.song)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def quit (self):
        self.stop ()
        # save them in 'order'
        self.saveConfig ()
        self.playlist.saveConfig ()
        self.playlist.collaggr.saveConfig ()
        for collection in self.playlist.collections:
            collection.saveConfig ()
        print "bye!"
        self.finished.emit ()

# end
