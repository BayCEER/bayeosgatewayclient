"""Implementation of BayEOS Frame Protocol Specification."""

from struct import pack, unpack
from time import time
from datetime import datetime
from abc import abstractmethod

REFERENCE_TIME_DIF = (datetime(2000, 1, 1) -
                              datetime(1970, 1, 1)).total_seconds()

class BayEOSFrame(object):
    """Factory Class for BayEOS Frames."""

    @staticmethod
    def factory(frame_type=0x1):
        """Instantiates a BayEOS Frame object regarding Frame Type."""
        try:
            return FRAME_TYPES[frame_type]['class'](frame_type)
        except KeyError as err:
            print 'Frame Type ' + str(err) + ' not found.'

    def __init__(self, frame_type=0x1):
        """Creates the binary Frame Type header of BayEOS Frames."""
        self.frame_type = frame_type
        self.frame = pack('<B', frame_type)

    @abstractmethod
    def create(self, *args):
        """Initialized a BayEOS Frame with its Frame Type specific attributes.
        @param *args: list of positional arguments
        """
        return

    @abstractmethod
    def parse(self,res={}):
        """Parses a binary coded BayEOS Frame into a Python dictionary."""
        return {}        

    def print_hex(self):
        print map(hex,map(ord,self.frame))

    def print_dict(self):
        """Prints a readable form of the BayEOS Frame."""
        print self.parse(res={'origin':'','timestamp':time()})

    @staticmethod
    def to_object(frame):
        """Initializes a BayEOSFrame object from a binary coded frame.
        @param frame: binary coded String
        @returns BayEOSFrame object
        """
        try:
            frame_type = unpack('<B', frame[0:1])[0]
            return BayEOSFrame.factory(frame_type)
        except TypeError as err:
            print 'Error in to_object method: ' + str(err)

    @staticmethod
    def parse_frame(frame):
        """Parses a binary coded BayEOS Frame into a Python dictionary.
        @param frame: binary coded String
        @return Python dictionary
        """
        res={'origin':'','timestamp':time()}
        try:
            bayeos_frame = BayEOSFrame.to_object(frame)
            bayeos_frame.frame = frame
            return bayeos_frame.parse(res)
        except AttributeError as err:
            print 'Error in parse_frame method: ' + str(err)
    
    

