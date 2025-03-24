"""
AstManager implementation.

This module provides a unified implementation of the AstManager class
that consolidates functionality from multiple implementations.
"""

import ast
import os
import pathlib
from collections import defaultdict

from mcp_code_indexer.environment.graph_database.graph_database import GraphDatabaseHandler

from .ast_utils import (get_dotted_name, get_module_name, get_py_files,
                        method_decorator, module_name_to_path)


class AstManager:
    """Manager for AST-based code analysis and graph database operations."""

    def __init__(self, project_path: str, task_id: str, graphDB: GraphDatabaseHandler):
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


class AstUpdateEdge:
    """Class for updating edges in the AST graph."""

    def __init__(self, project_path: str, task_id_old: str, task_id_new: str,
                 graphOld: GraphDatabaseHandler,
                 graphNew: GraphDatabaseHandler):
        """Initialize the AST update edge manager.
        
        Args:
            project_path (str): The path to the project.
            task_id_old (str): The old task ID.
            task_id_new (str): The new task ID.
            graphOld (GraphDatabaseHandler): The old graph database handler.
            graphNew (GraphDatabaseHandler): The new graph database handler.
        """
        self.project_path = project_path
        self.root_path = project_path
        self.task_id_old = task_id_old
        self.task_id_new = task_id_new

        self.graphOld = graphOld
        self.graphNew = graphNew

        self.ast_manage = AstManager(project_path, task_id_new, self.graphNew)
        self.class_inherited = defaultdict(list)
        self.set_C = set()
        self.edge_NC_to_C = set()

    def _get_all_node_in_file(self, file_full_path, batch_size: int = 500):
        """Get all nodes in a file.
        
        Args:
            file_full_path (str): The full path to the file.
            batch_size (int, optional): The batch size for processing. Defaults to 500.
            
        Returns:
            list: A list of full names of nodes in the file.
        """
        relative_path = os.path.relpath(file_full_path, self.root_path)
        all_methods = []
        offset = 0

        # Replace actual task ID
        task_id_new = self.task_id_new

        while True:
            query = f"""
MATCH (n:`{task_id_new}`)
WHERE exists(n.file_path) AND n.file_path = '{relative_path}'
RETURN n.full_name as full_name
SKIP {offset} LIMIT {batch_size}
            """
            response = self.graphNew.execute_query(query)
            if response:
                methods = [record['full_name'] for record in response]
                all_methods.extend(methods)
                if len(response) < batch_size:
                    break  # No more records to fetch
                offset += batch_size
            else:
                break

        return all_methods if all_methods else None

    def _get_node_to_target_in_old_graph(self, target_node_full_name):
        """Get nodes that point to a target node in the old graph.
        
        Args:
            target_node_full_name (str): The full name of the target node.
            
        Returns:
            list: A list of nodes that point to the target node.
        """
        query = f"""
MATCH (target_node:`{self.task_id_old}` {{full_name: '{target_node_full_name}'}})
MATCH (source_node:`{self.task_id_old}`)-[r]->(target_node)
WHERE exists(source_node.file_path)
RETURN source_node.full_name AS full_name, type(r) AS relationship_type
"""
        response = self.graphOld.execute_query(query)
        if response:
            nodes = [(record['full_name'], record['relationship_type'])
                     for record in response]
            return nodes
        else:
            return None

    def _get_old_edge_list(self,
                           node_list: list,
                           batch_size=500,
                           node_batch_size=80):
        """Get a list of edges from the old graph.
        
        Args:
            node_list (list): A list of nodes.
            batch_size (int, optional): The batch size for processing. Defaults to 500.
            node_batch_size (int, optional): The batch size for nodes. Defaults to 80.
            
        Returns:
            list: A list of edges from the old graph.
        """
        all_nodes = []

        # Replace actual task ID
        task_id_old = self.task_id_old
        task_id_new = self.task_id_new

        # Process node_list in batches
        for i in range(0, len(node_list), node_batch_size):
            batch_nodes = node_list[i:i + node_batch_size]
            offset = 0

            while True:
                query = f"""
UNWIND $batch_nodes AS node_full_name
MATCH (target_node:`{task_id_old}`)
WHERE exists(target_node.file_path) AND target_node.full_name = node_full_name
MATCH (source_node:`{task_id_old}`:`{task_id_new}`)-[r]->(target_node)
WHERE exists(source_node.file_path) AND source_node.file_path <> target_node.file_path
RETURN source_node.full_name AS source_node_full_name,
       target_node.full_name AS target_node_full_name,
       type(r) AS relationship_type
SKIP $offset LIMIT $batch_size
                """
                response = self.graphOld.execute_query(
                    query,
                    batch_nodes=batch_nodes,
                    offset=offset,
                    batch_size=batch_size,
                )
                if response:
                    nodes = [{
                        'source': record['source_node_full_name'],
                        'relationship_type': record['relationship_type'],
                        'target': record['target_node_full_name'],
                    } for record in response]
                    all_nodes.extend(nodes)
                    if len(response) < batch_size:
                        break
                    offset += batch_size
                else:
                    break

        return all_nodes if all_nodes else None

    def _build_edges_from_list(self,
                               relationships_list: list,
                               batch_size: int = 500):
        """Build edges from a list of relationships.
        
        Args:
            relationships_list (list): A list of relationships.
            batch_size (int, optional): The batch size for processing. Defaults to 500.
            
        Returns:
            list: A list of created edges.
        """
        # Classify relationships by type
        relationships_by_type = defaultdict(list)
        for edges in relationships_list:
            relationships_by_type[edges['relationship_type']].append({
                'source':
                edges['source'],
                'target':
                edges['target']
            })

        # Add inheritance relationships to class_inherited
        for relation in relationships_by_type['INHERITS']:
            self.class_inherited[relation['source']].append(relation['target'])

        # Create relationships in batches for each type
        results = []
        for relationship, relationships in relationships_by_type.items():
            offset = 0
            while offset < len(relationships):
                batch_relationships = relationships[offset:offset + batch_size]
                query = f"""
UNWIND $relationships AS rel
OPTIONAL MATCH (source_node:`{self.task_id_new}` {{full_name: rel.source}})
OPTIONAL MATCH (target_node:`{self.task_id_new}` {{full_name: rel.target}})
WHERE source_node IS NOT NULL AND target_node IS NOT NULL
MERGE (source_node)-[r:{relationship}]->(target_node)
RETURN source_node.full_name AS source_node_full_name,
       target_node.full_name AS target_node_full_name,
       type(r) AS relationship_type
            """
                response = self.graphOld.execute_query(
                    query, relationships=batch_relationships)
                if response:
                    nodes = [{
                        'source': record['source_node_full_name'],
                        'relationship_type': record['relationship_type'],
                        'target': record['target_node_full_name'],
                    } for record in response]
                    results.extend(nodes)

                offset += batch_size

        return results if results else None

    def _build_edge_old_to_new(self,
                               old_node_full_name,
                               new_node_full_name,
                               relation=''):
        """Build an edge from an old node to a new node.
        
        Args:
            old_node_full_name (str): The full name of the old node.
            new_node_full_name (str): The full name of the new node.
            relation (str, optional): The relationship type. Defaults to ''.
        """
        edge = self.graphNew.update_edge(
            start_name=old_node_full_name,
            relationship_type=relation,
            end_name=new_node_full_name,
        )
        if edge is not None and relation == 'INHERITS':
            if old_node_full_name not in self.class_inherited.keys():
                self.class_inherited[old_node_full_name] = []
            self.class_inherited[old_node_full_name].append(new_node_full_name)

    def build_new_node_to_old(self, change_files):
        """Build edges from new nodes to old nodes.
        
        Args:
            change_files (list): A list of changed files.
        """
        self.ast_manage.run(py_files=change_files)

    @method_decorator
    def build_old_node_to_new(self, change_files):
        """Build edges from old nodes to new nodes.
        
        Args:
            change_files (list): A list of changed files.
        """
        for file in change_files:
            # 1. Find all nodes C in [change_files]
            node_list = self._get_all_node_in_file(file)
            if node_list is None:
                continue
            # 2. Find all edges NC_i --> C_j in G_{old}
            old_edge_list = self._get_old_edge_list(node_list)
            if old_edge_list:
                self._build_edges_from_list(old_edge_list)

    def build_edge(self, change_files):
        """Build edges for changed files.
        
        Args:
            change_files (list): A list of changed files.
        """
        self.create_indexes()
        self.build_old_node_to_new(change_files)
        self.ast_manage.class_inherited.update(self.class_inherited)
        self.build_new_node_to_old(change_files)
        self.drop_indexes()

    def create_indexes(self):
        """Create indexes for the graph database."""
        task_id_old = self.task_id_old
        task_id_new = self.task_id_new

        # Create indexes for common queries
        index_queries = [
            f'CREATE INDEX ON :MODULE:`{task_id_new}`(full_name);',
            f'CREATE INDEX ON :`{task_id_new}`(name);',
            f'CREATE INDEX ON :CLASS:`{task_id_new}`(full_name);',
            f'CREATE INDEX ON :`{task_id_new}`(file_path);',
            f'CREATE INDEX ON :`{task_id_old}`(full_name);',
            f'CREATE INDEX ON :`{task_id_old}`(file_path);',
            f'CREATE INDEX ON :`{task_id_old}`:`{task_id_new}`(file_path);',
        ]

        for query in index_queries:
            try:
                self.graphNew.execute_query(query)
            except Exception as e:
                print(f"Error creating index with query '{query}': {str(e)}")

    def drop_indexes(self):
        """Drop indexes from the graph database."""
        task_id_old = self.task_id_old
        task_id_new = self.task_id_new

        # Drop indexes
        index_queries = [
            f'DROP INDEX ON :MODULE:`{task_id_new}`(full_name);',
            f'DROP INDEX ON :`{task_id_new}`(name);',
            f'DROP INDEX ON :CLASS:`{task_id_new}`(full_name);',
            f'DROP INDEX ON :`{task_id_new}`(file_path);',
            f'DROP INDEX ON :`{task_id_old}`(full_name);',
            f'DROP INDEX ON :`{task_id_old}`(file_path);',
            f'DROP INDEX ON :`{task_id_old}`:`{task_id_new}`(file_path);',
        ]

        for query in index_queries:
            try:
                self.graphNew.execute_query(query)
            except Exception as e:
                print(f"Error dropping index with query '{query}': {str(e)}")
