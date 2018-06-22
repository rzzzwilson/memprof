clean:
	rm -Rf *.out *.log stdout *.png images

test:
	./memprof.py -i naive,concat_naive.py -i join,concat_join.py -i stringIO,concat_stringio.py -i comprehension,concat_comprehension.py
