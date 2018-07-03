clean:
	rm -Rf *.out *.log *.pyc __pycache__

# test using python 3 for the monitored executables
test:
	./memprof.py -p test.png -f test_files.dat -o test.out -a "20,000,000 iterations"

# test using python 2 for the monitored executables
test2:
	./memprof.py -p test2.png -f test2_files.dat -o test2.out -a "20,000,000 iterations"

# do really short tests to show time between tests
short:
	./memprof.py -i short,"ls -lR" -i short2,"ls -lR" -a "test annotation"

all:	clean test test2

