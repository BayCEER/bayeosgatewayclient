from bayeosgatewayclient import BayEOSFrame
from time import time,sleep

data_frame_simple = BayEOSFrame.factory(0x1)
data_frame_simple.create(values=(2, 5, 4), value_type=0x22)  # Data Type Integer

print(BayEOSFrame.parse_frame(data_frame_simple.frame)) 
sleep(0.3)
print(BayEOSFrame.parse_frame(data_frame_simple.frame)) 

origin_frame = BayEOSFrame.factory(0xb)
origin_frame.create(origin="My Origin", nested_frame=data_frame_simple.frame)

print(BayEOSFrame.parse_frame(origin_frame.frame))
sleep(0.3)
print(BayEOSFrame.parse_frame(origin_frame.frame))

delayed_frame = BayEOSFrame.factory(0x7)
delayed_frame.create(nested_frame=origin_frame.frame,delay=1000)
print(BayEOSFrame.parse_frame(delayed_frame.frame))
sleep(0.3)
print(BayEOSFrame.parse_frame(delayed_frame.frame))

