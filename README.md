# bayeosgatewayclient
A Python package to transfer client (sensor) data to a BayEOS Gateway.

![basic concept](https://github.com/kleebaum/bayeosgatewayclient/blob/master/writer-sender.png)

## Installation
You can either use the setup.py script, the Python Package Index (PIP) or a Linux binary to install the package.

### Setup.py
Do the following steps to install the package via the setup.py script:
- git clone request ```git clone git://github.com/BayCEER/bayeosgatewayclient.git```
- find the right directory ```cd bayeosgatewayclient```
- run ```python setup.py install``` as root

### Linux Binary (for Debian)
- add the following repositories to /etc/apt/sources.list ```deb http://www.bayceer.uni-bayreuth.de/repos/apt/debian stretch main```
- install key ```wget -O - http://www.bayceer.uni-bayreuth.de/repos/apt/conf/bayceer_repo.gpg.key | apt-key add -```
- ```apt-get update```
- ```apt-get install python-bayeosgatewayclient```

Alternatively:
- run ```dpkg -i python-bayeosgatewayclient_*_all.deb``` as root

## Example usage
Import the package ```import bayeosgatewayclient```.

### Writer
A simple writer looks like this:
```
from time import sleep
from bayeosgatewayclient import BayEOSWriter

writer = BayEOSWriter('/tmp/bayeos-device1/')
writer.save_msg('BayEOS Writer was started.')

while True:
    print 'adding frame\n'
    writer.save([2.1, 3, 20.5])
    sleep(1)
```

A BayEOSWriter constructor takes the following arguments:
```
PATH = '/tmp/bayeos-device1/'	# directory to store .act and .rd files
MAX_CHUNK = 2000				# file size in bytes
MAX_TIME = 60					# time when a new file is started in seconds
writer = BayEOSWriter(path=PATH, max_chunk=MAX_CHUNK, max_time=MAX_TIME)
```

The following methods could also be of interest:
- save integer values: ```writer.save(values=[1,2,3], value_type=0x22)```
- save with channel indices: ```writer.save([[1,2.1], [2,3], [3,20.5]], value_type=0x41)``` or
  ```writer.save({1: 2.1, 2: 3, 3: 20.5}, value_type=0x41)```
- save with channel offset: ```writer.save([2.1, 3, 20.5], value_type=0x02, offset=2)```
- save origin: ```writer.save([2.1, 3, 20.5], origin='Writer-Example')```
- save error message: ```writer.save_msg('error message', error=True)```
- close current .act file and start a new one: ```writer.flush()```

### Sender
A simple sender looks like this:
```
from time import sleep
from bayeosgatewayclient import BayEOSSender

sender = BayEOSSender('/tmp/bayeos-device1/', 
					  'Test-Device', 
					  'http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveFlat')

while True:
    res = sender.send()
    if res > 0:
        print 'Successfully sent ' + str(res) + ' frames.'
    sleep(5)
```

A BayEOSSender constructor takes the following arguments:
```
PATH = '/tmp/bayeos-device1/'	# directory to look for .rd files
NAME = 'Test-Device'
URL = 'http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveFlat'
USER = 'import'					# user name to access the BayEOS Gateway
PASSWORD = 'import'				# password to access the BayEOS Gateway
BACKUP_PATH = '/home/.../' 		# backup path to store file if a) sending does not work 
								  or b) sending was successful but files but files 
								  shall be kept (renamed from .rd to .bak extension)

sender = BayEOSSender(path=PATH, 
					  name=NAME, 
					  url=URL, 
					  password=PASSWORD,
					  user=USER,
					  absolute_time=True, # if true writer, else sender time is used
					  remove=True,		  # .rd files deleted after successfully sent
					  backup_path=BACKUP_PATH)
```

The following methods could also be of interest:
- substitute the loop: ```sender.run(sleep_sec=5)```
- start sender as a separate thread ```sender.start(sleep_sec=5)```
- start sender as a separate process ```sender.start(sleep_sec=5, thread=False)```

### Connect writer and sender
Usually, the writer and sender are operating concurrently, although they are not
linked directly, i. e., they only share the same directory. 

A simple script to connect one writer-sender pair looks like this:
```
from bayeosgatewayclient import BayEOSWriter, BayEOSSender

PATH = '/tmp/bayeos-device/'
NAME = 'Writer-Sender-Example'
URL = 'http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveFlat'

writer = BayEOSWriter(PATH)
writer.save_msg('Writer was started.')

sender = BayEOSSender(PATH, NAME, URL)
sender.start() 	# sender runs in a concurrent thread

while True:
    print 'adding frame'
    writer.save([2.1, 3, 20.5])
    sleep(5)
```

Another way to combine writer-sender pairs is using the BayEOSGatewayClient class:
```
from bayeosgatewayclient import BayEOSGatewayClient

OPTIONS = {'bayeosgateway_url' : 'http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveFlat',
           'bayeosgateway_password' : 'import',
           'bayeosgateway_user' : 'import'}

NAMES = ['PythonTestDevice1', 'PythonTestDevice2', 'PythonTestDevice3']

class PythonTestDevice(BayEOSGatewayClient):
    """Creates both a writer and sender instance for every NAME in NAMES. Implements BayEOSGatewayClient."""
    def read_data(self):
    	"""Must be overwritten."""
        if self.name == 'PythonTestDevice1':
            return (2.1, 3, 20.5)
        else:
            return (42)
        
    def save_data(self, data=0, origin=''):
    	"""Can be overwritten."""
        if self.name == 'PythonTestDevice1':
            self.writer.save(data, origin='origin')
            self.writer.save_msg('Overwritten method.')
        elif self.name == 'PythonTestDevice2':
            self.writer.save(data)

client = PythonTestDevice(NAMES, OPTIONS)

client.run()
```

### Parsing command line arguments
Constructor arguments can be passed as command line arguments:

long option 	| short option	| description
----------------|---------------|-------------------------
−−name			|-n				|name to appear in Gateway
−−path			|-p				|path to store writer files before they are sent
−−max-chunk		|-m				|maximal file size [bytes] before a new file is started
−−writer-sleep	|-ws			|writer sleep time [seconds]
−−sender-sleep	|-ss			|sender sleep time [seconds]
−−password		|-pw			|password to access BayEOS Gateway
−−user			|-un			|user name to BayEOS Gateway
−−url 			|-u				|URL to access BayEOS Gateway

```
from bayeosgatewayclient import BayEOSWriter, bayeos_argparser
args = bayeos_argparser('This text appears on the command line.')

WRITER_SLEEP = float(args.writer_sleep)
MAX_CHUNK = float(args.max_chunk)
writer = BayEOSWriter(max_chunk=MAX_CHUNK)

while True:
    writer.save([42, 20.5], value_type=0x21)
    sleep(WRITER_SLEEP)
```

That is what could appear on the command line:
```python2.7 example_script.py -m 2560 -ws 5```

### Parsing config files
First, a config file has to be created, e.g.:
```
; Sample Config file for bayeosgatewayclient

[Overall]
name = Test-Device
path = /tmp/bayeos-device

[Writer]
max_time = 100
max_chunk = 2000
writer_sleep_time = 1

[Sender]
sender_sleep_time = 10
url = http://bayconf.bayceer.uni-bayreuth.de/gateway/frame/saveMatrix
bayeosgateway_user = import
bayeosgateway_pw = import
absolute_time = True
remove = False
backup_path = /home/pi/backup/
```

Second, the Python script needs to invoke the ```bayeos_confparser(config_file)``` method.

```
from bayeosgatewayclient import BayEOSWriter, BayEOSSender, bayeos_confparser
config = bayeos_confparser('config')

writer = BayEOSWriter(config['path'], config['max_chunk'])
sender = BayEOSSender(config['path'])
```
