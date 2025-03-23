"""
ModelScope Agent Wrapper Module

This module provides a centralized interface for ModelScope Agent dependencies.
It allows for easier mocking and replacement of ModelScope components.
"""

try:
    # Import from modelscope_agent if available
    from modelscope_agent.constants import DEFAULT_SEND_TO, USER_REQUIREMENT
    from modelscope_agent.schemas import Message
    from modelscope_agent.utils.logger import agent_logger
    
    # Import environment components if they exist
    try:
        from modelscope_agent.environment.graph_database import GraphDatabaseHandler as MSGraphDatabaseHandler
        from modelscope_agent.environment.graph_database.ast_search import AstManager as MSAstManager
    except ImportError:
        # Create stub classes if not available
        class MSGraphDatabaseHandler:
            """Stub class for GraphDatabaseHandler"""
            def __init__(self, *args, **kwargs):
                raise NotImplementedError("ModelScope GraphDatabaseHandler not available")
        
        class MSAstManager:
            """Stub class for AstManager"""
            def __init__(self, *args, **kwargs):
                raise NotImplementedError("ModelScope AstManager not available")

except ImportError:
    # Create stub components if modelscope_agent is not available
    DEFAULT_SEND_TO = "all"
    USER_REQUIREMENT = "user_requirement"
    
    class Message:
        """Stub Message class"""
        def __init__(self, content="", send_to="all", sent_from="system"):
            self.content = content
            self.send_to = send_to
            self.sent_from = sent_from
    
    class agent_logger:
        """Stub logger class"""
        @staticmethod
        def info(msg, *args, **kwargs):
            pass
        
        @staticmethod
        def error(msg, *args, **kwargs):
            pass
        
        @staticmethod
        def warning(msg, *args, **kwargs):
            pass
        
        @staticmethod
        def debug(msg, *args, **kwargs):
            pass
    
    class MSGraphDatabaseHandler:
        """Stub class for GraphDatabaseHandler"""
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("ModelScope GraphDatabaseHandler not available")
    
    class MSAstManager:
        """Stub class for AstManager"""
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("ModelScope AstManager not available")

# Re-export components
__all__ = [
    "DEFAULT_SEND_TO",
    "USER_REQUIREMENT",
    "Message",
    "agent_logger",
    "MSGraphDatabaseHandler",
    "MSAstManager"
]