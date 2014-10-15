#! /bin/bash

mkdir -pv tests/src

# create a 10s empty song
sox --null tests/src/01-null.mp3 trim 0 10

# copy, add tags
cp tests/src/01-null.mp3 tests/src/02-tags.mp3
# artist, year, collection, diskno, album, trackno, title, length
python tag_set.py tests/src/02-tags.mp3 'Foo' '1977' '' 0 'Fighters' 2 'Tags' 10

# should not be indexed
touch tests/src/03-not_index.txt
