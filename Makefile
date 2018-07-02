clean:
	rm -Rf *.log *.pyc __pycache__ __stdout__

# test using python 3 for the monitored executables
test:
	./memprof.py -p test.png -f test_files.dat -o test.out

# test using python 2 for the monitored executables
test2:
	./memprof.py -p test2.png -f test2_files.dat -o test2.out

# do really short tests to show time between tests
short:
	./memprof.py -i short,"ls -lR" -i short2,"ls -lR" -a "test annotation"

all:	clean test test2

