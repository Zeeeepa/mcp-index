"""
Workflow Module
Provides a workflow system for standardized component communication and process flows
"""

from typing import Dict, List, Any, Callable, Optional, Set, TypeVar, Generic, Union
import logging
import threading
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field

from .events import EventType, Event, publish, subscribe
from .di_container import resolve, resolve_all

logger = logging.getLogger(__name__)

# Generic type for workflow data
T = TypeVar('T')
R = TypeVar('R')

class WorkflowStatus(Enum):
    """Workflow status constants"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    """Workflow step status constants"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowContext(Generic[T]):
    """Workflow execution context"""
    workflow_id: str
    data: T
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StepContext(Generic[T]):
    """Workflow step execution context"""
    step_id: str
    workflow_context: WorkflowContext[T]
    status: StepStatus = StepStatus.PENDING
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkflowStep(Generic[T, R]):
    """Workflow step base class"""
    
    def __init__(self, step_id: str, name: str, description: str = None):
        """
        Initialize workflow step
        
        Args:
            step_id: Step ID
            name: Step name
            description: Step description
        """
        self.step_id = step_id
        self.name = name
        self.description = description or ""
        self.next_steps: List[WorkflowStep] = []
        self.error_steps: List[WorkflowStep] = []
        self.required_data: Set[str] = set()
    
    def execute(self, context: StepContext[T]) -> R:
        """
        Execute the step
        
        Args:
            context: Step execution context
            
        Returns:
            Step result
        """
        raise NotImplementedError("Subclasses must implement execute method")
    
    def can_execute(self, context: WorkflowContext[T]) -> bool:
        """
        Check if the step can be executed
        
        Args:
            context: Workflow execution context
            
        Returns:
            True if the step can be executed, False otherwise
        """
        # Check if all required data is available
        for data_key in self.required_data:
            if not hasattr(context.data, data_key):
                return False
        
        return True
    
    def on_success(self, step: 'WorkflowStep') -> 'WorkflowStep':
        """
        Add a step to execute on success
        
        Args:
            step: Next step to execute
            
        Returns:
            Self for chaining
        """
        self.next_steps.append(step)
        return self
    
    def on_error(self, step: 'WorkflowStep') -> 'WorkflowStep':
        """
        Add a step to execute on error
        
        Args:
            step: Step to execute on error
            
        Returns:
            Self for chaining
        """
        self.error_steps.append(step)
        return self
    
    def requires(self, *data_keys: str) -> 'WorkflowStep':
        """
        Specify required data keys
        
        Args:
            data_keys: Required data keys
            
        Returns:
            Self for chaining
        """
        self.required_data.update(data_keys)
        return self

class FunctionStep(WorkflowStep[T, R]):
    """Function-based workflow step"""
    
    def __init__(self, step_id: str, name: str, func: Callable[[StepContext[T]], R], description: str = None):
        """
        Initialize function step
        
        Args:
            step_id: Step ID
            name: Step name
            func: Function to execute
            description: Step description
        """
        super().__init__(step_id, name, description)
        self.func = func
    
    def execute(self, context: StepContext[T]) -> R:
        """
        Execute the function
        
        Args:
            context: Step execution context
            
        Returns:
            Function result
        """
        return self.func(context)

class ComponentStep(WorkflowStep[T, R]):
    """Component-based workflow step"""
    
    def __init__(self, step_id: str, name: str, component_type: type, method_name: str, description: str = None):
        """
        Initialize component step
        
        Args:
            step_id: Step ID
            name: Step name
            component_type: Component interface type
            method_name: Method name to call
            description: Step description
        """
        super().__init__(step_id, name, description)
        self.component_type = component_type
        self.method_name = method_name
    
    def execute(self, context: StepContext[T]) -> R:
        """
        Execute the component method
        
        Args:
            context: Step execution context
            
        Returns:
            Method result
        """
        # Resolve component
        component = resolve(self.component_type)
        if component is None:
            raise ValueError(f"Component of type {self.component_type.__name__} not found")
        
        # Get method
        method = getattr(component, self.method_name, None)
        if method is None or not callable(method):
            raise ValueError(f"Method {self.method_name} not found on component {self.component_type.__name__}")
        
        # Call method
        return method(context)

