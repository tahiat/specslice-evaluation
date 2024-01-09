import json
import os
import subprocess

issue_directory = 'ISSUES'

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

    specimin_input_dir = os.path.join(issue_directory_name, "input")
    specimin_output_dir = os.path.join(issue_directory_name, "output")

    os.makedirs(specimin_input_dir, exist_ok=True)
    os.makedirs(specimin_output_dir, exist_ok=True)
    return specimin_input_dir

def clone_repository(url, directory):  #TODO: parallel cloning task 
    subprocess.run(["git", "clone", url, directory])

def change_branch(directory, branch):
    pass

def checkout_commit(commit_hash):
    pass

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
        checkout_commit(commit_hash)

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