class DataFrame(BayEOSFrame):
    """Data Frame Factory class."""
    def create(self, values=(), value_type=0x41, offset=0):
        """Creates a BayEOS Data Frame.
        @param values: list, tuple or dictionary with channel number keys
        @param value_type: defines Offset and Data Type
        @param offset: length of Channel Offset (if Offset Type is 0x0)
        """
        
        #transform in dictionary
        if type(values) is tuple or type(values) is list:
            v={}
            key=1;
            for value in values:
                if(type(value) is tuple or type(value) is list):
                    v[value[0]]=value[1]
                else: 
                    v[key]=value
                key += 1
            values=v
        
        value_type = int(value_type)
        frame = pack('<B', value_type)
        offset_type = (0xf0 & value_type)  # first four bits of the Value Type
        data_type = (0x0f & value_type)  # last four bits of the Value Type
        try:
            val_format = DATA_TYPES[data_type]['format']  # search DATA_TYPES Dictionary
        except KeyError as err:
            print 'Error in create method for Data Frame: Data Type ' + str(err) + ' is not defined.'
            return

        if offset_type == 0x0:  # Data Frame with channel offset
            frame += pack('<B', offset)  # 1 byte channel offset

        for key, value in values.iteritems():
            if offset_type == 0x40:  # Data Frame with channel indices
                frame += pack('<B', int(key))
            elif offset_type == 0x60: # labeled channel type
                frame += pack('<B',len(str(key)))
                frame += str(key)
            frame += pack(val_format, value)
        self.frame += frame

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded BayEOS Data Frame into a Python dictionary.
        @return tuples of channel indices and values
        """
        if unpack('<B', self.frame[0:1])[0] != 0x1:
            print 'This is not a Data Frame.'
            return False
        value_type = unpack('<B', self.frame[1:2])[0]
        offset_type = 0xf0 & value_type
        data_type = 0x0f & value_type
        val_format = DATA_TYPES[data_type]['format']
        val_length = DATA_TYPES[data_type]['length']
        pos = 2
        key = 0
        payload = {}
        if offset_type == 0x0:
            key = unpack('<B', self.frame[2:3])[0]  # offset
            pos += 1
        while pos < len(self.frame):
            if offset_type == 0x40:
                key = unpack('<B', self.frame[pos:pos + 1])[0]
                pos += 1
            elif offset_type == 0x60:
                labellength = unpack('<B', self.frame[pos:pos + 1])[0]
                pos += 1
                key= self.frame[pos:pos + labellength + 1]
                pos += labellength
            else:
                key += 1
            try:
                value = unpack(val_format, self.frame[pos:pos + val_length])[0]
                payload[key] = value
            except:
                print 'Unpack error'
                pass
            pos += val_length
        res['values']= payload
        res['type']=0x1
        return res

class CommandFrame(BayEOSFrame):
    """Command and Command Response Frame Factory class."""
    def create(self, cmd_type, cmd):
        """Creates a BayEOS Command or Command Response Frame.
        @param cmd_type: type of command
        @param cmd: instruction for or response from receiver
        """
        self.frame += pack('<B', cmd_type) + cmd

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Command Frame into a Python dictionary.
        @return command type and instruction
        """
        res['cmd_type']=unpack('<B', self.frame[1:2])[0]
        res['cmd']=self.frame[2:]
        res['type']=unpack('<B', self.frame[0:1])[0]
        return res

class MessageFrame(BayEOSFrame):
    """Message and Error Message Frame Factory class."""
    def create(self, message):
        """Creates a BayEOS Message or Error Message Frame.
        @param message: message to save
        """
        self.frame += message

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Message Frame into a Python dictionary.
        @return message
        """
        res['message']=self.frame[1:]
        res['type']=unpack('<B', self.frame[0:1])[0]
        return res

class RoutedFrame(BayEOSFrame):
    """Routed Frame Factory class."""
    def create(self, my_id, pan_id, nested_frame):
        """
        Creates a BayEOS Routed Frame.
        @param my_id: TX-XBee MyId
        @param pan_id: XBee PANID
        @param nested_frame: valid BayEOS Frame
        """
        self.frame += pack('<h', my_id) + pack('<h', pan_id) + nested_frame

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Routed Frame into a Python dictionary.
        @return TX-XBee MyId, XBee PANID, nested frame as a binary String
        """
        res['origin']+="/XBee%d:%d" % (unpack('<h', self.frame[3:5])[0],unpack('<h', self.frame[1:3])[0])
        return BayEOSFrame.parse_frame(self.frame[5:],res)


class RoutedRSSIFrame(BayEOSFrame):
    """Routed RSSI Frame Factory class."""
    def create(self, my_id, pan_id, rssi, nested_frame ):
        """Creates a BayEOS Routed RSSI Frame.
        @param my_id: TX-XBee MyId
        @param pan_id: XBee PANID
        @param rssi: Remote Signal Strength Indicator
        @param nested_frame: valid BayEOS Frame
        """
        self.frame += pack('<h', my_id) + pack('<h', pan_id) + pack('<B', rssi) + nested_frame

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Routed RSSI Frame into a Python dictionary.
        @return TX-XBee MyId, XBee PANID, RSSI, nested frame as a binary String
        """
        res['origin']+="/XBee%d:%d" % (unpack('<h', self.frame[3:5])[0],unpack('<h', self.frame[1:3])[0])
        res['rssi']=unpack('<B', self.frame[5:6])[0]
        return BayEOSFrame.parse_frame(self.frame[6:],res)
        
class DelayedFrame(BayEOSFrame):
    """Delayed Frame Factory class."""
    def create(self, nested_frame, delay=0):
        """Creates a BayEOS Delayed Frame.
        @param nested_frame: valid BayEOS Frame
        @param delay: delay in milliseconds
        """
        
        self.frame += pack('<l', delay) + nested_frame

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Delayed Frame into a Python dictionary.
        @return timestamp and nested_frame as a binary String
        """
        res['timestamp']-=unpack('<l', self.frame[1:5])[0]/1000
        return BayEOSFrame.parse_frame(self.frame[5:],res)

