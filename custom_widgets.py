# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
from PyKDE4.kdeui import KLineEdit
from PyQt4.QtCore import Qt

class SearchEntry (KLineEdit):

    def keyPressEvent (self, event):
        if event.key ()==Qt.Key_Escape:
            # print "esc!"
            self.setText ('')
        else:
            KLineEdit.keyPressEvent (self, event)

# end
