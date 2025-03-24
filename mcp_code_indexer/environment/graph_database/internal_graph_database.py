"""
Internal implementation of the GraphDatabaseHandler.

This module provides an internal implementation of the GraphDatabaseHandler class
that was previously imported from modelscope_agent.
"""

import concurrent.futures

import fasteners
from py2neo import Graph, Node, NodeMatcher, Relationship, RelationshipMatcher

REMOVE_LABEL_QUERY_TEMPLATE = """
MATCH (n:`{label}`)
WHERE size(labels(n)) > 1
WITH n LIMIT {limit}
REMOVE n:`{label}`
RETURN count(n) AS removed_count
"""

DELETE_NODE_QUERY_TEMPLATE = """
MATCH (n:`{label}`)
WHERE size(labels(n)) = 1
WITH n LIMIT {limit}
DETACH DELETE n
RETURN count(n) AS deleted_count
"""


class NoOpLock:
    """A no-operation lock that does nothing."""

    def __enter__(self):
        """Enter the context manager."""
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass


class FileLock:
    """A file-based lock for inter-process synchronization."""

    def __init__(self, lockfile):
        """Initialize the file lock.
        
        Args:
            lockfile (str): The path to the lock file.
        """
        self.lockfile = lockfile
        self.lock = fasteners.InterProcessLock(self.lockfile)
        self.lock_acquired = False

    def __enter__(self):
        """Enter the context manager and acquire the lock."""
        self.lock_acquired = self.lock.acquire(blocking=True)
        if not self.lock_acquired:
            raise RuntimeError('Unable to acquire the lock')

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and release the lock."""
        if self.lock_acquired:
            self.lock.release()
            self.lock_acquired = False


class GraphDatabaseHandler:
    """Handler for interacting with a Neo4j graph database."""

    def __init__(
        self,
        uri,
        user,
        password,
        database_name='neo4j',
        task_id='',
        use_lock=False,
        lockfile='neo4j.lock',
    ):
        """Initialize the graph database handler.
        
        Args:
            uri (str): The URI of the Neo4j database.
            user (str): The username for authentication.
            password (str): The password for authentication.
            database_name (str, optional): The name of the database. Defaults to 'neo4j'.
            task_id (str, optional): The ID of the task. Defaults to ''.
            use_lock (bool, optional): Whether to use a lock for thread safety. Defaults to False.
            lockfile (str, optional): The path to the lock file. Defaults to 'neo4j.lock'.
        """
        self.graph = self._connect_to_graph(uri, user, password, database_name)
        self.node_matcher = NodeMatcher(self.graph)
        self.rel_matcher = RelationshipMatcher(self.graph)
        self.none_label = 'none'
        self.task_id = task_id
        self.lock = FileLock(lockfile) if use_lock else NoOpLock()

    def _connect_to_graph(self, uri, user, password, database_name):
        """Connect to the Neo4j graph database.
        
        Args:
            uri (str): The URI of the Neo4j database.
            user (str): The username for authentication.
            password (str): The password for authentication.
            database_name (str): The name of the database.
            
        Returns:
            Graph: The connected graph object.
            
        Raises:
            ConnectionError: If the connection fails.
        """
        try:
            return Graph(uri, auth=(user, password), name=database_name)
        except Exception as e:
            raise ConnectionError(
                'Failed to connect to Neo4j at {} after attempting to start the service.'
                .format(uri)) from e

    def _match_node(self, full_name):
        """Match a node by its full name.
        
        Args:
            full_name (str): The full name of the node.
            
        Returns:
            Node: The matched node, or None if no match is found.
        """
        if self.task_id:
            existing_node = self.node_matcher.match(
                self.task_id, full_name=full_name).first()
        else:
            existing_node = self.node_matcher.match(
                full_name=full_name).first()
        return existing_node

    def _create_node(self, label=None, full_name='', parms={}):
        """Create a new node.
        
        Args:
            label (str, optional): The label of the node. Defaults to None.
            full_name (str, optional): The full name of the node. Defaults to ''.
            parms (dict, optional): Additional parameters for the node. Defaults to {}.
            
        Returns:
            Node: The created node.
        """
        if label is None or label == '':
            label = self.none_label
        if self.task_id:
            node = Node(self.task_id, label, full_name=full_name, **parms)
        else:
            node = Node(label, full_name=full_name, **parms)
        self.graph.create(node)
        return node

    def _update_node_label(self, full_name, label):
        """Update the label of a node.
        
        Args:
            full_name (str): The full name of the node.
            label (str): The new label for the node.
            
        Returns:
            bool: True if the node was updated, False otherwise.
        """
        existing_node = self._match_node(full_name)
        if existing_node:
            query = ('MATCH (n:{0}:`{1}` {{full_name: $full_name}}) '
                     'REMOVE n:{0} '
                     'SET n:{2}').format(self.none_label, self.task_id, label)
            self.graph.run(query, full_name=full_name)
            return True
        return False

    def _add_node_label(self, full_name, new_label):
        """Add a label to a node.
        
        Args:
            full_name (str): The full name of the node.
            new_label (str): The label to add to the node.
            
        Returns:
            bool: True if the label was added, False otherwise.
        """
        existing_node = self._match_node(full_name)
        if existing_node:
            query = ('MATCH (n:`{0}` {{full_name: $full_name}}) '
                     'SET n:{1}').format(self.task_id, new_label)
            self.graph.run(query, full_name=full_name)
            return True
        return False

    def clear_task_data(self, task_id, batch_size=500):
        """Remove a specific label from nodes in batches.
        
        If a node only has this one label, delete the node.
        
        Args:
            task_id (str): The task ID to clear.
            batch_size (int, optional): The batch size for processing. Defaults to 500.
        """
        with self.lock:
            while True:
                remove_label_query = REMOVE_LABEL_QUERY_TEMPLATE.format(
                    label=task_id, limit=batch_size)
                remove_label_result = self.graph.run(remove_label_query).data()
                removed_count = remove_label_result[0]['removed_count']

                delete_node_query = DELETE_NODE_QUERY_TEMPLATE.format(
                    label=task_id, limit=batch_size)
                delete_node_result = self.graph.run(delete_node_query).data()
                deleted_count = delete_node_result[0]['deleted_count']

                if removed_count == 0 and deleted_count == 0:
                    break

    def clear_database(self):
        """Clear the entire database."""
        with self.lock:
            self.graph.run('MATCH (n) DETACH DELETE n')

    def execute_query(self, query, **params):
        """Execute a Cypher query.
        
        Args:
            query (str): The Cypher query to execute.
            **params: Additional parameters for the query.
            
        Returns:
            list: The result of the query, or an empty string if an error occurs.
        """
        try:
            with self.lock:
                result = self.graph.run(query, **params)
                return [record for record in result]
        except Exception:
            return ''

    def execute_query_with_exception(self, query, **params):
        """Execute a Cypher query and handle exceptions.
        
        Args:
            query (str): The Cypher query to execute.
            **params: Additional parameters for the query.
            
        Returns:
            tuple: A tuple containing the result of the query and a success flag.
        """
        try:
            with self.lock:
                result = self.graph.run(query, **params)
                return [record for record in result], True
        except Exception as e:
            return str(e), False

    def execute_query_with_timeout(self, cypher, timeout=60):
        """Execute a Cypher query with a timeout.
        
        Args:
            cypher (str): The Cypher query to execute.
            timeout (int, optional): The timeout in seconds. Defaults to 60.
            
        Returns:
            tuple: A tuple containing the result of the query and a success flag.
        """
        def query_execution():
            return self.execute_query_with_exception(cypher)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(query_execution)
            try:
                cypher_response, flag = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                cypher_response = 'cypher too complex, out of memory'
                flag = True
            except Exception as e:
                cypher_response = str(e)
                flag = False

        return cypher_response, flag

    def update_node(self, full_name, parms={}):
        """Update a node's parameters.
        
        Args:
            full_name (str): The full name of the node.
            parms (dict, optional): The parameters to update. Defaults to {}.
        """
        with self.lock:
            existing_node = self._match_node(full_name)
            if existing_node:
                existing_node.update(parms)
                self.graph.push(existing_node)

    def add_node(self, label, full_name, parms={}):
        """Add a node to the graph.
        
        Args:
            label (str): The label of the node.
            full_name (str): The full name of the node.
            parms (dict, optional): Additional parameters for the node. Defaults to {}.
            
        Returns:
            Node: The added node.
        """
        with self.lock:
            existing_node = self._match_node(full_name)
            if existing_node:
                if self.none_label in list(existing_node.labels):
                    self._update_node_label(full_name, label)
                elif label not in list(existing_node.labels):
                    self._add_node_label(full_name, label)
                existing_node.update(parms)
                self.graph.push(existing_node)
            else:
                existing_node = self._create_node(
                    label, full_name, parms=parms)
            return existing_node

    def add_edge(
        self,
        start_label=None,
        start_name='',
        relationship_type='',
        end_label=None,
        end_name='',
        params={},
    ):
        """Add an edge to the graph.
        
        Args:
            start_label (str, optional): The label of the start node. Defaults to None.
            start_name (str, optional): The name of the start node. Defaults to ''.
            relationship_type (str, optional): The type of the relationship. Defaults to ''.
            end_label (str, optional): The label of the end node. Defaults to None.
            end_name (str, optional): The name of the end node. Defaults to ''.
            params (dict, optional): Additional parameters for the edge. Defaults to {}.
            
        Returns:
            Relationship: The added edge, or None if the edge could not be added.
        """
        with self.lock:
            start_node = self._match_node(full_name=start_name)
            end_node = self._match_node(full_name=end_name)

            if not start_node:
                start_node = self._create_node(
                    start_label, full_name=start_name, parms=params)
            if not end_node:
                end_node = self._create_node(
                    end_label, full_name=end_name, parms=params)

            if start_node and end_node:
                rel = self.rel_matcher.match((start_node, end_node),
                                             relationship_type).first()
                if rel:
                    rel.update(params)
                    self.graph.push(rel)
                    return rel
                else:
                    rel = Relationship(start_node, relationship_type, end_node,
                                       **params)
                    self.graph.create(rel)
                    return rel
            return None

    def update_edge(self,
                    start_name='',
                    relationship_type='',
                    end_name='',
                    params={}):
        """Update an edge in the graph.
        
        Args:
            start_name (str, optional): The name of the start node. Defaults to ''.
            relationship_type (str, optional): The type of the relationship. Defaults to ''.
            end_name (str, optional): The name of the end node. Defaults to ''.
            params (dict, optional): Additional parameters for the edge. Defaults to {}.
            
        Returns:
            Relationship: The updated edge, or None if the edge could not be updated.
        """
        with self.lock:
            start_node = self._match_node(full_name=start_name)
            end_node = self._match_node(full_name=end_name)
            if start_node and end_node:
                rel = self.rel_matcher.match((start_node, end_node),
                                             relationship_type).first()
                if rel:
                    rel.update(params)
                    self.graph.push(rel)
                    return rel
                else:
                    rel = Relationship(start_node, relationship_type, end_node,
                                       **params)
                    self.graph.create(rel)
                    return rel
            return None

    def update_file_path(self, root_path):
        """Update the file paths in the database.
        
        Args:
            root_path (str): The root path to use for updating.
        """
        with self.lock:
            # Get all nodes with a file_path attribute
            query = (
                'MATCH (n:`{0}`) '
                'WHERE exists(n.file_path)'
                'RETURN n.file_path as file_path, n.full_name as full_name'
            ).format(self.task_id)

            nodes_with_file_path = self.execute_query(query)
            # Update each node's file_path
            for node in nodes_with_file_path:
                full_name = node['full_name']
                file_path = node['file_path']
                if file_path.startswith(root_path):
                    file_path = file_path[len(root_path):]
                    self.update_node(
                        full_name=full_name, parms={'file_path': file_path})