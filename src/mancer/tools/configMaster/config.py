from pathlib import Path
import yaml
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerConfig:
    ip: str
    username: str
    password: str
    sudo_password: str
    apps_dir: str = '/apps'

@dataclass
class AppConfig:
    debug: bool
    server: ServerConfig
    cache_dir: Path = Path('_cache_/serwery')
    
def load_config(config_file: str = 'config.yaml') -> AppConfig:
    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)
        
        # Mapowanie pola user na username
        server_config = data['server']
        if 'user' in server_config:
            server_config['username'] = server_config.pop('user')
            
        return AppConfig(
            debug=data.get('debug', False),
            server=ServerConfig(**server_config)
        ) 