class ParallelStep(WorkflowStep[T, List[Any]]):
    """Parallel execution step"""
    
    def __init__(self, step_id: str, name: str, steps: List[WorkflowStep], description: str = None):
        """
        Initialize parallel step
        
        Args:
            step_id: Step ID
            name: Step name
            steps: Steps to execute in parallel
            description: Step description
        """
        super().__init__(step_id, name, description)
        self.steps = steps
    
    def execute(self, context: StepContext[T]) -> List[Any]:
        """
        Execute steps in parallel
        
        Args:
            context: Step execution context
            
        Returns:
            List of step results
        """
        # Create threads for each step
        threads = []
        results = [None] * len(self.steps)
        errors = [None] * len(self.steps)
        
        def execute_step(index: int, step: WorkflowStep, step_context: StepContext):
            try:
                results[index] = step.execute(step_context)
            except Exception as e:
                errors[index] = str(e)
        
        # Start threads
        for i, step in enumerate(self.steps):
            # Create step context
            step_context = StepContext(
                step_id=step.step_id,
                workflow_context=context.workflow_context,
                status=StepStatus.PENDING,
                start_time=time.time()
            )
            
            # Create and start thread
            thread = threading.Thread(
                target=execute_step,
                args=(i, step, step_context)
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check for errors
        for i, error in enumerate(errors):
            if error is not None:
                raise RuntimeError(f"Error in parallel step {self.steps[i].name}: {error}")
        
        return results

class ConditionalStep(WorkflowStep[T, Any]):
    """Conditional execution step"""
    
    def __init__(self, step_id: str, name: str, 
                condition: Callable[[StepContext[T]], bool], 
                true_step: WorkflowStep, 
                false_step: Optional[WorkflowStep] = None,
                description: str = None):
        """
        Initialize conditional step
        
        Args:
            step_id: Step ID
            name: Step name
            condition: Condition function
            true_step: Step to execute if condition is true
            false_step: Step to execute if condition is false
            description: Step description
        """
        super().__init__(step_id, name, description)
        self.condition = condition
        self.true_step = true_step
        self.false_step = false_step
    
    def execute(self, context: StepContext[T]) -> Any:
        """
        Execute conditional step
        
        Args:
            context: Step execution context
            
        Returns:
            Step result
        """
        # Evaluate condition
        if self.condition(context):
            # Execute true step
            return self.true_step.execute(context)
        elif self.false_step is not None:
            # Execute false step
            return self.false_step.execute(context)
        
        # No step to execute
        return None

class Workflow(Generic[T, R]):
    """Workflow class"""
    
    def __init__(self, workflow_id: str, name: str, description: str = None):
        """
        Initialize workflow
        
        Args:
            workflow_id: Workflow ID
            name: Workflow name
            description: Workflow description
        """
        self.workflow_id = workflow_id
        self.name = name
        self.description = description or ""
        self.start_step: Optional[WorkflowStep] = None
        self.steps: Dict[str, WorkflowStep] = {}
        self.on_complete_callbacks: List[Callable[[WorkflowContext[T]], None]] = []
        self.on_error_callbacks: List[Callable[[WorkflowContext[T], Exception], None]] = []
    
    def set_start_step(self, step: WorkflowStep) -> 'Workflow':
        """
        Set the starting step
        
        Args:
            step: Starting step
            
        Returns:
            Self for chaining
        """
        self.start_step = step
        self.add_step(step)
        return self
    
    def add_step(self, step: WorkflowStep) -> 'Workflow':
        """
        Add a step to the workflow
        
        Args:
            step: Workflow step
            
        Returns:
            Self for chaining
        """
        self.steps[step.step_id] = step
        return self
    
    def on_complete(self, callback: Callable[[WorkflowContext[T]], None]) -> 'Workflow':
        """
        Add a completion callback
        
        Args:
            callback: Callback function
            
        Returns:
            Self for chaining
        """
        self.on_complete_callbacks.append(callback)
        return self
    
    def on_error(self, callback: Callable[[WorkflowContext[T], Exception], None]) -> 'Workflow':
        """
        Add an error callback
        
        Args:
            callback: Callback function
            
        Returns:
            Self for chaining
        """
        self.on_error_callbacks.append(callback)
        return self
    
    def execute(self, data: T) -> R:
        """
        Execute the workflow
        
        Args:
            data: Workflow data
            
        Returns:
            Workflow result
        """
        if self.start_step is None:
            raise ValueError("No start step defined for workflow")
        
        # Create workflow context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            data=data,
            status=WorkflowStatus.PENDING,
            start_time=time.time()
        )
        
        try:
            # Set workflow status
            context.status = WorkflowStatus.RUNNING
            
            # Publish workflow started event
            publish(Event(
                EventType.COMPONENT_INITIALIZED,  # Reusing existing event type
                {
                    "workflow_id": context.workflow_id,
                    "workflow_name": self.name,
                    "status": context.status.value
                },
                "workflow"
            ))
            
            # Execute workflow
            result = self._execute_step(self.start_step, context)
            
            # Set workflow status
            context.status = WorkflowStatus.COMPLETED
            context.end_time = time.time()
            
            # Publish workflow completed event
            publish(Event(
                EventType.COMPONENT_INITIALIZED,  # Reusing existing event type
                {
                    "workflow_id": context.workflow_id,
                    "workflow_name": self.name,
                    "status": context.status.value,
                    "duration": context.end_time - context.start_time
                },
                "workflow"
            ))
            
            # Call completion callbacks
            for callback in self.on_complete_callbacks:
                try:
                    callback(context)
                except Exception as e:
                    logger.error(f"Error in workflow completion callback: {str(e)}")
            
            return result
        except Exception as e:
            # Set workflow status
            context.status = WorkflowStatus.FAILED
            context.error = str(e)
            context.end_time = time.time()
            
            # Publish workflow failed event
            publish(Event(
                EventType.COMPONENT_ERROR,
                {
                    "workflow_id": context.workflow_id,
                    "workflow_name": self.name,
                    "status": context.status.value,
                    "error": context.error,
                    "duration": context.end_time - context.start_time
                },
                "workflow"
            ))
            
            # Call error callbacks
            for callback in self.on_error_callbacks:
                try:
                    callback(context, e)
                except Exception as callback_error:
                    logger.error(f"Error in workflow error callback: {str(callback_error)}")
            
            # Re-raise exception
            raise
    
    def execute_async(self, data: T, callback: Optional[Callable[[Union[R, Exception]], None]] = None) -> str:
        """
        Execute the workflow asynchronously
        
        Args:
            data: Workflow data
            callback: Optional callback function
            
        Returns:
            Workflow ID
        """
        # Create workflow context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            data=data,
            status=WorkflowStatus.PENDING
        )
        
        # Define thread function
        def execute_thread():
            try:
                result = self.execute(data)
                if callback is not None:
                    callback(result)
            except Exception as e:
                if callback is not None:
                    callback(e)
        
        # Start thread
        thread = threading.Thread(target=execute_thread)
        thread.daemon = True
        thread.start()
        
        return context.workflow_id
    
    def _execute_step(self, step: WorkflowStep, context: WorkflowContext[T]) -> Any:
        """
        Execute a workflow step
        
        Args:
            step: Workflow step
            context: Workflow context
            
        Returns:
            Step result
        """
        # Check if step can be executed
        if not step.can_execute(context):
            raise ValueError(f"Step {step.name} cannot be executed: missing required data")
        
        # Create step context
        step_context = StepContext(
            step_id=step.step_id,
            workflow_context=context,
            status=StepStatus.PENDING,
            start_time=time.time()
        )
        
        # Update workflow context
        context.current_step = step.step_id
        
        # Publish step started event
        publish(Event(
            EventType.COMPONENT_INITIALIZED,  # Reusing existing event type
            {
                "workflow_id": context.workflow_id,
                "workflow_name": self.name,
                "step_id": step.step_id,
                "step_name": step.name,
                "status": StepStatus.RUNNING.value
            },
            "workflow"
        ))
        
        try:
            # Set step status
            step_context.status = StepStatus.RUNNING
            
            # Execute step
            result = step.execute(step_context)
            
            # Set step status
            step_context.status = StepStatus.COMPLETED
            step_context.end_time = time.time()
            step_context.result = result
            
            # Store step result
            context.step_results[step.step_id] = result
            
            # Publish step completed event
            publish(Event(
                EventType.COMPONENT_INITIALIZED,  # Reusing existing event type
                {
                    "workflow_id": context.workflow_id,
                    "workflow_name": self.name,
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "status": step_context.status.value,
                    "duration": step_context.end_time - step_context.start_time
                },
                "workflow"
            ))
            
            # Execute next steps
            if step.next_steps:
                last_result = None
                for next_step in step.next_steps:
                    last_result = self._execute_step(next_step, context)
                return last_result
            
            return result
        except Exception as e:
            # Set step status
            step_context.status = StepStatus.FAILED
            step_context.error = str(e)
            step_context.end_time = time.time()
            
            # Publish step failed event
            publish(Event(
                EventType.COMPONENT_ERROR,
                {
                    "workflow_id": context.workflow_id,
                    "workflow_name": self.name,
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "status": step_context.status.value,
                    "error": step_context.error,
                    "duration": step_context.end_time - step_context.start_time
                },
                "workflow"
            ))
            
            # Execute error steps
            if step.error_steps:
                last_result = None
                for error_step in step.error_steps:
                    try:
                        last_result = self._execute_step(error_step, context)
                    except Exception as error_step_error:
                        logger.error(f"Error in error step {error_step.name}: {str(error_step_error)}")
                return last_result
            
            # Re-raise exception
            raise

