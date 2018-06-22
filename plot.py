import matplotlib
import matplotlib.pyplot as plt
import common

MByte = 1000000
MemUnit = 'MiB'

def plot(t, s, anno):
    """
    Plot a graph.

    t     time series
    s     data series
    anno  a list of tuples - annotations
    """

    max_t = max(t)
    max_s = (max(s) // 100) * 100

    (fig, ax) = plt.subplots()
    ax.plot(t, s)
    ax.set(xlabel='time (s)', ylabel=f'Memory used ({MemUnit})',
           title=f'Memory usage by time (loops={common.loops})')
    ax.grid()

    # add extra vertical line at start
    l = matplotlib.lines.Line2D((0, 0), (-100,10000), color='red', linewidth=0.5)
    ax.add_line(l)

    # now delimit each named test and show name+delta
    for (end_time, delta, name) in anno:
        ax.text(end_time-delta, max_s, f'{name} - {delta:.2f}s', rotation=270,
                horizontalalignment='left', verticalalignment='top')

        # draw vertical line at end of measurement
        l = matplotlib.lines.Line2D((end_time, end_time), (-100,10000),
                                    color='red', linewidth=0.5)
        ax.add_line(l)
    
    fig.savefig(f'test.png')
    plt.show()

# read data from file 'memprof.out'
# 1529579605.214047|name|274432
with open('memprof.out') as fd:
    lines = fd.readlines()

t = []
s = []
anno = []
start_time = None
last_name = None
last_start = None

for line in lines:
    (t_elt, name, s_elt) = line.split('|')
    t_elt = float(t_elt)

    if start_time is None:
        start_time = t_elt

    t_elt -= start_time
    s_elt = int(s_elt)/MByte

    s.append(s_elt)
    t.append(t_elt)

    if last_name != name:
        if last_name:
            delta = t_elt - last_start
            anno.append((t_elt, delta, last_name))
        last_name = name
        last_start = t_elt

delta = t_elt - last_start
anno.append((t_elt, delta, last_name))

plot(t, s, anno)
