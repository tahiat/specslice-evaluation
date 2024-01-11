import json
import os
import subprocess
from Keyvalue import JsonKeys


issue_folder_dir = 'ISSUES'
specimin_input = 'input'
specimin_output = 'ouput'
specimin_project_name = 'specimin'
specimin_source_url = 'git@github.com:kelloggm/specimin.git'

def read_json_from_file(file_path):
    '''
    Parse a json file.

    Parameters:
        file_path (path): Path to the json file

    Retruns:
        { }: Parsed json data
    '''
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
        return json_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

def create_issue_directory(issue_container_dir, issue_id):
    '''
    Creates a directory to store a SPECIMIN target project. Example: issue_id of cf-111 will create
    a cf-111 directory inside 'issue_container_dir'. Two other directory (input and output inside) will
    be created inside 'issue_container_dir/issue_id' directory. Target project is cloned inside 
    'issue_container_dir/issue_id/input' directory. SPECIMIN output is stored inside 'issue_container_dir/issue_id/output'
    directory

    issue_container_dir
    |--- issue_id     
    |    |--- input
    |    |--- output 

    Parameters: 
        issue_container_dir (str): The directory where new directory is created
        issue_id (str): Name of the directory to be created

    Returns:
        specimin_input_dir (str): A target directory of SPECIMIN.  
    '''
    issue_directory_name = os.path.join(issue_container_dir, issue_id)
    os.makedirs(issue_directory_name, exist_ok=True)

    specimin_input_dir = os.path.join(issue_directory_name, specimin_input)
    specimin_output_dir = os.path.join(issue_directory_name, specimin_output)

    os.makedirs(specimin_input_dir, exist_ok=True)
    os.makedirs(specimin_output_dir, exist_ok=True)
    return specimin_input_dir

def clone_repository(url, directory):
    '''
    Clone a repository from 'url' in 'directory' 

    Parameters:
        url (str): repository url
        directory (str): directory to clone in
    '''
    subprocess.run(["git", "clone", url, directory])

def change_branch(branch, directory):
    '''
    Checkout a branch of a git repository

    Parameters:
        branch (str): branch name
        directory (str): local directory of the git repository
    '''
    command = ["git", "checkout", f"{branch}"]
    subprocess.run(command, cwd=directory)

def checkout_commit(commit_hash, directory):   
    '''
    Checkout a commit of a git repository

    Parameters:
        commit_hash (str): commit hash
        directory (str): local directory of the git repository
    '''
    command = ["git", "checkout", commit_hash]
    result = subprocess.run(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print(f"Successfully checked-out commit {commit_hash} in {directory}")
    else:
        print(f"Failed to checkout commit {commit_hash} in {directory}")

def perform_git_pull (directory):
    '''
    Pull latest of a git repository

    Parameters:
        directory (str): local directory of the git repository
    '''
    command=["git", "pull", "origin", "--rebase"]
    subprocess.run(command, cwd=directory)

def clone_specimin(): 
    '''
    Checkout a commit of a git repository

    Parameters:
        commit_hash (str): commit hash
        directory (str): local directory of the git repository
    '''
    spcimin_source_path = os.path.join(issue_folder_dir, specimin_project_name)
    if (os.path.exists(spcimin_source_path)) and os.path.isdir(spcimin_source_path):
        perform_git_pull(spcimin_source_path)
    else:
        clone_repository(specimin_source_url, spcimin_source_path)


def build_specimin_command(issue_id, root_dir, package_name, targets):
    '''
    Checkout a commit of a git repository

    issue_container_dir(ISSUES)
    |--- issue_id(cf-1291)     
    |    |--- input  ---> it contains the git repository of a target project
    |    |      |----nomulus/core/src/main/java/    ---> this is the root directory of a package
    |    |                                   |---package_path/file.java (daikon/chicory/PureMethodInfo.java)  --> a target file
    |    |--- output --> Contains minimization result of Specimin

    
    Parameters:
        issue_id (str): Name of the directory/folder that contains a SPECIMINS' target project. Ex: cf-1291
        root_dir (str): A directory path relative to the project base directory where java package stored.
        package_name (str): A valid Java package
        targets ({'method': '', 'file': ''}) : targetted java file and method name data
    
    Retruns:
        command (str): The gradle command of SPECIMIN for the issue.
    '''
    output_dir = os.path.join("..", issue_id, specimin_output)
    root_dir = os.path.join("..", issue_id, specimin_input, root_dir) + os.sep

    dot_replaced_package_name = package_name.replace('.', '/')

    target_file_list = []
    target_method_list = []

    for target in targets:
        method_name = target[JsonKeys.METHOD_NAME.value]
        file_name = target[JsonKeys.FILE_NAME.value]

        if file_name:
            qualified_file_name = os.path.join(dot_replaced_package_name, file_name)
            target_file_list.append(qualified_file_name)

        if method_name:
            qualified_method_name = package_name + "." + os.path.splitext(file_name)[0]+ "#" + method_name
            target_method_list.append(qualified_method_name)

    output_dir_subcommand = "--outputDirectory" + " " + f"\"{output_dir}\""
    root_dir_subcommand = "--root" + " " + f"\"{root_dir}\""

    target_file_subcommand = ""
    for file in target_file_list:
        target_file_subcommand += "--targetFile" + " " + f"\"{file}\""

    target_method_subcommand = ""
    for method in target_method_list:
        target_method_subcommand += "--targetMethod" + " " + f"\"{method}\""

    command_args = root_dir_subcommand + " " + output_dir_subcommand + " " + target_file_subcommand + " " + target_method_subcommand
    command = "./gradlew" + " " + "run" + " " + "--args=" + f"\'{command_args}\'"
    
    return command

def run_specimin(command, directory):
    '''
    Execute SPECIMIN on a target project

    Parameters:
        command (str): The gradle command to run specimin
        directory (str): The base directory of the specimin repository
    
    Returns: 
        boolean: True/False based on successful execution of SPECIMIN
    '''
    result = subprocess.run(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) # TODO:
    if result.returncode == 0:
        return True
    else:
        return False
    

def performEvaluation(issue_data):
    '''
    For each issue dataExecute SPECIMIN on a target project. 

    Parameters:
        issue ({}): json data associated with an issue    
    '''

    issue_id = issue_data[JsonKeys.ISSUE_ID.value]
    url = issue_data[JsonKeys.URL.value]
    branch = issue_data[JsonKeys.BRANCH.value]
    commit_hash = issue_data[JsonKeys.COMMIT_HASH.value]

    input_dir = create_issue_directory(issue_folder_dir, issue_id)
    clone_repository(url, input_dir)  # TODO: check if clonning is successful.

    if branch:
        change_branch(input_dir, branch)  
    
    if commit_hash:
        checkout_commit(commit_hash, input_dir)

    specimin_command = build_specimin_command(issue_id, issue_data[JsonKeys.ROOT_DIR.value], issue_data[JsonKeys.PACKAGE.value], issue_data[JsonKeys.TARGETS.value])

    success = run_specimin(specimin_command, os.path.join(issue_folder_dir, specimin_project_name))

    if success:
        print(f"Test {issue_id} successfully completed.")
    else:
        print(f"Test {issue_id} failed.")


def main():
    '''
    Main method of the script. It iterates over the json data and perform minimization for each cases.   
    '''

    clone_specimin()
    json_file_path = 'resources/test_data.json'
    parsed_data = read_json_from_file(json_file_path)

    if parsed_data:
        for issue in parsed_data:
            performEvaluation(issue)


if __name__ == "__main__":
    main()