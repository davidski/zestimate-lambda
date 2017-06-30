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
	pwd
	zip -j ${BUILD_DIR}/update-zestimate.zip functions/update-zestimate/${MAIN}
	echo ${TRAVIS_BUILD_DIR}
	cd $(VIRTUAL_ENV)/lib/python3.6/site-packages && zip -r ${TRAVIS_BUILD_DIR}/${BUILD_DIR}/update-zestimate.zip *
#	zip -r ${BUILD_DIR}/update-zestimate.zip $(VIRTUAL_ENV)/lib/python2.7/dist-packages/*


clean:
	rm $(ZIPS)