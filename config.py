
_config = None
from json import load
from os.path import dirname, join
import logging

logging.basicConfig(level=logging.DEBUG)


project_path = dirname(dirname(__file__))
config_file_path = join(project_path, 'webagent-config.json')
def _loadConfig():
    global _config
    try:
        _config = load(open(config_file_path))    
    except OSError:        
        raise OSError('config.json not found in project root directory')



def get_config():
    global _config
    if not _config:
        _loadConfig()
    return _config


def set_waiting(waiting):
    global _config
    if waiting.get('timeout', None):
        _config["waiting"]['timeout'] = waiting['timeout']
    if waiting.get('sleep_time', None):
        _config["waiting"]['sleep_time'] = waiting['sleep_time']

