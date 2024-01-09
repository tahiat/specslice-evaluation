import json
import os
import subprocess

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

def create_directory(issue_id):
    directory_name = f"={issue_id}"
    os.makedirs(directory_name, exist_ok=True)
    return directory_name

def clone_repository(url):
    subprocess.run(["git", "clone", url])

def change_branch(directory, branch):
    os.chdir(directory)
    subprocess.run(["git", "checkout", branch])

def checkout_commit(commit_hash):
    subprocess.run(["git", "checkout", commit_hash])

def run_specimin(build_command):
    result = subprocess.run(build_command, shell=True)
    return result.returncode == 0

def performEvaluation(issue):
    test_id = issue['issue_id']
    url = issue['url']
    branch = issue['branch']
    commit_hash = issue['commitHash']
    specimin_command = issue['specimin_command']

    
    test_directory = create_directory(test_id)

    clone_repository(url)  # TODO: check if clonning is successful.
    change_branch(test_directory, branch)  #
    checkout_commit(commit_hash)

    success = run_specimin(specimin_command)

    if success:
        print(f"Test {test_id} successfully completed.")
    else:
        print(f"Test {test_id} failed.")

def main():
   
    json_file_path = 'resources/test_data.json'

    parsed_data = read_json_from_file(json_file_path)

    if parsed_data:
        for issue in parsed_data:
            performEvaluation(issue)

if __name__ == "__main__":
    main()