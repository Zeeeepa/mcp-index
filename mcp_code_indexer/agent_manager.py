"""
Agent Manager Module
Manages a multi-agent system for code analysis using the Environment
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import re
import threading
import time

from .environment.environment import Environment
from .config import Config
from .indexer import CodeIndexer
from .search_engine import SearchEngine
from .utils.json_utils import convert_sets_to_lists
from .external.modelscope import Message

logger = logging.getLogger(__name__)

class Agent:
    """Base Agent class for code analysis"""
    
    def __init__(self, role: str, environment: Environment):
        """
        Initialize Agent
        
        Args:
            role: Agent role name
            environment: Environment instance
            
        Returns:
            None
        """
        self.role = role
        self.environment = environment
    
    def process_messages(self, messages: List[Message]) -> Optional[Message]:
        """
        Process incoming messages
        
        Args:
            messages: List of messages to process
            
        Returns:
            Response message or None
        """
        raise NotImplementedError("Subclasses must implement process_messages")


class CodeAnalyzerAgent(Agent):
    """Agent for analyzing code structure"""
    
    def __init__(self, environment: Environment, indexer: CodeIndexer):
        """
        Initialize Code Analyzer Agent
        
        Args:
            environment: Environment instance
            indexer: Code indexer instance
            
        Returns:
            None
        """
        super().__init__("code_analyzer", environment)
        self.indexer = indexer
    
    def process_messages(self, messages: List[Message]) -> Optional[Message]:
        """
        Process incoming messages
        
        Args:
            messages: List of messages to process
            
        Returns:
            Response message or None
        """
        for message in messages:
            content = message.content
            
            # Check if this is a code analysis request
            if "analyze_file" in content:
                try:
                    # Extract file path from message
                    file_path_match = re.search(r"analyze_file:\s*([^\s]+)", content)
                    if file_path_match:
                        file_path = file_path_match.group(1)
                        
                        # Analyze code structure
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code_content = f.read()
                        
                        # Use the optimizer's analyzer to analyze code
                        language = os.path.splitext(file_path)[1][1:]
                        analysis = self.indexer.optimizer.analyzer.analyze_code(code_content, language)
                        
                        # Create response message
                        response_content = f"Code analysis for {file_path}:\n"
                        response_content += f"- Functions: {len(analysis['functions'])}\n"
                        response_content += f"- Classes: {len(analysis['classes'])}\n"
                        response_content += f"- Imports: {len(analysis['imports'])}\n"
                        
                        # Add function details
                        if analysis['functions']:
                            response_content += "\nFunctions:\n"
                            for func in analysis['functions']:
                                response_content += f"- {func['name']} (lines {func['start_line']}-{func['end_line']})\n"
                        
                        # Add class details
                        if analysis['classes']:
                            response_content += "\nClasses:\n"
                            for cls in analysis['classes']:
                                response_content += f"- {cls['name']} (lines {cls['start_line']}-{cls['end_line']})\n"
                        
                        return Message(
                            content=response_content,
                            send_to="all",
                            sent_from=self.role
                        )
                except Exception as e:
                    return Message(
                        content=f"Error analyzing code: {str(e)}",
                        send_to="all",
                        sent_from=self.role
                    )
        
        return None


class SearchAgent(Agent):
    """Agent for searching code"""
    
    def __init__(self, environment: Environment, search_engine: SearchEngine):
        """
        Initialize Search Agent
        
        Args:
            environment: Environment instance
            search_engine: Search engine instance
            
        Returns:
            None
        """
        super().__init__("search_agent", environment)
        self.search_engine = search_engine
    
    def process_messages(self, messages: List[Message]) -> Optional[Message]:
        """
        Process incoming messages
        
        Args:
            messages: List of messages to process
            
        Returns:
            Response message or None
        """
        for message in messages:
            content = message.content
            
            # Check if this is a search request
            if "search:" in content:
                try:
                    # Extract query from message
                    query_match = re.search(r"search:\s*(.+)", content)
                    if query_match:
                        query = query_match.group(1)
                        
                        # Search code
                        results = self.search_engine.search(query, limit=5)
                        
                        # Create response message
                        if not results:
                            return Message(
                                content=f"No results found for query: {query}",
                                send_to="all",
                                sent_from=self.role
                            )
                        
                        response_content = f"Search results for '{query}':\n\n"
                        
                        for i, result in enumerate(results, 1):
                            file_path = result.get("file_path", "")
                            language = result.get("language", "text")
                            start_line = result.get("start_line", 1)
                            end_line = result.get("end_line", 1)
                            content = result.get("content", "")
                            
                            response_content += f"{i}. {os.path.basename(file_path)} (lines {start_line}-{end_line})\n"
                            response_content += f"   File: {file_path}\n"
                            response_content += f"   ```{language}\n   {content}\n   ```\n\n"
                        
                        return Message(
                            content=response_content,
                            send_to="all",
                            sent_from=self.role
                        )
                except Exception as e:
                    return Message(
                        content=f"Error searching code: {str(e)}",
                        send_to="all",
                        sent_from=self.role
                    )
        
        return None


class QualityAnalyzerAgent(Agent):
    """Agent for analyzing code quality"""
    
    def __init__(self, environment: Environment, indexer: CodeIndexer):
        """
        Initialize Quality Analyzer Agent
        
        Args:
            environment: Environment instance
            indexer: Code indexer instance
            
        Returns:
            None
        """
        super().__init__("quality_analyzer", environment)
        self.indexer = indexer
    
    def process_messages(self, messages: List[Message]) -> Optional[Message]:
        """
        Process incoming messages
        
        Args:
            messages: List of messages to process
            
        Returns:
            Response message or None
        """
        for message in messages:
            content = message.content
            
            # Check if this is a quality analysis request
            if "analyze_quality:" in content:
                try:
                    # Extract file path from message
                    file_path_match = re.search(r"analyze_quality:\s*([^\s]+)", content)
                    if file_path_match:
                        file_path = file_path_match.group(1)
                        
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code_content = f.read()
                        
                        # Analyze code quality
                        language = os.path.splitext(file_path)[1][1:]
                        quality_metrics = self.indexer.optimizer.analyze_code_quality(
                            code_content, file_path, language
                        )
                        
                        # Create response message
                        response_content = f"Code quality analysis for {file_path}:\n\n"
                        
                        for category, metrics in quality_metrics.items():
                            response_content += f"## {category.capitalize()}\n"
                            for metric, value in metrics.items():
                                response_content += f"- {metric}: {value}\n"
                            response_content += "\n"
                        
                        return Message(
                            content=response_content,
                            send_to="all",
                            sent_from=self.role
                        )
                except Exception as e:
                    return Message(
                        content=f"Error analyzing code quality: {str(e)}",
                        send_to="all",
                        sent_from=self.role
                    )
        
        return None


class DependencyAnalyzerAgent(Agent):
    """Agent for analyzing code dependencies"""
    
    def __init__(self, environment: Environment, indexer: CodeIndexer):
        """
        Initialize Dependency Analyzer Agent
        
        Args:
            environment: Environment instance
            indexer: Code indexer instance
            
        Returns:
            None
        """
        super().__init__("dependency_analyzer", environment)
        self.indexer = indexer
    
    def process_messages(self, messages: List[Message]) -> Optional[Message]:
        """
        Process incoming messages
        
        Args:
            messages: List of messages to process
            
        Returns:
            Response message or None
        """
        for message in messages:
            content = message.content
            
            # Check if this is a dependency analysis request
            if "analyze_dependencies:" in content:
                try:
                    # Extract project path from message
                    path_match = re.search(r"analyze_dependencies:\s*([^\s]+)", content)
                    if path_match:
                        project_path = path_match.group(1)
                        
                        # Analyze dependencies
                        dependencies = self.indexer.optimizer.analyze_project_dependencies(project_path)
                        
                        # Convert sets to lists for JSON serialization
                        serializable_dependencies = convert_sets_to_lists(dependencies)
                        
                        # Create response message
                        response_content = f"Dependency analysis for {project_path}:\n\n"
                        response_content += json.dumps(serializable_dependencies, indent=2)
                        
                        return Message(
                            content=response_content,
                            send_to="all",
                            sent_from=self.role
                        )
                except Exception as e:
                    return Message(
                        content=f"Error analyzing dependencies: {str(e)}",
                        send_to="all",
                        sent_from=self.role
                    )
        
        return None


class AgentManager:
    """
    Agent Manager class
    
    Manages a multi-agent system for code analysis using the Environment
    """
    
    def __init__(self, config: Config, indexer: CodeIndexer, search_engine: SearchEngine):
        """
        Initialize Agent Manager
        
        Args:
            config: Configuration object
            indexer: Code indexer
            search_engine: Search engine
            
        Returns:
            None
        """
        self.config = config
        self.indexer = indexer
        self.search_engine = search_engine
        
        # Initialize environment with roles
        self.roles = ["code_analyzer", "search_agent", "quality_analyzer", "dependency_analyzer"]
        self.environment = Environment(roles=self.roles)
        
        # Initialize agents
        self.agents = {
            "code_analyzer": CodeAnalyzerAgent(self.environment, self.indexer),
            "search_agent": SearchAgent(self.environment, self.search_engine),
            "quality_analyzer": QualityAnalyzerAgent(self.environment, self.indexer),
            "dependency_analyzer": DependencyAnalyzerAgent(self.environment, self.indexer)
        }
        
        # Start agent processing threads
        self._start_agent_threads()
    
    def _start_agent_threads(self) -> None:
        """Start agent processing threads"""
        for role, agent in self.agents.items():
            thread = threading.Thread(
                target=self._agent_loop,
                args=(agent,),
                daemon=True
            )
            thread.start()
    
    def _agent_loop(self, agent: Agent) -> None:
        """
        Agent processing loop
        
        Args:
            agent: Agent instance
            
        Returns:
            None
        """
        while True:
            try:
                # Extract messages for this agent
                messages = self.environment.extract_message_by_role(agent.role)
                
                if messages:
                    # Process messages
                    response = agent.process_messages(messages)
                    
                    # Store response in environment
                    if response:
                        self.environment.store_message_from_role(agent.role, response)
                
                # Sleep to avoid busy waiting
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in agent loop for {agent.role}: {str(e)}")
    
    def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """
        Perform multi-agent code analysis
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Analysis results
        """
        # Reset environment
        self.environment.reset_env_queues()
        
        # Create analysis request messages
        code_analysis_request = Message(
            content=f"analyze_file: {file_path}",
            send_to="code_analyzer",
            sent_from="user"
        )
        
        quality_analysis_request = Message(
            content=f"analyze_quality: {file_path}",
            send_to="quality_analyzer",
            sent_from="user"
        )
        
        # Store messages in environment
        self.environment.store_message_from_role("user", code_analysis_request)
        self.environment.store_message_from_role("user", quality_analysis_request)
        
        # Wait for responses
        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        
        results = {}
        
        while time.time() - start_time < timeout:
            # Check if all agents have responded
            history = self.environment.extract_all_history_message()
            
            # Extract responses from history
            code_analysis_response = None
            quality_analysis_response = None
            
            for message in history:
                if message.sent_from == "code_analyzer":
                    code_analysis_response = message.content
                elif message.sent_from == "quality_analyzer":
                    quality_analysis_response = message.content
            
            # If all responses received, break
            if code_analysis_response and quality_analysis_response:
                results = {
                    "code_analysis": code_analysis_response,
                    "quality_analysis": quality_analysis_response
                }
                break
            
            # Sleep before checking again
            time.sleep(0.5)
        
        # If timeout reached, return partial results
        if not results:
            results = {
                "error": "Analysis timeout",
                "partial_results": {}
            }
            
            # Include any partial results
            history = self.environment.extract_all_history_message()
            for message in history:
                if message.sent_from == "code_analyzer":
                    results["partial_results"]["code_analysis"] = message.content
                elif message.sent_from == "quality_analyzer":
                    results["partial_results"]["quality_analysis"] = message.content
        
        return results
    
    def analyze_project_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze project dependencies
        
        Args:
            project_path: Path to the project
            
        Returns:
            Dependency analysis results
        """
        # Reset environment
        self.environment.reset_env_queues()
        
        # Create dependency analysis request
        dependency_request = Message(
            content=f"analyze_dependencies: {project_path}",
            send_to="dependency_analyzer",
            sent_from="user"
        )
        
        # Store message in environment
        self.environment.store_message_from_role("user", dependency_request)
        
        # Wait for response
        start_time = time.time()
        timeout = 60  # 60 seconds timeout
        
        results = {}
        
        while time.time() - start_time < timeout:
            # Check if agent has responded
            history = self.environment.extract_all_history_message()
            
            # Extract response from history
            for message in history:
                if message.sent_from == "dependency_analyzer":
                    results = {
                        "dependency_analysis": message.content
                    }
                    break
            
            # If response received, break
            if results:
                break
            
            # Sleep before checking again
            time.sleep(0.5)
        
        # If timeout reached, return error
        if not results:
            results = {
                "error": "Dependency analysis timeout"
            }
        
        return results
    
    def search_code(self, query: str) -> Dict[str, Any]:
        """
        Search code using search agent
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        # Reset environment
        self.environment.reset_env_queues()
        
        # Create search request
        search_request = Message(
            content=f"search: {query}",
            send_to="search_agent",
            sent_from="user"
        )
        
        # Store message in environment
        self.environment.store_message_from_role("user", search_request)
        
        # Wait for response
        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        
        results = {}
        
        while time.time() - start_time < timeout:
            # Check if agent has responded
            history = self.environment.extract_all_history_message()
            
            # Extract response from history
            for message in history:
                if message.sent_from == "search_agent":
                    results = {
                        "search_results": message.content
                    }
                    break
            
            # If response received, break
            if results:
                break
            
            # Sleep before checking again
            time.sleep(0.5)
        
        # If timeout reached, return error
        if not results:
            results = {
                "error": "Search timeout"
            }
        
        return results