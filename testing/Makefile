DB = globalAveAtmos.db globalAveIce.db globalAveLand.db globalAveOcean.db \
     nhAveAtmos.db nhAveIce.db nhAveLand.db shAveAtmos.db shAveIce.db \
     shAveLand.db tropicsAveAtmos.db tropicsAveLand.db

OBJECTS=$(patsubst %, db/%, $(DB))

all: $(OBJECTS)

test_data:
	curl -o gfdlvitals_test_data.tar.gz ftp://ftp.gfdl.noaa.gov/pub/John.Krasting/gfdlvitals/gfdlvitals_test_data.tar.gz
	tar -xzvf gfdlvitals_test_data.tar.gz
	rm -f gfdlvitals_test_data.tar.gz
	rm -fR test_data/ascii

$(OBJECTS): test_data
	gfdlvitals -m ESM4 -g test_data/gridspec.tar -o db test_data/history

check: $(OBJECTS)
	mkdir -p results
	for f in $(DB) ; do \
	    sqlite3 db/$$f .dump | grep VALUES | sort --ignore-case > results/$$f.txt ; \
	done
	diff results reference

clean:
	rm -f $(OBJECTS)
	rm -fR db
	rm -fR results

distclean:
	rm -f $(OBJECTS)
	rm -fR db/
	rm -fR results/
	rm -fR test_data/
