"""Reads BayEOS options from a config file."""

from bayeosgatewayclient import BayEOSWriter, BayEOSSender, bayeos_confparser

config = bayeos_confparser('config')
print(config)

writer = BayEOSWriter(path=config['path'], max_chunk=config['max_chunk'])
sender = BayEOSSender(path=config['path'])