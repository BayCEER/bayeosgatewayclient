"""Creates an example writer and sender using threads."""
from time import sleep
from bayeosgatewayclient import BayEOSWriter, BayEOSSender
import logging
import tempfile
from os import path

PATH = path.join(tempfile.gettempdir(),'bayeos-device')
BACKUP_PATH =  path.join(tempfile.gettempdir(),'bayeos-device-backup')
NAME = 'Python-Thread-WithLogging'

URL = 'http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveFlat'

## Define logging format
## has to be done before creation of writer and sender
logging.basicConfig(format='%(asctime)s: samplethreadWithLogging.py: %(levelname)s:%(message)s ', level=logging.DEBUG)

writer = BayEOSWriter(PATH,max_time=10)
writer.save_msg('Writer was started.')

sender = BayEOSSender(PATH, NAME, URL,backup_path=BACKUP_PATH)
sender.start()

nr=0
while True:
    writer.save([nr, 3, 20.5])
    #writer.flush()
    nr+=1
    sleep(5)