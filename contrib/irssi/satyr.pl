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

use strict;
use vars qw($VERSION %IRSSI);

# depends on qdbus

use Irssi;
$VERSION = '0.4';
%IRSSI = (
    authors     => 'Marcos Dione',
    contact     => 'mdione@grulic.org.ra',
    name        => 'Ask satyr what\'s playing now',
    description => 'Do I have to say more?',
    license     => 'GPLv2',
);

Irssi::command_bind ('np', sub {
    my ($data, $server, $witem) = @_;

    if (!$server || !$server->{connected}) {
        Irssi::print("Not connected to server");
        return;
    }

    if ($witem && ($witem->{type} eq "CHANNEL" ||
                   $witem->{type} eq "QUERY")) {
        my $str= `qdbus org.kde.satyr /player nowPlaying`;
        chomp ($str);
        # Irssi::print("ok so far: $str");
        # we have to say where we're sending the action? really???
        $witem->command ("action ".$witem->{name}." playing with satyr: $str");
    } else {
        Irssi::print("No active channel/query in window");
    }
} );

Irssi::print("satyr loaded. the command is /np. use with discretion");
