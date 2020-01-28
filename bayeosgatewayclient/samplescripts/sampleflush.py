"""Creates an example writer and flushes it before max chunk size is reached."""

from time import sleep
from bayeosgatewayclient import BayEOSWriter

PATH = '/tmp/bayeos-device1/'
writer = BayEOSWriter(PATH, max_chunk=1000)
writer.save_msg('Writer was started.', origin='Python-Writer-Flush-Example')
flush = 0

while True:
    #print('adding frame')
    writer.save(values=[2.1, 3, 20.5], value_type=0x01, offset=2, origin='Python-Writer-Flush-Example')
    flush += 1
    if flush % 5 == 0: # flush writer every 5 seconds
        writer.save_msg('Writer was flushed.', origin='Python-Writer-Flush-Example')
        writer.flush()        
        print('flushed writer')
        flush = 0
    sleep(1)