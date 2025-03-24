"""
Logger for the MCP Code Indexer environment.

This module provides logging functionality that was previously imported from modelscope_agent.
"""

import logging
import sys

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger instance
agent_logger = logging.getLogger('mcp_code_indexer')

# Add methods to match the modelscope_agent logger interface
def info(msg, *args, **kwargs):
    """Log an info message.
    
    Args:
        msg: The message to log.
        *args: Additional arguments.
        **kwargs: Additional keyword arguments.
    """
    agent_logger.info(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    """Log an error message.
    
    Args:
        msg: The message to log.
        *args: Additional arguments.
        **kwargs: Additional keyword arguments.
    """
    agent_logger.error(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    """Log a warning message.
    
    Args:
        msg: The message to log.
        *args: Additional arguments.
        **kwargs: Additional keyword arguments.
    """
    agent_logger.warning(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    """Log a debug message.
    
    Args:
        msg: The message to log.
        *args: Additional arguments.
        **kwargs: Additional keyword arguments.
    """
    agent_logger.debug(msg, *args, **kwargs)

# Add the methods to the logger instance
agent_logger.info = info
agent_logger.error = error
agent_logger.warning = warning
agent_logger.debug = debug