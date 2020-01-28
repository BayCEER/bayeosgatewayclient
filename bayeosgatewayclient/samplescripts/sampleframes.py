"""Creates example BayEOS Frames."""

from bayeosgatewayclient import BayEOSFrame

# Data Frames, simple
data_frame_simple = BayEOSFrame.factory(0x1)
data_frame_simple.create(values=(2, 5, 4), value_type=0x22)  # Data Type Integer
data_frame_simple.print_dict()
data_frame_simple.print_hex()
print(BayEOSFrame.parse_frame(data_frame_simple.frame))

# Data Frame with Channel Offset
data_frame_offset = BayEOSFrame.factory()  # 0x1 is default
data_frame_offset.create([2.3, 4.5], value_type=0x01, offset=2)  # Data Type float
data_frame_offset.print_dict()
 
# Data Frame with Channel Indices
data_frame_indices = BayEOSFrame.factory()
data_frame_indices.create(([3, 1], [2, 5]), value_type=0x41)  # Data Type float
data_frame_indices.print_dict()

data_frame_indices2 = BayEOSFrame.factory()
data_frame_indices2.create(((3, 1), (2, 5)), value_type=0x42)  # Data Type Integer
data_frame_indices2.print_dict()
 
# Message Frames
message_frame = BayEOSFrame().factory(0x4)
message_frame.create(message="This is an important message.")
message_frame.print_dict()
 
error_message_frame = BayEOSFrame().factory(0x5)
error_message_frame.create("This is an ERROR message.")
error_message_frame.print_dict()
 
# Origin Frame
origin_frame = BayEOSFrame.factory(0xb)
origin_frame.create(origin="My Origin", nested_frame=data_frame_simple.frame)
origin_frame.print_dict()
 
 
# Routed Frame
routed_frame_rssi = BayEOSFrame.factory(0x8)
routed_frame_rssi.create(12,3332,64,data_frame_simple.frame)
routed_frame_rssi.print_dict()

routed_frame = BayEOSFrame.factory(0x6)
routed_frame.create(11,3331,routed_frame_rssi.frame)
routed_frame.print_dict()

# Binary Frame
binary_frame = BayEOSFrame.factory(frame_type=0xa)
binary_frame.create("This a message to be packed as binary data.".encode('utf-8'))
binary_frame.print_dict()

# Delayed Frame
delayed_frame = BayEOSFrame.factory(0x7)
delayed_frame.create(nested_frame=data_frame_simple.frame,delay=1034)
delayed_frame.print_dict()

# Timestamp Frames
timestamp_frame_sec = BayEOSFrame.factory(0x9)
timestamp_frame_sec.create(data_frame_simple.frame)
timestamp_frame_sec.print_dict()
 
timestamp_frame_msec = BayEOSFrame.factory(0xc)
timestamp_frame_msec.create(data_frame_simple.frame)
timestamp_frame_msec.print_dict()




# Checksum Frame
simple_checksum_frame = BayEOSFrame.factory(0xf)
simple_checksum_frame.create(data_frame_simple.frame)
simple_checksum_frame.print_dict()
simple_checksum_frame.print_hex()

checksum_frame = BayEOSFrame.factory(0xf)
checksum_frame.create(routed_frame.frame)
checksum_frame.print_dict()
checksum_frame.print_hex()
#print BayEOSFrame.parse_frame(checksum_frame.frame)


# routed Origin Frame
routed_origin_frame = BayEOSFrame.factory(0xd)
routed_origin_frame.create(origin="RoutedOrigin", nested_frame=checksum_frame.frame)
routed_origin_frame.print_dict()
routed_origin_frame.print_hex()

routed_frame_rssi = BayEOSFrame.factory(0x8)
routed_frame_rssi.create(12,3332,64,routed_origin_frame.frame)
routed_frame_rssi.print_dict()
routed_frame_rssi.print_hex()

