import json
import os
import subprocess

issue_directory = 'ISSUES'
specimin_input = 'input'
specimin_output = 'ouput'

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

def clone_repository(url, directory):  #TODO: parallel cloning task 
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
        

def run_specimin(build_command):
    pass

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

    success = run_specimin(specimin_command)

    if success:
        print(f"Test {issue_id} successfully completed.")
    else:
        print(f"Test {issue_id} failed.")

def main():
   
    json_file_path = 'resources/test_data.json'

    parsed_data = read_json_from_file(json_file_path)

    if parsed_data:
        for issue in parsed_data:
            performEvaluation(issue)

if __name__ == "__main__":
    main()