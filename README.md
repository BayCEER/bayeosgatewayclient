# bayeosgatewayclient
A Python package to transfer client (sensor) data to a [BayEOS Gateway](https://github.com/BayCEER/bayeos-gateway). All data is send as 
[BayEOS Frames](https://www.bayceer.uni-bayreuth.de/bayeos/frames) over HTTP.

![basic concept](https://github.com/kleebaum/bayeosgatewayclient/blob/master/writer-sender.png)

### Prerequisites
- Python 3 

## Installation
You can either use the setup.py script, the Python Package Index (PIP) or a Linux binary to install the package.

### Setup.py
Do the following steps to install the package via the setup.py script:
- git clone request ```git clone git://github.com/BayCEER/bayeosgatewayclient.git```
- find the right directory ```cd bayeosgatewayclient```
- run ```python setup.py install``` as root

### Linux Binary (for Debian)
- Login as root
- Install basic tools for installation  
  `apt-get update`  
  `apt-get install wget gnupg`
- Import the repository key  
  `wget -O - http://www.bayceer.uni-bayreuth.de/repos/apt/conf/bayceer_repo.gpg.key |apt-key add -`
- Add the BayCEER Debian repository  
  `echo "deb http://www.bayceer.uni-bayreuth.de/repos/apt/debian $(lsb_release -c -s) main" | tee /etc/apt/sources.list.d/bayceer.list`
- Update your repository cache  
  `apt-get update`
- Install the package  
  `apt-get install python3-bayeosgatewayclient`

Alternatively:
- run ```dpkg -i python3-bayeosgatewayclient_*_all.deb``` as root

## Example usage
```python
from time import sleep
from bayeosgatewayclient import BayEOSWriter, BayEOSSender
import tempfile
from os import path
import math 

NAME = 'SineWave'
URL = 'http://localhost:5533/gateway/frame/saveFlat'
USER= 'root'
PASSWORD = 'bayeos'
PATH = path.join(tempfile.gettempdir(),NAME)

# Create a writer thread 
writer = BayEOSWriter(PATH,max_time=5)
writer.save_msg('Writer was started.')

# Create a sender thread
sender = BayEOSSender(PATH, NAME, URL,user=USER,password=PASSWORD)
sender.start()

# Produce some values 
nr=0
angle = 0
while True:
    writer.save([nr,angle ,10*math.sin(angle)])    
    nr+=1
    angle+=0.1
    if angle > 360:
        angle = 0
    sleep(0.5)

```

More examples can be found in folder [samplescripts](bayeosgatewayclient/samplescripts)

## Useful Hints 
- Logging: You can adjust the log level of BayEOS Writer and Sender by using the log_level argument.

  


