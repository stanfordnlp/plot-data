PROC_DIR=output

all : verify20180810 turk20180810 turk20180808 turk20180805 turk20180803

gh-pages:
	gh-pages -d output
