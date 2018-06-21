clean:
	rm -Rf *.out *.log stdout

test:
	./memprof.py -i name,test_exe.py
