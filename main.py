import json
import os
import subprocess

issue_directory = 'ISSUES'
specimin_input = 'input'
specimin_output = 'ouput'
specimin_project_name = 'specimin'
specimin_source_url = 'git@github.com:kelloggm/specimin.git'

def read_json_from_file(file_path):
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

def create_directory(issue_container_dir, issue_id):
    issue_directory_name = os.path.join(issue_container_dir, issue_id)
    os.makedirs(issue_directory_name, exist_ok=True)

    specimin_input_dir = os.path.join(issue_directory_name, specimin_input)
    specimin_output_dir = os.path.join(issue_directory_name, specimin_output)

    os.makedirs(specimin_input_dir, exist_ok=True)
    os.makedirs(specimin_output_dir, exist_ok=True)
    return specimin_input_dir

def clone_repository(url, directory):
    subprocess.run(["git", "clone", url, directory])

def change_branch(branch, directory):
    pass

def checkout_commit(commit_hash, directory):   
    command = ["git", "checkout", commit_hash]
    result = subprocess.run(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if the command was successful
    if result.returncode == 0:
        print(f"Successfully checked-out commit {commit_hash} in {directory}")
    else:
        print(f"Failed to checkout commit {commit_hash} in {directory}")
        

def run_specimin(issue_id, root_dir, package_name, targets):
    command = ["./gradlew", "run", "-"]


    output_dir = os.path.join(issue_directory, issue_id, specimin_output)
    root_dir = os.path.join(issue_directory, issue_id, specimin_input, root_dir) + os.sep


    dot_replaced_package_name = package_name.replace('.', '/')

    target_file_list = []
    target_method_list = []

    for target in targets:
        method_name = target["method"]
        file_name = target["file"]

        if file_name:
            qualified_file_name = os.path.join(dot_replaced_package_name, file_name)
            target_file_list.append(qualified_file_name)

        if method_name:
            qualified_method_name = package_name + "." + os.path.splitext(file_name)[0]+ "#" + method_name
            target_method_list.append(qualified_method_name)








def performEvaluation(issue):
    issue_id = issue['issue_id']
    url = issue['url']
    branch = issue['branch']
    commit_hash = issue['commitHash']
    specimin_command = issue['specimin_command']

    input_dir = create_directory(issue_directory, issue_id)
    clone_repository(url, input_dir)  # TODO: check if clonning is successful.

    if branch:
        change_branch(input_dir, branch)  
    
    if commit_hash:
        checkout_commit(commit_hash, input_dir)

    success = run_specimin(issue_id, issue['rootDir'], issue['package'], issue['targets'])

    if success:
        print(f"Test {issue_id} successfully completed.")
    else:
        print(f"Test {issue_id} failed.")


def perform_git_pull (directory):
    command=["git", "pull", "origin", "--rebase"]
    subprocess.run(command, cwd=directory)

def clone_specimin(): 
    spcimin_source_path = os.path.join(issue_directory, specimin_project_name)
    if (os.path.exists(spcimin_source_path)) and os.path.isdir(spcimin_source_path):
        perform_git_pull(spcimin_source_path)
    else:
        clone_repository(specimin_source_url, spcimin_source_path)

def main():
    clone_specimin()

    json_file_path = 'resources/test_data.json'
    parsed_data = read_json_from_file(json_file_path)

    if parsed_data:
        for issue in parsed_data:
            performEvaluation(issue)


if __name__ == "__main__":
    main()