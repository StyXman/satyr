TESTFILESDIR=tests/src
TESTFILES=$(foreach file,01-null.mp3 02-tags.mp3 03-do_not_index.txt,$(TESTFILESDIR)/$(file))


all: $(TESTFILES)

$(TESTFILESDIR):
	mkdir -pv $(TESTFILESDIR)

$(TESTFILESDIR)/01-null.mp3: $(TESTFILESDIR)
	sox --null $@ trim 0 10

$(TESTFILESDIR)/02-tags.mp3: $(TESTFILESDIR)/01-null.mp3
	cp $< $@
	python tag_set.py $@ 'Foo' '1977' '' 0 'Fighters' 2 'Tags' 10

$(TESTFILESDIR)/03-do_not_index.txt:
	touch $@

tests: test

test: $(TESTFILES)
	python -m unittest discover -v tests
