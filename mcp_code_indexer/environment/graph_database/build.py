import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from mcp_code_indexer.environment.graph_database.graph_database import GraphDatabaseHandler
from mcp_code_indexer.environment.graph_database.ast_search.ast_manage import AstManager


def get_py_files(directory):
    py_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files


def run_single(path, root, task_id, shallow, env_path_dict=None):

    env_path = env_path_dict['env_path']
    script_path = os.path.join(env_path_dict['working_directory'],
                               'run_index_single.py')
    working_directory = env_path_dict['working_directory']
    url = env_path_dict['url']
    user = env_path_dict['user']
    password = env_path_dict['password']
    db_name = env_path_dict['db_name']

    if shallow:
        script_args = [
            '--file_path',
            path,
            '--root_path',
            root,
            '--task_id',
            task_id,
            '--url',
            url,
            '--user',
            user,
            '--password',
            password,
            '--db_name',
            db_name,
            '--env',
            env_path,
            '--shallow',
        ]
    else:
        script_args = [
            '--file_path', path, '--root_path', root, '--task_id', task_id
        ]
    return run_script_in_env(env_path, script_path, working_directory,
                             script_args)


def run_script_in_env(env_path,
                      script_path,
                      working_directory,
                      script_args=None):
    if not os.path.exists(env_path):
        raise FileNotFoundError(
            'Python executable not found in the environment: {}'.format(
                env_path))

    command = [env_path, script_path]
    if script_args:
        command.extend(script_args)

    try:
        result = subprocess.run(
            command,
            cwd=working_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8')

        if result.returncode == 0:
            return 'Script executed successfully:\n{}'.format(stdout)
        else:
            return 'Script execution failed:\n{}'.format(stderr)
    except subprocess.CalledProcessError as e:
        return 'Error: {}'.format(e.stderr)


def build_graph_database(graph_db: GraphDatabaseHandler,
                         repo_path: str,
                         task_id: str,
                         is_clear: bool = True,
                         max_workers=None,
                         env_path_dict=None,
                         update_progress_bar=None):
    """Build a graph database for a repository.
    
    Args:
        graph_db (GraphDatabaseHandler): The graph database handler.
        repo_path (str): The path to the repository.
        task_id (str): The ID of the task.
        is_clear (bool, optional): Whether to clear existing data. Defaults to True.
        max_workers (int, optional): Maximum number of worker threads. Defaults to None.
        env_path_dict (dict, optional): Dictionary with environment paths. Defaults to None.
        update_progress_bar (callable, optional): Function to update progress. Defaults to None.
        
    Returns:
        None or str: None if successful, error message if failed.
    """
    file_list = get_py_files(repo_path)
    root_path = repo_path

    if is_clear:
        graph_db.clear_task_data(task_id=task_id)

    start_time = time.time()

    total_files = len(file_list)

    if update_progress_bar:
        update_progress_bar(0.5 / total_files)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(run_single, file_path, root_path, task_id, True,
                            env_path_dict): file_path
            for file_path in file_list
        }
        for i, future in enumerate(as_completed(future_to_file)):
            file_path = future_to_file[future]
            try:
                future.result()
                print('Successfully processed {}'.format(file_path))
            except Exception as exc:
                msg = '`{}` generated an exception: `{}`'.format(
                    file_path, exc)
                print(msg)
                # Stop submitting new tasks and try to cancel all unfinished tasks
                executor.shutdown(wait=False, cancel_futures=True)
                return msg
            finally:
                # Update progress bar after each task
                if update_progress_bar:
                    update_progress_bar((i + 1) / total_files)
    
    # Process AST and class inheritance
    ast_manage = AstManager(repo_path, task_id, graph_db)
    ast_manage.run()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'✍️ Shallow indexing ({int(elapsed_time)} s)')
    return None