class DelayedSecondFrame(BayEOSFrame):
    """Delayed Frame Factory class."""
    def create(self, nested_frame, delay=0):
        """Creates a BayEOS Delayed Frame.
        @param nested_frame: valid BayEOS Frame
        @param delay: delay in milliseconds
        """
        
        self.frame += pack('<l', delay) + nested_frame

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Delayed Frame into a Python dictionary.
        @return timestamp and nested_frame as a binary String
        """
        res['timestamp']-=unpack('<l', self.frame[1:5])[0]
        return BayEOSFrame.parse_frame(self.frame[5:],res)

class OriginFrame(BayEOSFrame):
    """Origin Frame Factory class."""
    def create(self, origin, nested_frame):
        """Creates a BayEOS Origin Frame.
        @param origin: name to appear in the gateway
        @param nested_frame: valid BayEOS frame
        """
        origin = origin[0:255]
        self.frame += pack('<B', len(origin)) + origin + nested_frame
 
    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Origin Frame into a Python dictionary.
        @return origin and nested_frame as a binary String
        """
        length = unpack('<B', self.frame[1:2])[0]
        res['origin']=self.frame[2:length + 2]
        return BayEOSFrame.parse_frame(self.frame[length + 2:],res)

class RoutedOriginFrame(BayEOSFrame):
    """Origin Frame Factory class."""
    def create(self, origin, nested_frame):
        """Creates a routed BayEOS Origin Frame.
        @param origin: name to be appended in the gateway
        @param nested_frame: valid BayEOS frame
        """
        origin = origin[0:255]
        self.frame += pack('<B', len(origin)) + origin + nested_frame
 
    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded routed Origin Frame into a Python dictionary.
        @return origin and nested_frame as a binary String
        """
        length = unpack('<B', self.frame[1:2])[0]
        res['origin']+='/'+self.frame[2:length + 2]
        return BayEOSFrame.parse_frame(self.frame[length + 2:],res)

class BinaryFrame(BayEOSFrame):
    """Binary Frame Factory class."""
    def create(self, string):
        """Creates a BayEOS Frame including a binary coded String
        @param string: message to pack
        """
        length = len(string)
        self.frame += pack('<f', length) + pack(str(length) + 's', string)

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Binary Frame into a Python dictionary.
        @return length and content of a String
        """
        res['binary']=self.frame[5:]
        res['pos']=unpack('<f', self.frame[1:5])[0]
        res['type']=unpack('<B', self.frame[0:1])[0]
        return res

class TimestampFrameSec(BayEOSFrame):
    """Timestamp Frame (s) Factory class."""
    def create(self, nested_frame, timestamp=0):
        """Creates a BayEOS Timestamp Frame with second precision
        @param nested_frame: valid BayEOS frame
        @param timestamp: time in seconds
        """
        if not timestamp:
            timestamp = time()
        # seconds since 1st of January, 2000
        time_since_reference = round(timestamp - REFERENCE_TIME_DIF)
        self.frame += pack('<l', time_since_reference) + nested_frame
        self.nested_frame = nested_frame

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Timestamp Frame (s) into a Python dictionary.
        @return timestamp and nested_frame as a binary String
        """
        res['timestamp']=unpack('<l', self.frame[1:5])[0]
        return BayEOSFrame.parse_frame(self.frame[5:],res)

class TimestampFrame(BayEOSFrame):
    """Timestamp Frame (ms) Factory class."""
    def create(self, nested_frame, timestamp=0):
        """Creates a BayEOS Timestamp Frame with millisecond precision
        @param nested_frame: valid BayEOS frame
        @param timestamp: time
        """
        if not timestamp:
            timestamp = time()
        self.frame += pack('<q', round(timestamp * 1000)) + nested_frame
        self.nested_frame = nested_frame

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses a binary coded Timestamp Frame (ms) into a Python dictionary.
        @return timestamp and nested_frame as a binary String"""
        res['timestamp']=unpack('<q', self.frame[1:9])[0]
        return BayEOSFrame.parse_frame(self.frame[9:],res)

