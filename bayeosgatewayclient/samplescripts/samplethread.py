"""Creates an example writer and sender using threads."""
from time import sleep
from bayeosgatewayclient import BayEOSWriter, BayEOSSender
import tempfile
from os import path

PATH = path.join(tempfile.gettempdir(),'bayeos-device') 
NAME = 'Python-Thread-Example2'
URL = 'http://localhost/gateway/frame/saveFlat'

writer = BayEOSWriter(PATH)
writer.save_msg('Writer was started.')

## Create the sender and start it in the background
sender = BayEOSSender(PATH, NAME, URL)
sender.start()


## main tread - runs unlimited
while True:
    writer.save(values={"Temperatur":22.0,"Feuchte":55.2},value_type=0x61) 
    sleep(5)
    writer.flush()
