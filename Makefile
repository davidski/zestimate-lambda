SUBDIRS   := $(wildcard functions/*/)
ZIPS      := $(addsuffix .zip,$(subst functions,,$(subst /,,$(SUBDIRS))))
MAIN      = main.py
BUILD_DIR = build

echo:
	@echo $(value SUBDIRS)
	@echo $(value ZIPS)

#$(ZIPS): functions/%.zip : | %
#	zip BUILD_DIR/$@ functions/$*/${MAIN}

dist: $(ZIPS)

${BUILD_DIR}:
	mkdir ${BUILD_DIR}

manual: | ${BUILD_DIR}
	zip -j ${BUILD_DIR}/update-zestimate.zip functions/update-zestimate/${MAIN}
	zip -j ${BUILD_DIR}/update-zestimate.zip $VIRTUAL_ENV/lib/python2.7/site-packages/*


clean:
	rm $(ZIPS)