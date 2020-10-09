"""Creates an example writer and sender using threads."""
from time import sleep
from bayeosgatewayclient import BayEOSWriter, BayEOSSender, BayEOSFrame
import logging
import tempfile
from os import path

PATH = path.join(tempfile.gettempdir(),'bayeos-device')
BACKUP_PATH =  path.join(tempfile.gettempdir(),'bayeos-device-backup')
NAME = 'Python-SampleFrames'

URL = 'http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveFlat'

writer = BayEOSWriter(PATH,max_time=10,log_level=logging.DEBUG)
writer.save_msg('Writer was started.')

sender = BayEOSSender(PATH, NAME, URL,backup_path=BACKUP_PATH)
sender.start()

while True:
    data_frame_simple = BayEOSFrame.factory(0x1)
    data_frame_simple.create(values=(1, 5, 4), value_type=0x22)  # Data Type Integer
    writer.save_frame(data_frame_simple.frame)
    routed_origin_frame = BayEOSFrame.factory(0xd)
    routed_origin_frame.create(origin="RoutedOrigin", nested_frame=data_frame_simple.frame)
    writer.save_frame(routed_origin_frame.frame)
    sleep(2)
    
    # in the second try - checksum frames are send
    # first direct - second nested in routed origin frame
    data_frame_simple = BayEOSFrame.factory(0x1)
    data_frame_simple.create(values=(2, 5, 4), value_type=0x22)  # Data Type Integer
    checksum_frame = BayEOSFrame.factory(0xf)
    checksum_frame.create(data_frame_simple.frame)
    writer.save_frame(checksum_frame.frame)
    sleep(2)
    routed_origin_frame = BayEOSFrame.factory(0xd)
    routed_origin_frame.create(origin="RoutedOrigin", nested_frame=checksum_frame.frame)
    writer.save_frame(routed_origin_frame.frame)
    
    ## test writer.save methode
    v={'test1':1,'test2':3}
    writer.save(v) ## Channel test1 and test2
    v=[10,11,12]
    writer.save(v) ## Channel 1-3
    writer.save(v,offset=10) ## Channel 11-13
    writer.save(v,origin='Python-SampleFrames -- fixed Origin')
    writer.save(v,origin='with routed Origin',routed=True)
    
    writer.flush()
   
    
    sleep(6)