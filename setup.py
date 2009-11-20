#!/usr/bin/python
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

from distutils.core import setup
import sys

python_version='%d.%d' % sys.version_info[:2]

data= dict (
    name='satyr',
    version='0.1-beta1',
    description="audio player developed in PyKDE4.",
    long_description="""
satyr pretends to have the following features (some are not implemented yet):

 * The PlayList and the Collection(s) are the same thing.
 * Yours is a Collection of Albums, nothing else.
 * Some Albums are from the same artists and some are compilations.
 * If you want an ephemeral playlist you could queue songs.
 * If you want non-ephemeral playlists, then this player is not for you.
 * Ability to search à la xmms, but in the same interface.
 * Tag reading and writing.
 * Order you collection based on the tags.
 * The collection discovers new files and adds them to the playlist on the fly.
 * Be able to use all the program only with your keyboard (die, mouse, die!).
""",
    author='Marcos Dione',
    author_email='mdione@grulic.org.ar',
    url='http://savannah.nongnu.org/projects/satyr/',
    license='GPL',
    classifiers=[
        'Development Status :: 4 - Beta',

        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',

        'License :: OSI Approved :: GNU General Public License (GPL)',

        'Natural Language :: Spanish',
        'Natural Language :: English',

        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',

        'Programming Language :: Python',

        'Topic :: Internet',
        'Topic :: System :: Archiving :: Mirroring',
        'Topic :: Utilities',
        ],

    requires= ['PyKDE4(>=4.3)', 'tagpy(>=0.94)', 'PyQt4(>=4.5, <4.6)'],
    packages= ['satyr', 'satyr.skins'],
    # this kinda suck
    data_files= [
        ('lib/python%s/site-packages/satyr/skins/' % python_version,
            ('satyr/skins/default.ui', 'satyr/skins/simple.ui'))],
    scripts= ['satyr_main'],
    )

if __name__=='__main__':
    setup (**data)

# end
