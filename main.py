import json
import os
import sys
import subprocess
import shutil
from Keyvalue import JsonKeys
from Result import Result
from report_builder import TableGenerator

issue_folder_dir = 'ISSUES'
specimin_input = 'input'
specimin_output = 'output'
specimin_project_name = 'specimin'
specimin_source_url = 'https://github.com/kelloggm/specimin.git'
TIMEOUT_DURATION = 300
specimin_env_var = "SPECIMIN"
json_status_file_name = "target_status.json"
minimized_program_build_log_file = "build_log.txt"

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

def get_specimin_env_var():
    '''
    Check and returns the path of the Specimin program if defined
    Retruns:
        Path of the local Specimin program
    '''
    specimin_env_value = os.environ.get(specimin_env_var)
    return specimin_env_value

def get_repository_name(github_ssh: str):
    '''
    Extract the repository name from github ssh
    Parameters:
        github_ssh (str): A valid github ssh

    Returns: repository name 
    '''
    repository_name = os.path.splitext(os.path.basename(github_ssh))[0]
    return repository_name

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
        issue_container_dir (str): Absolute path of the container directory containing all program directory.
        issue_id (str): Name of the directory to be created inside container directory.

    Returns:
        specimin_input_dir (str): A target directory of SPECIMIN. (issue_container_dir/issue_id/input) 
    '''
    issue_directory_name = os.path.join(issue_container_dir, issue_id)
    os.makedirs(issue_directory_name, exist_ok=True)

    specimin_input_dir = os.path.join(issue_directory_name, specimin_input)
    #specimin_output_dir = os.path.join(issue_directory_name, specimin_output)

    os.makedirs(specimin_input_dir, exist_ok=True)
    #if os.path.exists(specimin_output):
    #     shutil.rmtree(specimin_output)
    #os.makedirs(specimin_output_dir, exist_ok=True)
    return specimin_input_dir


def is_git_directory(dir):
    '''
    Check whether a directory is a git directory
    Parameters:
        dir: path of the directory
    Returns:
        booleans
    '''
    git_dir_path = os.path.join(dir, '.git')
    return os.path.exists(git_dir_path) and os.path.isdir(git_dir_path)

def get_target_data(url, branch, commit, directory):
    '''
    Get target repository data 

    Parameters:
        url (str): repository url
        branch(str): branch name
        commit(str): commit #
        directory (str): directory to clone in
    '''
    project_name = get_repository_name(url)
    if (os.path.exists(os.path.join(directory, project_name))):
        print(f"{project_name} repository already exists. Aborting cloning")
        return

    clone_command = ["git", "clone"]
    if branch:
        clone_command.extend(["-b", branch])
    if not commit:
        clone_command.extend(["--depth", "1"])
        clone_command.append(url)
        subprocess.run(clone_command, cwd=directory) # targetted clone is fast, no need to reuse existing one.
    else:
        clone_command.append(url)
        subprocess.run(clone_command, cwd=directory)
        checkout_commit(commit, os.path.join(directory, get_repository_name(url)))

    cmd_str = ' '.join(clone_command)
    print(f"get_target_data -> {cmd_str}")

def clone_repository(url, directory):
    '''
    Clone a repository from 'url' in 'directory' 

    Parameters:
        url (str): repository url
        directory (str): directory to clone in
    '''
    project_name = get_repository_name(url)
    if (os.path.exists(os.path.join(directory, project_name))):
        print(f"{project_name} repository already exists. Aborting cloning")
        # make sure the existing repo is clean
        project_dir=str(os.path.join(directory, project_name))
        subprocess.run(["git", "reset", "--hard"], cwd=project_dir)
        subprocess.run(["git", "clean", "-f", "-d", "-x"], cwd=project_dir)
        return
    subprocess.run(["git", "clone", url], cwd=directory)

def change_branch(branch, directory):
    '''
    Checkout a branch of a git repository

    Parameters:
        branch (str): branch name
        directory (str): local directory of the git repository
    '''
    if not is_git_directory(directory):
        raise ValueError(f"{directory} is not a valid git directory")
    command = ["git", "checkout", f"{branch}"]
    subprocess.run(command, cwd=directory)

def checkout_commit(commit_hash, directory):   
    '''
    Checkout a commit of a git repository

    Parameters:
        commit_hash (str): commit hash
        directory (str): local directory of the git repository
    '''
    if not is_git_directory(directory):
        raise ValueError(f"{directory} is not a valid git directory")
    
    if (commit_hash):
        command = ["git", "checkout", commit_hash]
        result = subprocess.run(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else: 
        return True
    if result.returncode == 0:
        print(f"Successfully checked-out commit {commit_hash} in {directory}")
    else:
        print(f"Failed to checkout commit {commit_hash} in {directory}")
    return result.returncode == 0 if True else False

def perform_git_pull (directory):
    '''
    Pull latest of a git repository

    Parameters:
        directory (str): local directory of the git repository
    '''
    command=["git", "pull", "origin", "--rebase"]
    subprocess.run(command, cwd=directory)

def clone_specimin(path_to_clone, url): 
    '''
    Clone the latest Specimin project from github

    Parameters:
        path_to_clone (str): Path where Specimin is to be clonned
        url (str): url of specimin
    '''
    spcimin_source_path = os.path.join(issue_folder_dir, specimin_project_name)
    if (os.path.exists(spcimin_source_path)) and os.path.isdir(spcimin_source_path):
        perform_git_pull(spcimin_source_path)
    else:
        get_target_data(url, "", "", path_to_clone)


def build_specimin_command(project_name: str,
                           target_base_dir_path: str,
                           root_dir: str,  
                           targets: list):
    '''
    Build the gradle command to execute Specimin on target project

    issue_container_dir(ISSUES)
    |--- issue_id(cf-1291)     
    |    |--- input  ---> it contains the git repository of a target project
    |    |      |----nomulus/core/src/main/java/    ---> this is the root directory of a package
    |    |                                   |---package_path/file.java (daikon/chicory/PureMethodInfo.java)  --> a target file
    |    |--- output --> Contains minimization result of Specimin

    
    Parameters:
        project_name (str): Name of the target project. Example: daikon
        target_base_dir (str): path of the target project directory. Ex: ISSUES/cf-1291
        root_dir (str): A directory path relative to the project base directory where java package stored.
        targets ({'method': '', 'file': '', 'package': ''}) : target java file and method name data
    
    Retruns:
        command (str): The gradle command of SPECIMIN for the issue.
    '''
    
    if not os.path.isabs(target_base_dir_path):
        raise ValueError("Invalid argument: target_base_dir_path must be an absolute path")

    output_dir = os.path.join(target_base_dir_path, specimin_output, project_name, "src", "main", "java")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    root_dir = os.path.join(target_base_dir_path, specimin_input, project_name, root_dir)
    root_dir = root_dir.rstrip('/') + os.sep

    target_file_list = []
    target_method_list = []

    for target in targets:

        method_name = target[JsonKeys.METHOD_NAME.value]
        file_name = target[JsonKeys.FILE_NAME.value]
        package_name = target[JsonKeys.PACKAGE.value]

        dot_replaced_package_name = package_name.replace('.', '/')

        if file_name:
            qualified_file_name = os.path.join(dot_replaced_package_name, file_name)
            target_file_list.append(qualified_file_name)

        if method_name:
            inner_class_name = ""
            if JsonKeys.INNER_CLASS.value in target and target[JsonKeys.INNER_CLASS.value] :
                inner_class_name = f".{target[JsonKeys.INNER_CLASS.value]}"
            #if non-primary class exists, file name will not be included in target-method
            # Look for PR #177: https://github.com/kelloggm/specimin/pull/177

            if JsonKeys.NON_PRIMARY_CLASS.value in target and target[JsonKeys.NON_PRIMARY_CLASS.value]:
                qualified_method_name = package_name + "." + target[JsonKeys.NON_PRIMARY_CLASS.value] + inner_class_name + "#" + method_name
            else:
                qualified_method_name = package_name + "." + os.path.splitext(file_name)[0]+ inner_class_name + "#" + method_name
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

def run_specimin(issue_name, command, directory) -> Result:
    '''
    Execute SPECIMIN on a target project

    Parameters:
        command (str): The gradle command to run specimin
        directory (str): The base directory of the specimin repository
    
    Returns: 
        Result: execution result of Specimin
    '''
    print(f"{issue_name} executing...")
    try:
        result = subprocess.run(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=TIMEOUT_DURATION)
        print(f"{issue_name} execution ends.")
        if result.returncode == 0:
            return Result(issue_name, "PASS", "")
        else:
            error_msg_file = os.path.join(issue_folder_dir, issue_name, f"{issue_name}_error.txt") # not abs path. ISSUES/cf-1291/cf-1291_error.txt
            try:
                stderr_str = result.stderr.decode("utf-8") # this can fail.
                stderr_lines = stderr_str.split('\n')[:5]
                first_five_lines_stderr = '\n'.join(stderr_lines)
                print(first_five_lines_stderr)
                if os.path.exists(error_msg_file):
                    os.remove(error_msg_file)
                with open(error_msg_file, 'w') as file:
                    file.write(stderr_str)
            except UnicodeDecodeError as e:
                 print("Error decoding stderr:", e)
            return Result(issue_name, "FAIL", f"{error_msg_file}")
    except subprocess.TimeoutExpired:
        print(f"{issue_name} execution ends. TIMEOUT")
        return Result(issue_name, "FAIL", "Timeout")
    except Exception as e:
        return Result(issue_name, "FAIL", f"Unhandled exception occurred: {e}")
    
    

def performEvaluation(issue_data) -> Result:
    '''
    For each issue data, execute SPECIMIN on a target project. 

    Parameters:
        issue ({}): json data associated with an issue    
    '''

    issue_id = issue_data[JsonKeys.ISSUE_ID.value]
    url = issue_data[JsonKeys.URL.value]
    branch = issue_data[JsonKeys.BRANCH.value]
    commit_hash = issue_data[JsonKeys.COMMIT_HASH.value]

    issue_folder_abs_dir = os.path.abspath(issue_folder_dir)
    input_dir = create_issue_directory(issue_folder_abs_dir, issue_id)

    get_target_data(url, branch, commit_hash, input_dir) 
    
    repo_name = get_repository_name(url)
    specimin_command = ""
    result: Result = None
    specimin_path = get_specimin_env_var()
    if specimin_path is not None and os.path.exists(specimin_path):
        specimin_command = build_specimin_command(repo_name, os.path.join(issue_folder_abs_dir, issue_id), issue_data[JsonKeys.ROOT_DIR.value], issue_data[JsonKeys.TARGETS.value])
        result = run_specimin(issue_id ,specimin_command, specimin_path)
    else:
        specimin_command = build_specimin_command(repo_name, os.path.join(issue_folder_abs_dir, issue_id), issue_data[JsonKeys.ROOT_DIR.value], issue_data[JsonKeys.TARGETS.value])
        result = run_specimin(issue_id ,specimin_command, os.path.join(issue_folder_abs_dir, specimin_project_name))
    
    print(f"{result.name} - {result.status}")

    test_targets = ["cf-6282", "cf-6077", "cf-6019", "cf-4614"] #only running on these targets. 
    if issue_id not in test_targets:
        return result


    # build script is shipped with input program. It exists in the "specimin" directory of the input program's root directory.
    # Coping the build script to the output directory of the minimized program.
    build_script_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "build.gradle")
    build_script_destination_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_output, repo_name, "build.gradle")

    copy_build_script = f"cp {build_script_path} {build_script_destination_path}"
    subprocess.run(copy_build_script, shell=True)
    
    #../ISSUES/cf-xx/output/projectname/build_log.txt
    log_file = os.path.join(issue_folder_abs_dir, issue_id, specimin_output, repo_name, minimized_program_build_log_file)

    if os.path.exists(log_file):
        os.remove(log_file)

    # Open the log file in write mode
    with open(log_file, "w") as log_file_obj:
        build_status = subprocess.run(f"./gradlew -b  {build_script_destination_path} compileJava", cwd = os.path.abspath("resources"), shell=True, stderr=log_file_obj)
        print(f"{issue_id} Minimized program gradle build status = {build_status}")

    expected_log_file = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "expected_log.txt")
    if (issue_data[JsonKeys.BUG_TYPE.value] == "crash"):
        compare_crash_log(expected_log_file, log_file)

    return result



def compare_crash_log(expected_log_path, actual_log_path):
    with open(expected_log_path, "r") as file:
        expected_content = file.read()

    with open(actual_log_path, "r") as file:
        actual_content = file.read()
    
    expected_lines = expected_content.split('\n')
    actual_lines = actual_content.split('\n')

    ## get line # of "; The Checker Framework crashed."
    expected_cf_crash_line = next(line_no for line_no, line in enumerate(expected_lines) if line.lstrip().startswith('; The Checker Framework crashed.'))
    expected_crashed_class_name_line = -1
    for i in range(expected_cf_crash_line, expected_cf_crash_line + 5): # should be immediate next line of crash line
        if expected_lines[i].lstrip().startswith("Compilation unit:"):
            expected_crashed_class_name_line = i
            break

    expected_class_name_abs_path = expected_lines[expected_crashed_class_name_line].split(" ")[-1]
    expected_crashed_class_name = os.path.basename(expected_class_name_abs_path)

    exception_line = -1
    for i in range(expected_crashed_class_name_line, expected_crashed_class_name_line + 5): # should be immediate next line of crash line
        if expected_lines[i].lstrip().startswith("Exception:"):
            exception_line = i
            break
    
    exception_stack = [] #compare it with actual stack trace
    expected_exception_cause = (expected_lines[exception_line].split(":")[-1]).strip()
    for i in range(exception_line + 1, exception_line + 6):
        if expected_lines[i].lstrip().startswith("at"):
            exception_stack.append(expected_lines[i].split("at")[-1].strip())


    actual_cf_crash_line = [line_no for line_no, line in enumerate(actual_lines) if line.lstrip().startswith('; The Checker Framework crashed.')]
    if len(actual_cf_crash_line) == 0:
        print("The Checker Framework did not crash in the minimized program")
        return False
    
    for line_no in actual_cf_crash_line: # if multiple crash location found, one shoud match exactly with the expected crash information
        actual_crashed_class_name_line = -1
        for i in range(line_no, line_no + 5): # should be immediate next line of crash line
            if actual_lines[i].strip().startswith("Compilation unit:"):
                actual_crashed_class_name_line = i
                break
        if actual_crashed_class_name_line == -1:
            continue  # start looking for next crash location
        actual_class_name_abs_path = actual_lines[actual_crashed_class_name_line].split(" ")[-1]
        actual_crashed_class_name = os.path.basename(actual_class_name_abs_path)

        actual_exception_line = -1
        for i in range(actual_crashed_class_name_line, actual_crashed_class_name_line + 5): # should be immediate next line of crash line
            if actual_lines[i].strip().startswith("Exception:"):
                actual_exception_line = i
                break
        actual_exception_stack = [] #compare it with actual stack trace
        actual_exception_cause = (actual_lines[actual_exception_line].split(":")[-1]).strip()
        for i in range(actual_exception_line + 1, actual_exception_line + 6):
            if actual_lines[i].lstrip().startswith("at"):
                actual_exception_stack.append(actual_lines[i].split("at")[-1].strip())
        
        log_match = True
        if expected_crashed_class_name != actual_crashed_class_name:
            log_match = False
        if expected_exception_cause != actual_exception_cause:
            log_match = False
        
        if len(exception_stack) != len(actual_exception_stack):
            log_match = False
        
        for i in range(len(exception_stack)):
            if exception_stack[i] != actual_exception_stack[i]:
                log_match = False
        
        
        
    # match the class name of the crash




def main():
    '''
    Main method of the script. It iterates over the json data and perform minimization for each cases.   
    '''
    os.makedirs(issue_folder_dir, exist_ok=True)   # create the issue holder directory
    
    specimin_path = get_specimin_env_var()
    if specimin_path is not None and os.path.exists(specimin_path) and os.path.isdir(specimin_path):
        print("Local Specimin copy is being used")
    else:
        print("Local Specimin not found. Cloning a Specimin copy")
        clone_specimin(issue_folder_dir, specimin_source_url)

    args = sys.argv
    specified_targets: str = ""
    if (len(args) - 1) >= 1:
        specified_targets = args[1]  # paper_target/bug_target

    json_file_path: str
    if specified_targets.lower() == "bugs":
        json_file_path = os.path.join("resources", "sp_issue.json")
    else:
        json_file_path = os.path.join("resources", "test_data.json")

    parsed_data = read_json_from_file(json_file_path)

    evaluation_results: list[Result] = []
    json_status: dict[str, str] = {} # Contains PASS/FAIL status of targets to be printed as a json file 
    if parsed_data:
        for issue in parsed_data:
            issue_id = issue["issue_id"]
            print(f"{issue_id} execution starts =========>")
            result = performEvaluation(issue)
            evaluation_results.append(result)
            json_status[issue_id] = result.status
            print((f"{issue_id} <========= execution Ends."))
            # task of crash generation on minimized program. 
            # copy the build script from the input target specimin directory
            
            


    report_generator: TableGenerator = TableGenerator(evaluation_results)
    report_generator.generateTable()

    json_status_file = os.path.join(issue_folder_dir, json_status_file_name)
    # Write JSON data in a file. This can be compared from specimin to verify that the successful # of targets do not get reduced in a PR
    with open(json_status_file, "w") as json_file:
        json.dump(json_status, json_file, indent= 2)

    print("\n\n\n\n")
    print(f"issue_name    |    status    |    reason")
    print("--------------------------------------------")
    case = 1
    for minimization_result in evaluation_results:
        print(f"({case}){minimization_result.name}    |    {minimization_result.status}     |    {minimization_result.reason}")
        case +=1

    

    

if __name__ == "__main__":
    main()
