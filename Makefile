clean:
	rm -Rf *.log *.pyc __pycache__ __stdout__

# test using python 3 for the monitored executables
test:
	./memprof.py -g test.png -f test_files.dat -o test.out

# test using python 2 for the monitored executables
test2:
	./memprof.py -g test2.png -f test2_files.dat -o test2.out

all:	clean test test2

