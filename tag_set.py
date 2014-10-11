#! /usr/bin/python

import sys

from satyr.song import Song

s= Song (None, sys.argv[1], onDemand=False)
# artist, year, collection, diskno, album, trackno, title, length
for index, tag in enumerate (['artist', 'year', 'collection', 'diskno', 'album',
                          'trackno', 'title', 'length'], 2):
    s[tag]= sys.argv[index]
s.saveMetadata ()
