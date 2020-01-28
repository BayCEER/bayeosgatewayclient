"""Reads BayEOS options from command line."""

from time import time, sleep
from bayeosgatewayclient import BayEOSWriter, BayEOSSender, bayeos_argparser

# Fetch input arguments
args = bayeos_argparser('This is the text to appear on the command line.')

WRITER_SLEEP = float(args.writer_sleep)
MAX_CHUNK = float(args.max_chunk)

NAME = args.name + '-WS' + str(WRITER_SLEEP) + '-M' + str(MAX_CHUNK)
PATH = args.path + '/' + NAME + '/'
if args.url:
    URL = args.url
else:
    URL = 'http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveFlat'

print('name to appear in Gateway is', NAME)
print('max-chunk is', MAX_CHUNK, 'byte')
print('writer sleep time is', WRITER_SLEEP, 'sec')
print('path to store writer files is', PATH)

# init writer and sender
writer = BayEOSWriter(PATH, MAX_CHUNK)
writer.save_msg('Writer was started.')

sender = BayEOSSender(PATH, NAME, URL, 'import', 'import')
sender.start()

# start measurement
while True:
    writer.save([time()], value_type=0x21)
    sleep(WRITER_SLEEP)