class ChecksumFrame(BayEOSFrame):
    """Timestamp Frame (ms) Factory class."""
    def create(self, nested_frame):
        """Creates a BayEOS Checksum Frame 
        @param nested_frame: valid BayEOS frame
        """
        self.frame += nested_frame
        checksum=0
        pos=0
        while pos < len(self.frame):
            checksum += unpack('<B', self.frame[pos:pos + 1])[0]
            pos += 1
        self.frame += pack('<H', 0xffff- (checksum&0xffff))
        self.nested_frame = nested_frame
        

    def parse(self,res={'origin':'','timestamp':time()}):
        """Parses into a Python dictionary.
        @return validChecksum and nested_frame as a binary String"""
        checksum=0
        pos=0
        while pos < len(self.frame)-2:
            checksum += unpack('<B', self.frame[pos:pos + 1])[0]
            pos += 1
        checksum += unpack('<H',self.frame[pos:])[0]
        res['validChecksum']=(checksum==0xffff)
        return BayEOSFrame.parse_frame(self.frame[1:-2],res)

DATA_TYPES = {0x1 : {'format' : '<f', 'length' : 4},  # float32 4 bytes
              0x2 : {'format' : '<i', 'length' : 4},  # int32 4 bytes
              0x3 : {'format' : '<h', 'length' : 2},  # int16 2 bytes
              0x4 : {'format' : '<b', 'length' : 1},  # int8 1 byte
              0x5 : {'format' : '<q', 'length' : 8}}  # double 8 bytes

FRAME_TYPES = {0x1: {'name' : 'Data Frame',
                     'class' : DataFrame},
               0x2: {'name' : 'Command Frame',
                     'class' : CommandFrame},
               0x3: {'name' : 'Command Response Frame',
                     'class' : CommandFrame},
               0x4: {'name' : 'Message Frame',
                     'class' : MessageFrame},
               0x5: {'name' : 'Error Message Frame',
                     'class' : MessageFrame},
               0x6: {'name' : 'Routed Frame',
                     'class' : RoutedFrame},
               0x7: {'name' : 'Delayed Frame',
                     'class' : DelayedFrame},
               0x8: {'name' : 'Routed RSSI Frame',
                     'class' : RoutedRSSIFrame},
               0x9: {'name' : 'Timestamp Frame',
                     'class' : TimestampFrameSec},
               0xa: {'name' : 'Binary',
                     'class' : BinaryFrame},
               0xb: {'name' : 'Origin Frame',
                     'class' : OriginFrame},
               0xc: {'name' : 'Timestamp Frame',
                     'class' : TimestampFrame},
               0xd: {'name' : 'Routed Origin Frame',
                     'class' : RoutedOriginFrame},
               0xe: {'name' : 'Gateway Command',
                     'class' : CommandFrame},
               0xf: {'name' : 'Checksum Frame',
                     'class' : ChecksumFrame},
               0x10: {'name' : 'Delayed Second Frame',
                     'class' : DelayedSecondFrame}}

# swaps keys and values in FRAME_TYPES Dictionary
# FRAME_NAMES = {value['name']:key for key, value in FRAME_TYPES.iteritems()}
# for key, value in FRAME_NAMES.iteritems():
#     print key, value