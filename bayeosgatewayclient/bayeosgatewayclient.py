"""bayeosgatewayclient"""
import os, string, base64, re
from os import rename
from tempfile import gettempdir
from struct import pack, unpack
from socket import gethostname
from time import sleep, time
from glob import glob
from bayeosframe import BayEOSFrame
from abc import abstractmethod
from multiprocessing import Process
from threading import Thread
import sys
if sys.version_info> (2 , 8):
    from _thread import start_new_thread
    from configparser import ConfigParser
else:
    from thread import start_new_thread
    from ConfigParser import ConfigParser
   
from shutil import move
import argparse
import logging
import requests
import tempfile

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.WARNING)

DEFAULTS = {'path' : gettempdir(),
            'writer_sleep_time' : 5,
            'sender_sleep_time' : 5,
            'max_chunk' : 2500,
            'max_time' : 60,
            'value_type' : 0x41,
            'sender_sleep_time' : 5,
            'name' : '',
            'url' : '',
            'bayeosgateway_pw' : 'import',
            'bayeosgateway_user' : 'import',
            'absolute_time' : True,
            'remove' : True,
            'sleep_between_children' : 0,
            'backup_path' : None}

def bayeos_argparser(description = ''):
    """Parses command line arguments useful for this package.
    @param description: text to appear on the command line
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-n', '--name', default='BayEOS-Device',
                    help='name to appear in Gateway')
    parser.add_argument('-p', '--path', default=DEFAULTS['path'],
                    help='path to store writer files before they are sent')
    parser.add_argument('-m', '--max-chunk', default=DEFAULTS['max_chunk'],
                    help='maximal file size [bytes] before a new file is started')
    parser.add_argument('-ws', '--writer-sleep', default=DEFAULTS['writer_sleep_time'],
                    help='writer sleep time [seconds]')
    parser.add_argument('-ss', '--sender-sleep', default=DEFAULTS['sender_sleep_time'],
                    help='sender sleep time [seconds]')
    parser.add_argument('-pw', '--password', default=DEFAULTS['bayeosgateway_pw'],
                    help='password to access BayEOS Gateway')
    parser.add_argument('-un', '--user', default=DEFAULTS['bayeosgateway_user'],
                    help='user name to BayEOS Gateway')
    parser.add_argument('-u', '--url', default='',
                    help='URL to access BayEOS Gateway')

    return parser.parse_args()

def bayeos_confparser(config_file):
    """Reads a config file and returns a Python dictionary.
    @param config_file: path to the config file
    """
    config_parser = ConfigParser()
    config = {}
    try:
        config_parser.read(config_file)
        for section in config_parser.sections():
            for key, value in config_parser.items(section):
                try:
                    value = int(value)
                except:
                    None
                config[key] = value
    except ConfigParser.Error as e:
        print(str(e) + '. Config File not found or corrupt.')
    return config

class BayEOSWriter(object):
    """Writes BayEOSFrames to file."""
    
    def __init__(self, path=DEFAULTS['path'], max_chunk=DEFAULTS['max_chunk'],
                 max_time=DEFAULTS['max_time'],log_level=logging.INFO):
        """Constructor for a BayEOSWriter instance.
        @param path: path of queue directory
        @param max_chunk: maximum file size in Bytes, when reached a new file is started
        @param max_time: maximum time when a new file is started
        @param log_level: log level according to logging package
        """
        logging.getLogger().setLevel(log_level)
        self.path = os.path.abspath(path)
        self.max_chunk = max_chunk
        self.max_time = max_time
        if not os.path.isdir(self.path):
            try:
                os.makedirs(self.path, 0o700)
            except OSError as err:
                logging.critical('OSError: ' + str(err) + ' Could not create dir.')
                exit()
        files = glob(os.path.join(self.path,'*.act'))
        for each_file in files:
            try:
                rename(each_file, each_file.replace('.act', '.rd'))
            except OSError as err:
                logging.warning('OSError: ' + str(err))
        self.__start_new_file()

    def __save_frame(self, frame, timestamp=0):
        """Saves frames to file.
        @param frame: must be a valid BayEOS Frame as a binary coded String
        @param timestamp: Unix epoch time stamp, if zero system time is used
        """
        if not timestamp:
            timestamp = time()
        frame_length = len(frame)
        if self.file.tell() + frame_length + 10 > self.max_chunk or time() - self.current_timestamp > self.max_time:
            self.flush()
            
        self.file.write(pack('<d', timestamp) + pack('<h', frame_length) + frame)
        self.file.flush()
        logging.debug('Frame saved.')


    def __start_new_file(self):
        """Opens a new file with ending .act and determines current file name."""
        self.current_timestamp = time()
        [sec, usec] = str.split(str(self.current_timestamp), '.')        
        [fd, self.current_name] = tempfile.mkstemp('.act',sec + '-' + usec + '-',self.path)
        os.close(fd)
        self.file = open(self.current_name, 'wb')

    def save(self, values, value_type=0x41, offset=0, timestamp=0, origin=None, routed=False):
        """Generic frame saving method.
        @param values: list with [channel index, value] tuples or just values (..,..) or [..,..]
        @param value_type: defines Offset and Data Type
        @param offset: defines Channel Offset
        @param timestamp: Unix epoch time stamp, if zero system time is used
        @param origin: if defined, it is used as a name
        @param routed: only relevant with origin - if true, routed origin is created
        """
        data_frame = BayEOSFrame.factory(0x1)
        data_frame.create(values, value_type, offset)
        if not origin:
            self.__save_frame(data_frame.frame, timestamp)
        else:
            origin_frame = BayEOSFrame.factory(0xb)
            origin_frame.create(origin=origin, nested_frame=data_frame.frame)
            self.__save_frame(origin_frame.frame, timestamp)

    def save_msg(self, message, error=False, timestamp=0, origin=None, routed=False):
        """Saves Messages or Error Messages to Gateway.
        @param message: String to send
        @param error: when true, an Error Message is sent
        @param timestamp: Unix epoch time stamp, if zero system time is used
        @param origin: if defined, it is used as a name
        @param routed: only relevant with origin - if true, routed origin is created
        """
        if error:
            msg_frame = BayEOSFrame.factory(0x5)  # instantiate ErrorMessage Frame
        else:
            msg_frame = BayEOSFrame.factory(0x4)  # instantiate Message Frame
        msg_frame.create(message)
        if not origin:
            self.__save_frame(msg_frame.frame, timestamp)
        else:
            origin_frame = BayEOSFrame.factory(0xb)
            origin_frame.create(origin=origin, nested_frame=msg_frame.frame)
            self.__save_frame(origin_frame.frame, timestamp)
            
    def save_frame(self, frame, timestamp=0, origin=None, routed=False):
        """Saves a BayEOS Frame either as it is or wrapped in an Origin Frame."""
        if not origin:
            self.__save_frame(frame, timestamp); 
        else:
            if routed:
                origin_frame = BayEOSFrame.factory(0xd)
            else:   
                origin_frame = BayEOSFrame.factory(0xb)
            origin_frame.create(origin=origin, nested_frame=frame)
            self.__save_frame(origin_frame.frame, timestamp)

    def flush(self):
        """Close the current used file and renames it from .act to .rd.
        Starts a new file.
        """
        logging.info('Flushed writer.')
        self.file.close()
        try:
            p = (self.current_name+'$$__end_key__$$').replace('.act$$__end_key__$$','.rd')                 
            rename(self.current_name, p)
            logging.debug('File '+ p + ' ready for post')
        except OSError as err:
            logging.warning(str(err) + '. Could not find file: ' + self.current_name )
        self.__start_new_file()

class BayEOSSender(object):
    """Sends content of BayEOS writer files to Gateway."""
    def __init__(self, path=DEFAULTS['path'], 
                 name=DEFAULTS['name'], 
                 url=DEFAULTS['url'],
                 password=DEFAULTS['bayeosgateway_pw'],
                 user=DEFAULTS['bayeosgateway_user'],
                 absolute_time=DEFAULTS['absolute_time'],
                 remove=DEFAULTS['remove'],
                 backup_path=DEFAULTS['backup_path'],
                 log_level=logging.INFO):
        """Constructor for BayEOSSender instance.
        @param path: path where BayEOSWriter puts files
        @param name: sender name
        @param url: gateway url e.g. http://<gateway>/gateway/frame/saveFlat
        @param password: password on gateway
        @param user: user on gateway
        @param absolute_time: if set to false, relative time is used (delay)
        @param remove: if set to false files are kept as .bak file in the BayEOSWriter directory
        @param backup_path: path 
        @param log_level: log level according to logging package
        """
        if not password:
            exit('No gateway password was found.')
        self.path = os.path.abspath(path)
        self.name = name
        self.url = url
        self.password = password
        self.user = user
        self.absolute_time = absolute_time
        self.remove = remove
        logging.getLogger().setLevel(log_level)
        if backup_path and not os.path.isdir(backup_path):
            try:
                os.makedirs(backup_path, 0o700)
            except OSError as err:
                logging.warning('OSError: ' + str(err))
            backup_path=os.path.abspath(backup_path)
        self.backup_path = backup_path


    def send(self):
        """Keeps sending until all files are sent or an error occurs.
        @return number of posted frames as an integer
        """
        count_frames = 0
        try:
            count_frames += self.__send_files(self.path)
        except:
            logging.warning('Send error on __send_files(: ' + self.path + ')')
        if self.backup_path:
            try:
                count_frames += self.__send_files(self.backup_path)
            except:
                logging.warning('Send error on __send_files(: ' + self.backup_path + ')')
        return count_frames

    def __send_files(self, path):
        """Sends all files within one directory.
        @param path: path in file system
        @return number of frames in directory
        """
        try:
            files = glob(os.path.join(path,'*.rd'))
        except OSError as err:
            logging.warning('OSError: ' + str(err))
            return 0
        
        if len(files) == 0:
            return 0

        count_frames = 0
        i = 0
        while i < len(files):
            if(os.stat(files[i]).st_size==0):
                logging.warning('Empty file. Removing')
                os.remove(files[i])
                i += 1
                continue

            try:
                count = self.__post_file(files[i])
            except:
                logging.warning('Sender __send_file error on '+ files[i])
                count=0
            
            if count:
                i += 1
                count_frames += count
            else:
                break

        # on post error we did not run to the end
        # move files to backup_path
        if self.backup_path and path != self.backup_path:
            while i < len(files):        
                logging.debug('moving ' + files[i] + ' to backup_path')
                try:
                    move(files[i], files[i].replace(self.path,self.backup_path))
                except OSError as err:
                    logging.warning('OSError: ' + str(err))
                i += 1

        return count_frames
    
    def __post_file(self, file_name):
        """Reads one file and tries to send its content to the gateway.
        uses the requests library!!
        On success the file is deleted or renamed to *.bak ending.
        @return number of successfully posted frames in one file
        """
        current_file = open(file_name, 'rb')  # opens oldest file
        data={'sender': self.name}
        frames=[]
        timestamp = current_file.read(8)
        while timestamp:  # until end of file
            timestamp = unpack('<d', timestamp)[0]
            frame_length = unpack('<h', current_file.read(2))[0]
            frame = current_file.read(frame_length)
            if frame:
                if self.absolute_time:  # Timestamp Frame
                    # millisecond resolution from 1970-01-01
                    wrapper_frame = BayEOSFrame.factory(0xc)

                else:  # Delayed Frame
                    wrapper_frame = BayEOSFrame.factory(0x7)
                wrapper_frame.create(frame, timestamp)
                frames.append(base64.b64encode(wrapper_frame.frame))
            timestamp = current_file.read(8)
        current_file.close()
        backup_file_name = file_name.replace('.rd', '.bak')
        if self.backup_path:
            backup_file_name.replace(self.path, self.backup_path)
        if len(frames)==0:
            move(file_name, backup_file_name)
            logging.warning('No frames in file. Move to ' + backup_file_name)
            return 0
        
        data['bayeosframes[]']=frames
        headers={'user-agent': 'BayEOS-Python-Gateway-Client/0.3.9'}
        try:
            r=requests.post(self.url,data=data,auth=(self.user, self.password),headers=headers, timeout=10)
#            r.raise_for_status()
        except requests.exceptions.RequestException as e:  
            logging.warning('sender __post error:'+e)
            return 0
        
        if r.status_code==200: # all fine!
            if self.remove:
                os.remove(file_name)
            else:
                move(file_name, backup_file_name)
            return len(frames)
        
        logging.warning('sender __post error code: '+r.status_code)
        
        return 0
 
    def run(self, sleep_sec=DEFAULTS['sender_sleep_time']):
        """Tries to send frames within a certain interval.
        @param sleep_sec: specifies the sleep time
        """
        while True:
            try:
                res = self.send()
                if res > 0:
                    logging.info('Successfully sent ' + str(res) + ' frames.')
            except Exception as err:
                logging.warning('Exception:' + str(err) + '\n') 
            except:
                logging.warning('Unknown exception in run()\n')
            sleep(sleep_sec)
    
    def run_thread(self,sleep_sec=DEFAULTS['sender_sleep_time']):
        """Starts a run thread. When this thread terminates it starts a new run thread
        @param sleep_sec: specifies the sleep time
        """
        while True:
            t1 = Thread(target=self.run, args=(sleep_sec,))
            t1.start()
            t1.join()
            logging.warning('Sender run thread has terminated - starting new one\n')
        

    def start(self, sleep_sec=DEFAULTS['sender_sleep_time'], thread=True):
        """Starts a thread or a process to run the sender concurrently
        @param sleep_sec: specifies the sleep time
        """
        if thread:
            start_new_thread(self.run_thread, (sleep_sec,))
            logging.info('started sender thread')
        else:
            Process(target=self.run_thread, args=(sleep_sec,)).start()
            logging.info('started sender process')

class BayEOSGatewayClient(object):
    """Combines writer and sender for every device."""

    def __init__(self, names, options):
        """Creates an instance of BayEOSGatewayClient.
        @param names: list of device names e.g. 'Fifo.0', 'Fifo.1', ...
        The names are used to determine storage directories e.g. /tmp/Fifo.0.
        @param options: dictionary of options.
        """
        # check whether a valid list of device names is given
        if not isinstance(names, list):
            names = names.split(', ')
        if len(set(names)) < len(names):
            exit('Duplicate names detected.')
        if len(names) == 0:
            exit('No name given.')

        # if more than one device name is given, use sender name as prefix
        prefix = ''
        try:
            if isinstance(options['sender'], list):
                exit('Sender needs to be given as a String, not a list.')
                # options['sender'] = '_'.join(options['sender'])
            if len(names) > 1:
                prefix = options['sender'] + '/'
        except KeyError:
            prefix = gethostname() + '/'  # use host name if no sender specified

        options['sender'] = {}
        for each_name in names:
            options['sender'][each_name] = prefix + each_name

        # Set missing options on default values
        for each_default in DEFAULTS.items():
            try:
                options[each_default[0]]
            except KeyError:
                print('Option "' + each_default[0] + '" not set using default: ' + str(each_default[1]))
                options[each_default[0]] = each_default[1]

        self.names = names
        self.options = options

    def __init_folder(self, name):
        """Initializes folder to save data in.
        @param name: will be the folder name
        """
        path = os.path.join(self.__get_option('path'),re.sub('[-]+|[/]+|[\\\\]+|["]+|[\']+', '_', name))
        if not os.path.isdir(path):
            try:
                os.makedirs(path, 0o700)
            except OSError as err:
                exit('OSError: ' + str(err))
        return path

    def __get_option(self, key, default=''):
        """Helper function to get an option value.
        @param key: key in options dictionary
        @param default: default value to return if key is not specified
        @return value of the given option key or default value
        """
        try:
            self.options[key]
        except KeyError:
            return default
        if isinstance(self.options[key], dict):
            try:
                self.options[key][self.name]
            except AttributeError:
                return default
            except KeyError:
                return default
            return self.options[key][self.name]
        return self.options[key]

    def __start_writer(self, path):
        """Instantiates a BayEOSWriter object and starts an endless loop for data acquisition."""
        self.init_writer()
        self.writer = BayEOSWriter(path, self.__get_option('max_chunk'),
                                    self.__get_option('max_time'))
        print('Started writer for ' + self.name + ' with pid ' + str(os.getpid()))
        self.writer.save_msg('Started writer for ' + self.name)
        while True:
            data = self.read_data()
            if data:
                self.save_data(data)
            sleep(self.__get_option('writer_sleep_time'))

    def __start_sender(self, path):
        """Instantiates a BayEOSSender object and starts an endless loop for frame sending."""
        self.sender = BayEOSSender(path,
                                   self.__get_option('sender'),
                                   self.__get_option('url'),
                                   self.__get_option('bayeosgateway_password'),
                                   self.__get_option('bayeosgateway_user'),
                                   self.__get_option('absolute_time'),
                                   self.__get_option('remove'))
        print('Started sender for ' + self.name + ' with pid ' + str(os.getpid()))
        while True:
            self.sender.send()
            sleep(self.__get_option('sender_sleep_time'))

    def __start_sender_writer_pair(self, path, thread=True):
        """Creates a sender-writer pair.
        @param thread: if True sender runs in a thread
        """
        if thread:
            Thread(target=self.__start_sender, args=(path,)).start()
        else:
            Process(target=self.__start_sender, args=(path,)).start()
        self.__start_writer(path)

    def run(self, pair=True, thread=True):
        """Runs the BayEOSGatewayClient.
        Creates an own process for an instance of BayEOSWriter and BayEOSSender per device name.
        @param pair: if False writer and sender started in two processes, other parameters will be ignored
        @param thread: if True sender runs in a thread
        """
        print('Parent pid is ' + str(os.getpid()))
        for each_name in self.names:
            self.name = each_name  # will be forked and then overwritten
            path = self.__init_folder(each_name)
            if not pair:
                Process(target=self.__start_sender, args=(path,)).start()
                Process(target=self.__start_writer, args=(path,)).start()
            else:
                Process(target=self.__start_sender_writer_pair, args=(path, thread)).start()

    @abstractmethod
    def init_writer(self):
        """Method called by run(). Can be overwritten by implementation."""
        return

    @abstractmethod
    def read_data(self):
        """Method called by run(). Must be overwritten by implementation."""
        exit("No read data method found. Method has to be implemented.")

    def save_data(self, *args):
        """Method called by run().
        Can be overwritten by implementation (e.g. to store message frames).
        @param *args: list of arguments for writer's save methods
        """
        self.writer.save(args[0], self.__get_option('value_type'))
