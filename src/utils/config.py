"""
Configuration Management Module

This module provides utilities for loading and managing configuration settings
from environment variables, configuration files, and command-line arguments.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import copy

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 5432,
        'dbname': 'skype_archive',
        'user': 'postgres',
        'password': '',
    },
    'output': {
        'directory': 'output',
        'overwrite': False,
    },
    'logging': {
        'level': 'INFO',
        'file': None,
    },
    'message_types': {
        'Event/Call': '***A call started/ended***',
        'Poll': '***Created a poll***',
        'RichText/Media_Album': '***Sent an album of images***',
        'RichText/Media_AudioMsg': '***Sent a voice message***',
        'RichText/Media_CallRecording': '***Sent a call recording***',
        'RichText/Media_Card': '***Sent a media card***',
        'RichText/Media_FlikMsg': '***Sent a moji***',
        'RichText/Media_GenericFile': '***Sent a file***',
        'RichText/Media_Video': '***Sent a video message***',
        'RichText/UriObject': '***Sent a photo***',
        'RichText/ScheduledCallInvite': '***Scheduled a call***',
        'RichText/Location': '***Sent a location***',
        'RichText/Contacts': '***Sent a contact***',
    },
    'default_message_format': '***Sent a {message_type}***'
}

def load_config(config_file: Optional[str] = None, message_types_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables and optionally from JSON files.
    Environment variables take precedence over file configuration.

    Args:
        config_file (str, optional): Path to a JSON configuration file
        message_types_file (str, optional): Path to a JSON message types configuration file

    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    # Start with default configuration (deep copy to avoid modifying DEFAULT_CONFIG)
    config = copy.deepcopy(DEFAULT_CONFIG)

    # Load from main config file if provided
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Merge file config with defaults (deep merge)
                _deep_update(config, file_config)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Error loading configuration from {config_file}: {e}")

    # Load message types from separate file if provided
    if message_types_file and os.path.exists(message_types_file):
        try:
            with open(message_types_file, 'r', encoding='utf-8') as f:
                message_types_config = json.load(f)
                # Merge message types config with defaults
                if 'message_types' in message_types_config:
                    config['message_types'] = message_types_config['message_types']
                if 'default_message_format' in message_types_config:
                    config['default_message_format'] = message_types_config['default_message_format']
            logger.info(f"Loaded message types configuration from {message_types_file}")
        except Exception as e:
            logger.warning(f"Error loading message types configuration from {message_types_file}: {e}")

    # Override with environment variables
    # Database settings
    if os.getenv('POSTGRES_HOST'):
        config['database']['host'] = os.getenv('POSTGRES_HOST')
    if os.getenv('POSTGRES_PORT'):
        config['database']['port'] = int(os.getenv('POSTGRES_PORT'))
    if os.getenv('POSTGRES_DB'):
        config['database']['dbname'] = os.getenv('POSTGRES_DB')
    if os.getenv('POSTGRES_USER'):
        config['database']['user'] = os.getenv('POSTGRES_USER')
    if os.getenv('POSTGRES_PASSWORD'):
        config['database']['password'] = os.getenv('POSTGRES_PASSWORD')

    # Output settings
    if os.getenv('OUTPUT_DIR'):
        config['output']['directory'] = os.getenv('OUTPUT_DIR')
    if os.getenv('OUTPUT_OVERWRITE'):
        config['output']['overwrite'] = os.getenv('OUTPUT_OVERWRITE').lower() in ('true', 'yes', '1')

    # Logging settings
    if os.getenv('LOG_LEVEL'):
        config['logging']['level'] = os.getenv('LOG_LEVEL')
    if os.getenv('LOG_FILE'):
        config['logging']['file'] = os.getenv('LOG_FILE')

    return config

def get_db_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract database configuration from the main configuration.

    Args:
        config (Dict[str, Any]): Main configuration dictionary

    Returns:
        Dict[str, Any]: Database configuration dictionary
    """
    return {
        'host': config['database']['host'],
        'port': config['database']['port'],
        'dbname': config['database']['dbname'],
        'user': config['database']['user'],
        'password': config['database']['password'],
    }

def get_message_type_description(config: Dict[str, Any], msg_type: str) -> str:
    """
    Get the description for a message type from the configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary
        msg_type (str): Message type

    Returns:
        str: Description of the message type
    """
    if not msg_type:
        return "Unknown message type"

    message_types = config.get('message_types', {})
    default_format = config.get('default_message_format', '***Sent a {message_type}***')

    return message_types.get(msg_type, default_format.format(message_type=msg_type))

def setup_logging(config: Dict[str, Any]) -> None:
    """
    Set up logging based on configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary
    """
    log_level = getattr(logging, config['logging']['level'].upper(), logging.INFO)
    log_file = config['logging']['file']

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def _deep_update(target: Dict, source: Dict) -> None:
    """
    Deep update a nested dictionary with another dictionary.

    Args:
        target (Dict): Target dictionary to update
        source (Dict): Source dictionary with new values
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value