class WorkflowRegistry:
    """Workflow registry for managing workflows"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WorkflowRegistry, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the registry"""
        if self._initialized:
            return
            
        self._workflows: Dict[str, Workflow] = {}
        self._initialized = True
        logger.info("Workflow registry initialized")
    
    def register_workflow(self, workflow: Workflow) -> None:
        """
        Register a workflow
        
        Args:
            workflow: Workflow to register
        """
        self._workflows[workflow.workflow_id] = workflow
        logger.debug(f"Registered workflow {workflow.name} ({workflow.workflow_id})")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a workflow by ID
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow or None if not found
        """
        return self._workflows.get(workflow_id)
    
    def get_all_workflows(self) -> List[Workflow]:
        """
        Get all registered workflows
        
        Returns:
            List of workflows
        """
        return list(self._workflows.values())

# Convenience functions for working with the workflow registry
def register_workflow(workflow: Workflow) -> None:
    """
    Register a workflow
    
    Args:
        workflow: Workflow to register
    """
    WorkflowRegistry().register_workflow(workflow)

def get_workflow(workflow_id: str) -> Optional[Workflow]:
    """
    Get a workflow by ID
    
    Args:
        workflow_id: Workflow ID
        
    Returns:
        Workflow or None if not found
    """
    return WorkflowRegistry().get_workflow(workflow_id)

def get_all_workflows() -> List[Workflow]:
    """
    Get all registered workflows
    
    Returns:
        List of workflows
    """
    return WorkflowRegistry().get_all_workflows()