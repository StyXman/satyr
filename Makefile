default.py: default.ui
	pyuic4 $< | sed 's/searchentry/search_entry/g' > $@
