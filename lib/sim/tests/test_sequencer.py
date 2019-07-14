import sys

sys.path.append(
    '/storage/emulated/0/qpython/')

from sim.sequencer import DEFAULT_SEQUENCER as SEQ
from sim.tests import okeq


# Test sequencer
def callback1(time):
    msg = 'callback1(t={})'
    print(msg.format(time))


def callback2(time):
    msg = 'callback2(t={})'
    print(msg.format(time))
    return [(7, callback1)]


print ('test single ...')
SEQ.add((5, callback1))
SEQ.run()
print('... done')
print('')

print('test single => extra ...')
SEQ.add((5, callback2))
SEQ.run()
print('... done')
print('')

print('test run to fixed time...')
SEQ.add((25, callback1))
SEQ.add((17, callback2))
SEQ.add((1000, callback2))
SEQ.run(stop=500)
print('... done up to t=500.')
print('Remaining events : {}'.format(SEQ.events))
print('\nNow run to end ...')
SEQ.run()
print('... done')
print('')

print ('test time+priority ordering')
results = []


def cb(time, priority):
    def _inner(time):
        global results
        results += [(time, priority)]
        msg = 'event @{}, priority={}'
        print(msg.format(time, priority))

    return _inner


def req(time, priority=None):
    if priority != None:
        key = (time, priority)
    else:
        key = time
    SEQ.add(
        (key,
         cb(time, priority)
         ))


req(10.0)
req(20.0, 1)
req(10.0, 4)
req(20.0, 0)
req(20.0)
req(20.0, -1.5)
req(20.0, 2)
req(20.001, 10)
req(20.001, 25)
SEQ.run(10.0)
okeq(results, [
    (10.0, 4),
    (10.0, None),
])
results = []
SEQ.run(20.0)
okeq(results, [
    (20.0, 2),
    (20.0, 1),
    (20.0, 0),
    (20.0, None),
    (20.0, -1.5),
])
results = []
SEQ.run()
okeq(results, [
    (20.001, 25),
    (20.001, 10),
])
print('')

print('check an event can '
      'add an event at the same time.')


def cb_add_2(time):
    global results
    results += [(time, '?',
                 'added')]
    msg = 'extra event action @{}'
    print (msg.format(time))


def cb_add(time):
    global results
    results += [(time, '?',
                 'adding')]
    msg = ('extra event add @{} adds '
           'later at same time')
    print (msg.format(time))
    SEQ.add((time, cb_add_2))
    SEQ.add((time + 0.5, cb_add_2))


# Note: happens last although done now.
SEQ.add(((75., -9999), cb_add))
req(75.)
SEQ.add((75., cb_add))
req(75., 2)
req(75.)

results = []
SEQ.run(75.)
okeq(results, [
    (75., 2),
    (75., None),
    (75., '?', 'adding'),
    (75., None),
    (75., '?', 'added'),
    (75., '?', 'adding'),
    (75., '?', 'added'),
])
results = []
SEQ.run()
okeq(results, [
    (75.5, '?', 'added'),
    (75.5, '?', 'added'),
])

print('')
