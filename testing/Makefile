ESM4_DB = globalAveAtmos.db globalAveIce.db globalAveLand.db globalAveOBGC.db globalAveOcean.db \
          nhAveAtmos.db nhAveIce.db nhAveLand.db nhAveOBGC.db \
          shAveAtmos.db shAveIce.db shAveLand.db shAveOBGC.db \
          tropicsAveAtmos.db tropicsAveLand.db tropicsAveOBGC.db

ESM2_DB = globalAveAtmos.db globalAveOcean.db nhAveOBGC.db shAveAtmos.db \
          shAveOcean.db tropicsAveOBGC.db globalAveOBGC.db nhAveAtmos.db \
		  nhAveOcean.db shAveOBGC.db tropicsAveAtmos.db tropicsAveOcean.db

ESM4_OBJECTS=$(patsubst %, db-esm4/%, $(ESM4_DB))
ESM2_OBJECTS=$(patsubst %, db-esm2/%, $(ESM2_DB))

all: $(ESM4_OBJECTS) $(ESM2_OBJECTS)

esm2: $(ESM2_OBJECTS)

test_data:
	curl -o gfdlvitals_test_data.latest.tar.gz https://extranet.gfdl.noaa.gov/~John.Krasting/testing/gfdlvitals_test_data.latest.tar.gz
	tar -xzvf gfdlvitals_test_data.latest.tar.gz
	rm -f gfdlvitals_test_data.latest.tar.gz
	rm -fR test_data/ascii

$(ESM4_OBJECTS): test_data
	gfdlvitals -m CM4 -o db-esm4 test_data/esm4/history

$(ESM2_OBJECTS): test_data
	gfdlvitals -m ESM2 -o db-esm2 test_data/esm2g/history

check: $(ESM4_OBJECTS) $(ESM2_OBJECTS)
	mkdir -p results/esm4
	for f in $(ESM4_DB) ; do \
	    sqlite3 db-esm4/$$f .dump | grep VALUES | sort --ignore-case > results/esm4/$$f.txt ; \
	done
	mkdir -p results/esm2
	for f in $(ESM2_DB) ; do \
	    sqlite3 db-esm2/$$f .dump | grep VALUES | sort --ignore-case > results/esm2/$$f.txt ; \
	done
	diff -r results reference

clean:
	rm -f $(OBJECTS)
	rm -fR db-esm4
	rm -fR db-esm2
	rm -fR results

distclean:
	rm -f $(OBJECTS)
	rm -fR db-esm4/
	rm -fR db-esm2/
	rm -fR results/
	rm -fR test_data/

