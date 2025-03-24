"""
Schema definitions for the MCP Code Indexer environment.

This module provides schema classes that were previously imported from modelscope_agent.
"""

class Message:
    """Message class for communication between components.
    
    This class represents a message that can be sent between different components
    in the environment.
    """
    
    def __init__(self, content="", send_to="all", sent_from="system"):
        """Initialize a new Message.
        
        Args:
            content (str): The content of the message.
            send_to (str): The recipient of the message.
            sent_from (str): The sender of the message.
        """
        self.content = content
        self.send_to = send_to
        self.sent_from = sent_from
        
    def __eq__(self, other):
        """Check if two messages are equal.
        
        Args:
            other: Another message to compare with.
            
        Returns:
            bool: True if the messages are equal, False otherwise.
        """
        if not isinstance(other, Message):
            return False
        return (self.content == other.content and 
                self.send_to == other.send_to and 
                self.sent_from == other.sent_from)
                
    def __repr__(self):
        """Get a string representation of the message.
        
        Returns:
            str: A string representation of the message.
        """
        return f"Message(content='{self.content}', send_to='{self.send_to}', sent_from='{self.sent_from}')"