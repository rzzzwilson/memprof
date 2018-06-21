clean:
	rm -f *.out *.log

test:
	./memprof.py -i name,test_exe.py
