"""
Internal implementation of the AstManager.

This module provides an internal implementation of the AstManager class
that was previously imported from modelscope_agent.
"""

import ast
import os
import pathlib
from collections import defaultdict

from .ast_utils import (get_dotted_name, get_module_name, get_py_files,
                        method_decorator, module_name_to_path)


class AstManager:
    """Manager for AST-based code analysis and graph database operations."""

    def __init__(self, project_path: str, task_id: str, graphDB):
        """Initialize the AST manager.
        
        Args:
            project_path (str): The path to the project.
            task_id (str): The ID of the task.
            graphDB: The graph database handler.
        """
        self.project_path = project_path
        self.root_path = project_path
        self.graphDB = graphDB
        self.task_id = task_id
        self.class_inherited = {}
        self.processed_relations = set()  # Track processed relationships
        self.visited = []

    def get_full_name_from_graph(self, module_full_name, target_name):
        """Get the full name of a node from the graph.
        
        Args:
            module_full_name (str): The full name of the module.
            target_name (str): The target name to look for.
            
        Returns:
            tuple: A tuple containing the full name and label of the node.
        """
        query = (
            f"MATCH (m:MODULE:`{self.task_id}` {{full_name: '{module_full_name}'}})"
            f'-[:CONTAINS]->(c:`{self.task_id}` '
            f"{{name: '{target_name}'}}) "
            'RETURN c.full_name as full_name, labels(c) AS labels')
        response = self.graphDB.execute_query(query)
        if response:
            full_name, labels = response[0]['full_name'], response[0]['labels']
            label = next(lbl for lbl in labels if lbl in [
                'MODULE', 'CLASS', 'FUNCTION', 'METHOD', 'GLOBAL_VARIABLE',
                'FIELD'
            ])
            return full_name, label
        else:
            return None, None

    def get_all_name_from_graph(self, module_full_name):
        """Get all names from a module in the graph.
        
        Args:
            module_full_name (str): The full name of the module.
            
        Returns:
            list: A list of full names and labels.
        """
        query = f"""
MATCH (m:MODULE:`{self.task_id}` {{full_name: '{module_full_name}'}})-[:CONTAINS]->(c:`{self.task_id}`)
RETURN c.full_name as full_name, labels(c) AS labels
"""

        def get_type_label(labels):
            type_label = next(lbl for lbl in labels if lbl in [
                'MODULE', 'CLASS', 'FUNCTION', 'METHOD', 'GLOBAL_VARIABLE',
                'FIELD'
            ])
            return type_label

        response = self.graphDB.execute_query(query)

        if response:
            return [[record['full_name'],
                     get_type_label(record['labels'])] for record in response]
        else:
            return None

    def get_all_edge_of_class(self, class_full_name):
        """Get all edges of a class.
        
        Args:
            class_full_name (str): The full name of the class.
            
        Returns:
            list: A list of edges.
        """
        query = f"""
MATCH (c:CLASS:`{self.task_id}` {{full_name: '{class_full_name}'}})-[r:HAS_METHOD|HAS_FIELD]->(m:`{self.task_id}`)
RETURN m.full_name as full_name, m.name as name, type(r) as relationship_type
"""
        response = self.graphDB.execute_query(query)
        if response:
            methods = [(record['full_name'], record['name'],
                        record['relationship_type']) for record in response]
            return methods
        else:
            return None

    def check_exist_edge_of_class(self, class_full_name, node_name):
        """Check if an edge exists for a class.
        
        Args:
            class_full_name (str): The full name of the class.
            node_name (str): The name of the node.
            
        Returns:
            list: A list of full names.
        """
        query = (
            f"MATCH (c:CLASS:`{self.task_id}` {{full_name: '{class_full_name}'}}) "
            f"-[r:HAS_METHOD|HAS_FIELD]->(m:`{self.task_id}` {{name: '{node_name}'}}) "
            'RETURN m.full_name as full_name')
        response = self.graphDB.execute_query(query)
        if response:
            methods = [record['full_name'] for record in response]
            return methods
        else:
            return None

    def run(self, py_files=None):
        """Run the AST manager.
        
        Args:
            py_files (list, optional): A list of Python files to process. Defaults to None.
        """
        self._run(py_files)

    @method_decorator
    def _run(self, py_files=None):
        """Internal implementation of run.
        
        Args:
            py_files (list, optional): A list of Python files to process. Defaults to None.
        """
        if py_files is None:
            py_files = get_py_files(self.project_path)

        for py_file in py_files:
            self.build_modules_contain(py_file)

        for py_file in py_files:
            self.build_inherited(py_file)

        for cur_class_full_name in self.class_inherited.keys():
            for base_class_full_name in self.class_inherited[
                    cur_class_full_name]:
                self._build_inherited_method(cur_class_full_name,
                                             base_class_full_name)

    def _build_inherited_method(self, cur_class_full_name,
                                base_class_full_name):
        """Build inherited methods.
        
        Args:
            cur_class_full_name (str): The full name of the current class.
            base_class_full_name (str): The full name of the base class.
        """
        # Create a unique identifier for the relationship
        relation_key = (cur_class_full_name, base_class_full_name)
        # If this relationship has already been processed, return
        if relation_key in self.processed_relations:
            return
        # Mark the current relationship as processed
        self.processed_relations.add(relation_key)

        methods = self.get_all_edge_of_class(base_class_full_name)
        if methods is None:
            return
        for node_full_name, name, type in methods:
            # Check for overrides
            if not self.check_exist_edge_of_class(cur_class_full_name, name):
                self.graphDB.update_edge(
                    start_name=cur_class_full_name,
                    relationship_type=type,
                    end_name=node_full_name,
                )

        if base_class_full_name in self.class_inherited.keys():
            for base_base_class_full_name in self.class_inherited[
                    base_class_full_name]:
                self._build_inherited_method(cur_class_full_name,
                                             base_base_class_full_name)

    def _build_modules_contain_edge(self, target_module_full_name, target_name,
                                    cur_module_full_name):
        """Build module containment edges.
        
        Args:
            target_module_full_name (str): The full name of the target module.
            target_name (str): The name of the target.
            cur_module_full_name (str): The full name of the current module.
            
        Returns:
            bool: True if the edge was created, False otherwise.
        """
        target_full_name, target_label = self.get_full_name_from_graph(
            target_module_full_name, target_name)
        if not target_full_name:
            return False

        edge = self.graphDB.add_edge(
            start_label='MODULE',
            start_name=cur_module_full_name,
            relationship_type='CONTAINS',
            end_name=target_full_name,
            params={'association_type': target_label},
        )
        return edge is not None

    def _build_modules_contain_edge_all(self, target_module_full_name,
                                        cur_module_full_name):
        """Build all module containment edges.
        
        Args:
            target_module_full_name (str): The full name of the target module.
            cur_module_full_name (str): The full name of the current module.
            
        Returns:
            bool: True if all edges were created, False otherwise.
        """
        target_list = self.get_all_name_from_graph(target_module_full_name)

        if not target_list:
            return False

        for target_full_name, target_label in target_list:
            edge = self.graphDB.add_edge(
                start_label='MODULE',
                start_name=cur_module_full_name,
                relationship_type='CONTAINS',
                end_name=target_full_name,
                params={'association_type': target_label},
            )
            if not edge:
                return False

        return True

    def build_modules_contain(self, file_full_path):
        """Build module containment relationships.
        
        Args:
            file_full_path (str): The full path to the file.
            
        Returns:
            None: If the file has already been visited or cannot be parsed.
        """
        if file_full_path in self.visited:
            return None
        self.visited.append(file_full_path)

        try:
            file_content = pathlib.Path(file_full_path).read_text()
            tree = ast.parse(file_content)
        except Exception:
            # Failed to read/parse one file, we should ignore it
            return None

        if '__init__.py' in file_full_path:
            cur_module_full_name = get_dotted_name(
                self.root_path, os.path.dirname(file_full_path))
        else:
            cur_module_full_name = get_dotted_name(self.root_path,
                                                   file_full_path)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            target_module_full_name = get_module_name(file_full_path, node,
                                                      self.root_path)
            if not target_module_full_name:
                continue

            for target in node.names:
                target_name = target.name

                if target_name == '*':
                    if not self._build_modules_contain_edge_all(
                            target_module_full_name, cur_module_full_name):
                        module_path = module_name_to_path(
                            target_module_full_name, self.root_path)
                        file_path = os.path.join(self.root_path, module_path,
                                                 '__init__.py')
                        if os.path.exists(file_path):
                            self.build_modules_contain(file_path)
                    self._build_modules_contain_edge_all(
                        target_module_full_name, cur_module_full_name)
                else:
                    if not self._build_modules_contain_edge(
                            target_module_full_name, target_name,
                            cur_module_full_name):
                        module_path = module_name_to_path(
                            target_module_full_name, self.root_path)
                        file_path = os.path.join(self.root_path, module_path,
                                                 '__init__.py')
                        if os.path.exists(file_path):
                            self.build_modules_contain(file_path)
                    self._build_modules_contain_edge(target_module_full_name,
                                                     target_name,
                                                     cur_module_full_name)

    def build_inherited(self, file_full_path):
        """Build inheritance relationships.
        
        Args:
            file_full_path (str): The full path to the file.
            
        Returns:
            None: If the file cannot be parsed.
        """
        try:
            file_content = pathlib.Path(file_full_path).read_text()
            tree = ast.parse(file_content)
        except Exception:
            # Failed to read/parse one file, we should ignore it
            return None

        if '__init__.py' in file_full_path:
            cur_module_full_name = get_dotted_name(
                self.root_path, os.path.dirname(file_full_path))
        else:
            cur_module_full_name = get_dotted_name(self.root_path,
                                                   file_full_path)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            class_name = node.name
            cur_class_full_name = cur_module_full_name + '.' + class_name
            for base in node.bases:
                if not isinstance(base, ast.Name):
                    continue
                base_class_full_name, _ = self.get_full_name_from_graph(
                    cur_module_full_name, base.id)
                if base_class_full_name is None:
                    pass
                if cur_class_full_name not in self.class_inherited.keys():
                    self.class_inherited[cur_class_full_name] = []
                self.class_inherited[cur_class_full_name].append(
                    base_class_full_name)
                if base_class_full_name:
                    self.graphDB.update_edge(
                        start_name=cur_class_full_name,
                        relationship_type='INHERITS',
                        end_name=base_class_full_name,
                    )