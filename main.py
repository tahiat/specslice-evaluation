import json
import re
import os
import sys
import subprocess
import shutil
from Keyvalue import JsonKeys
from Result import Result
from report_builder import TableGenerator
from exception_data import ExceptionData
import zipfile
import platform
import tarfile
import glob
import stat
import argparse
import time
import math
import statistics

issue_folder_dir = 'ISSUES'
specimin_input = 'input'
specimin_output = 'output'
specimin_jar_output = 'jar_output'
specimin_project_name = 'specimin'
specimin_source_url = 'https://github.com/kelloggm/specimin.git'
TIMEOUT_DURATION = 300
specimin_env_var = "SPECIMIN"
json_status_file_name = "target_status.json"
minimized_program_build_log_file = "build_log.txt"
linux_system_identifier = "Linux"
macos_system_identifier = "Darwin"
windows_system_identifier = "Windows"
preservation_status_file_name = "preservation_status.json"
run_time = {}

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

def set_directory_exec_permission(directory_path):
    if isWindows():
        # Code borrowed and modified from https://stackoverflow.com/questions/12168110/how-to-set-folder-permissions-in-windows
        # Licensed under CC BY-SA 3.0
        import win32security
        import ntsecuritycon as con

        user, _, _ = win32security.LookupAccountName ("", os.getlogin())
        sd = win32security.GetFileSecurity(directory_path, win32security.DACL_SECURITY_INFORMATION)
        
        dacl = sd.GetSecurityDescriptorDacl()

        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_EXECUTE, user)

        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(directory_path, win32security.DACL_SECURITY_INFORMATION, sd)
    else:
        current_permissions = os.stat(directory_path).st_mode
        new_permissions = current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH # owner, group, other
        os.chmod(directory_path, new_permissions)

def download_with_wget_or_curl(url, save_as):
    try:
        # Windows doesn't have wget by default
        if isWindows():
            subprocess.run(["curl", "-L", "-o", save_as, url])
        else:
            subprocess.run(["wget", "-q", "--show-progress", "-O", save_as, url], check=True)
        print("File downloaded successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to download file:", e)

def unzip_file(zip_file):
    '''
    unzips a zip file
    '''
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall()

def extract_and_rename(tar_or_zip_file, target_name):
    if isWindows():
        with zipfile.ZipFile(tar_or_zip_file, 'r') as zip_ref:
            zip_ref.extractall()
            extracted_dir = zip_ref.namelist()[0]
            set_directory_exec_permission(extracted_dir)
        # Windows doesn't allow overwrite when renaming
        if os.path.exists(target_name):
            shutil.rmtree(target_name)
    else:
        with tarfile.open(tar_or_zip_file, "r:gz") as tar:
            tar.extractall()
            extracted_dir = tar.getnames()[0]
            set_directory_exec_permission(extracted_dir)
    os.rename(extracted_dir, target_name)

def execute_shell_command_with_logging(command, log_file_path):
    with open(log_file_path, 'w') as f:
       st = subprocess.run(command, stderr=f)
       if st.returncode == 0:
           raise Exception("exception")


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
    os.makedirs(specimin_input_dir, exist_ok=True)

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
                           targets: list,
                           jar_path: str = "",
                           isJarMode = False):
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
        targets ({'method': '' or 'field': '', 'file': '', 'package': ''}) : target java file and method/field name data
    
    Retruns:
        command (str): The gradle command of SPECIMIN for the issue.
    '''
    
    if not os.path.isabs(target_base_dir_path):
        raise ValueError("Invalid argument: target_base_dir_path must be an absolute path")

    if isJarMode:
        output_dir = os.path.join(target_base_dir_path, specimin_jar_output, project_name, "src", "main", "java")
    else:
        output_dir = os.path.join(target_base_dir_path, specimin_output, project_name, "src", "main", "java")
                                  
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    root_dir = os.path.join(target_base_dir_path, specimin_input, project_name, root_dir)
    root_dir = root_dir.rstrip(os.sep) + os.sep

    # avoid mixed slashes + convert \ to / for gradlew
    if isWindows():
        output_dir = os.path.normpath(output_dir).replace('\\', '/')
        root_dir = os.path.normpath(root_dir).replace('\\', '/')
        jar_path = os.path.normpath(jar_path).replace('\\', '/')

    target_file_list = []
    target_method_list = []
    target_field_list = []

    for target in targets:

        method_name = target[JsonKeys.METHOD_NAME.value]
        field_name = target.get(JsonKeys.FIELD_NAME.value)
        file_name = target[JsonKeys.FILE_NAME.value]
        package_name = target[JsonKeys.PACKAGE.value]

        dot_replaced_package_name = package_name.replace('.', '/')

        if file_name:
            qualified_file_name = os.path.join(dot_replaced_package_name, file_name)
            # avoid mixed slashes + convert \ to / for gradlew
            if isWindows():
                qualified_file_name = os.path.normpath(qualified_file_name).replace('\\', '/')
            target_file_list.append(qualified_file_name)

        inner_class_name = ""
        if JsonKeys.INNER_CLASS.value in target and target[JsonKeys.INNER_CLASS.value] :
            inner_class_name = f".{target[JsonKeys.INNER_CLASS.value]}"

        if method_name:
            #if non-primary class exists, file name will not be included in target-method
            # Look for PR #177: https://github.com/kelloggm/specimin/pull/177

            if JsonKeys.NON_PRIMARY_CLASS.value in target and target[JsonKeys.NON_PRIMARY_CLASS.value]:
                qualified_method_name = package_name + "." + target[JsonKeys.NON_PRIMARY_CLASS.value] + inner_class_name + "#" + method_name
            else:
                qualified_method_name = package_name + "." + os.path.splitext(file_name)[0]+ inner_class_name + "#" + method_name
            target_method_list.append(qualified_method_name)

        if field_name:
            target_field_list.append(package_name + "." + os.path.splitext(file_name)[0]+ inner_class_name + "#" + field_name)

    output_dir_subcommand = "--outputDirectory" + " " + f"\"{output_dir}\""
    root_dir_subcommand = "--root" + " " + f"\"{root_dir}\""
    target_file_subcommand = ""
    for file in target_file_list:
        target_file_subcommand += "--targetFile" + " " + f"\"{file}\""

    target_method_subcommand = ""
    for method in target_method_list:
        target_method_subcommand += "--targetMethod" + " " + f"\"{method}\""

    target_field_subcommand = ""
    for field in target_field_list:
        target_field_subcommand += " --targetField" + " " + f"\"{field}\""

    jar_path_subcommand = ""
    if jar_path:
        jar_path_subcommand = " --jarPath" + " " + f"\"{jar_path}\""

    command_args = root_dir_subcommand + " " + output_dir_subcommand + " " + target_file_subcommand + " " + target_method_subcommand +  target_field_subcommand + jar_path_subcommand
    

    command = ""

    if isWindows():
        command = "gradlew.bat"
    else:
        command = "./gradlew"

    command += " " + "run" + " " + "--args="

    if isWindows():
        command_args = command_args.replace("\"", "\'")
        command += f"\"{command_args}\""
    else:
        command += f"\'{command_args}\'"

    
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


def pullDependencies(script_path, specimin_path):
    command = ""

    # avoid mixed slashes + convert \ to / for gradlew
    if isWindows():
        script_path = os.path.normpath(script_path).replace('\\', '/')
        command = "gradlew.bat"
    else:
        command = "./gradlew"

    command = f"{command} -b {script_path} pullJar"
    
    status = subprocess.run(command, cwd = specimin_path, shell=True)
    print(f"Jar pull status = {status.returncode}")

def copyFiles(src_dir, des_dir):
    files = os.listdir(src_dir)
    # Iterate through the files and copy .jar files
    for file in files:
        if file.endswith(".jar"):
            src_file = os.path.join(src_dir, file)
            dest_file = os.path.join(des_dir, file)
            shutil.copy2(src_file, dest_file)

def performEvaluation(issue_data, isJarMode = False) -> Result:
    '''
    For each issue data, execute SPECIMIN on a target project. 

    Parameters:
        issue ({}): json data associated with an issue    
    '''

    issue_id = issue_data[JsonKeys.ISSUE_ID.value]
    url = issue_data[JsonKeys.URL.value]
    branch = issue_data[JsonKeys.BRANCH.value]
    commit_hash = issue_data[JsonKeys.COMMIT_HASH.value]
    qual_jar_required = issue_data[JsonKeys.CHECKER_QUAL_REQURIED.value]

    issue_folder_abs_dir = os.path.abspath(issue_folder_dir)
    input_dir = create_issue_directory(issue_folder_abs_dir, issue_id)
    repo_name = get_repository_name(url)

    specimin_path = get_specimin_env_var()
    if not specimin_path or not os.path.exists(specimin_path):
        print("Clone copy of Specimin is used")
        specimin_path = os.path.join(issue_folder_abs_dir, specimin_project_name)

    get_target_data(url, branch, commit_hash, input_dir) 

    jar_path = ""
    if isJarMode:
        jar_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "libs") # this should include the qual jar if needed
        os.makedirs(jar_path, exist_ok=True)
        req_dep_in_jar_mode = issue_data.get("has_dependency", False)
        jar_pull_script = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "dependency.gradle")
        if req_dep_in_jar_mode and not os.path.exists(jar_pull_script):
            print("Jar pull script is not available.")
            return Result(issue_id, "FAIL", "Jar pull script unavailable")
        elif req_dep_in_jar_mode and os.path.exists(jar_pull_script):
            pullDependencies(jar_pull_script, specimin_path)
    elif qual_jar_required:
        jar_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "checker") # in seperate directory so that unnecessary jar's are not loaded
    else:
        jar_path = ""
    
    qual_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "checker")
    if isJarMode and qual_jar_required:
        if os.path.exists(qual_path):
            copyFiles(qual_path, jar_path)
    
    specimin_command = ""
    result: Result = None
    
    specimin_command = build_specimin_command(repo_name, os.path.join(issue_folder_abs_dir, issue_id), issue_data[JsonKeys.ROOT_DIR.value], issue_data[JsonKeys.TARGETS.value], jar_path if os.path.exists(jar_path) else "", isJarMode)

    print(f"build command: {specimin_command}")
    start_time = time.time()
    result = run_specimin(issue_id ,specimin_command, specimin_path)   
    end_time = time.time()

    duration = round(end_time - start_time)

    global run_time
    run_time[f"{issue_id}"] = duration

    print(f"{result.name} - {result.status}")

    if result.status.lower() == "fail":
        result.set_preservation_status("FAIL", "Minimization did not succeed.")
        return result

    build_system = issue_data.get("build_system", "gradle")
    print(f"build used = {build_system}")
    if build_system == "gradle":
        # build.gradle and settings.gradle are shipped with input program. It exists in the "specimin" directory of the input program's root directory.
        # Copying both to the output directory of the minimized program.
        build_gradle_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "build.gradle")
        settings_gradle_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "settings.gradle")

        if not os.path.exists(build_gradle_path) or not os.path.exists(settings_gradle_path):
            print(f"{issue_id}: {build_gradle_path} or {settings_gradle_path} not found.")
            result.set_preservation_status("FAIL", "Build script missing") 
            return result
        
        if isJarMode:
            gradle_files_destination_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_jar_output, repo_name)
            #../ISSUES/cf-xx/jar_output/projectname/build_log.txt
            log_file = os.path.join(issue_folder_abs_dir, issue_id, specimin_jar_output, repo_name, minimized_program_build_log_file)
        else:
            gradle_files_destination_path = os.path.join(issue_folder_abs_dir, issue_id, specimin_output, repo_name)
            #../ISSUES/cf-xx/output/projectname/build_log.txt
            log_file = os.path.join(issue_folder_abs_dir, issue_id, specimin_output, repo_name, minimized_program_build_log_file)

        if isWindows():
            build_gradle_path = os.path.normpath(build_gradle_path)
            settings_gradle_path = os.path.normpath(settings_gradle_path)
            gradle_files_destination_path = os.path.normpath(gradle_files_destination_path)
            copy_command = f"copy {build_gradle_path} {gradle_files_destination_path}"
            subprocess.run(copy_command, shell=True)
            copy_command = f"copy {settings_gradle_path} {gradle_files_destination_path}"
            subprocess.run(copy_command, shell=True)
        else:
            copy_command = f"cp {build_gradle_path} {settings_gradle_path} {gradle_files_destination_path}"
            subprocess.run(copy_command, shell=True)

        if os.path.exists(log_file):
            os.remove(log_file)

        target_gradle_script = os.path.join(gradle_files_destination_path, "build.gradle")
        # Open the log file in write mode
        min_prgrm_build_status = None
        with open(log_file, "w") as log_file_obj:
            command = ""
            # avoid mixed slashes + convert \ to / for gradlew
            if isWindows():
                target_gradle_script = os.path.normpath(target_gradle_script).replace('\\', '/')
                command = "gradlew.bat"
            else:
                command = "./gradlew"
                
            command = f"{command} -b  {target_gradle_script} compileJava"

            min_prgrm_build_status = subprocess.run(command, cwd = specimin_path, shell=True, stderr=log_file_obj)
            print(f"{issue_id} Minimized program gradle build status = {min_prgrm_build_status.returncode}")
        if min_prgrm_build_status.returncode == 0:
            print(f"{issue_id} Minimized program gradle build successful. Expected: Fail")
            result.set_preservation_status("FAIL", "Min program is not reproducing issue with modular analyses")
            return result
    else:
        if build_system != "javac":
            cf_url = issue_data.get("cf_release_url", "")
            version = issue_data.get("cf_version", "1.9.13")
            cf_path = f"checker-framework-{version}"
            cf_abs_path = os.path.abspath(cf_path)
            cf_zip = f"{cf_abs_path}.zip"
            full_url = cf_url + "/" + cf_path + "/" + cf_path + ".zip"
            if not os.path.exists(cf_zip):
                download_with_wget_or_curl(full_url, cf_zip)

            if os.path.exists(cf_zip) and not os.path.exists(cf_abs_path):
                unzip_file(cf_zip)
        
        if isWindows():
            if build_system == "javac":
                jdk_template_url = "https://download.oracle.com/java/17/archive/jdk-{version}_{os}-{arch}_bin.zip"
            else:
                jdk_template_url = "https://corretto.aws/downloads/latest/amazon-corretto-{version}-{arch}-{os}-jdk.zip"
        else:
            if build_system == "javac":
                jdk_template_url = "https://download.oracle.com/java/17/archive/jdk-{version}_{os}-{arch}_bin.tar.gz"
            else:
                jdk_template_url = "https://corretto.aws/downloads/latest/amazon-corretto-{version}-{arch}-{os}-jdk.tar.gz"
        
        version = issue_data.get(JsonKeys.JAVA_VERSION.value, "11")
        #TODO: if version is not 8, no need to pull jdk
        arch = "x64"
        if platform.machine() == "arm64": #ignoring x86
            arch = "aarch64"
        platform_system = platform.system()
        op = ""  # use this variable to only form the jdk download url
        if platform_system == linux_system_identifier:
            op = "linux"
        elif platform_system == macos_system_identifier:
            op = "macos"
        elif platform_system == windows_system_identifier:
            op = "windows"
        else:
            result.set_preservation_status("FAIL", f"{platform_system} not supported")
            raise Exception(f"{platform_system} not supported")

        jdk_url = jdk_template_url.format(version=version, arch=arch, os=op)

        if build_system == "javac":
            jdk_name = f"jdk-{version}"
        else:
            jdk_name = f"amazon-corretto-{version}"
        
        if isWindows():
            jdk_file_name = f"{jdk_name}.zip"
        else:
            jdk_file_name = f"{jdk_name}.tar.gz"

        jdk_file_abs_path = os.path.abspath(jdk_file_name)

        if not os.path.exists(jdk_file_abs_path):
            download_with_wget_or_curl(jdk_url, jdk_file_abs_path)

        if platform_system == linux_system_identifier:
            extracted_jdk_abs_path = os.path.abspath(jdk_name) #/../amazon-corretto-8
        elif platform_system == macos_system_identifier:
            extracted_jdk_abs_path = os.path.abspath(jdk_name) + ".jdk" #//.//amazon-corretto-8.jdk
        elif platform_system == windows_system_identifier:
            extracted_jdk_abs_path = os.path.abspath(jdk_name) #C:\.\amazon-corretto-8
        else:
            raise Exception(f"{platform_system} not supported")
        
        if not os.path.exists(extracted_jdk_abs_path):
            os.makedirs(extracted_jdk_abs_path, exist_ok=True)
        if os.path.exists(extracted_jdk_abs_path):
            if build_system == "javac":
                if isWindows():
                    unzip_file(jdk_file_abs_path)
                else:
                    with tarfile.open(jdk_file_abs_path, "r:gz") as tar:
                        tar.extractall()
                set_directory_exec_permission(extracted_jdk_abs_path)
            else:
                if isWindows():
                    # Windows doesn't allow overwrite when renaming
                    if os.path.exists(extracted_jdk_abs_path):
                        shutil.rmtree(extracted_jdk_abs_path)
                extract_and_rename(jdk_file_abs_path, extracted_jdk_abs_path)
        # https://checkerframework.org/manual/#external-tools
        # using option 3 for CF invokation with downloaded jdk
        #Option 3: Whenever this document tells you to run javac, instead run checker.jar via java (not javac) as in:
        #java -jar "$CHECKERFRAMEWORK/checker/dist/checker.jar" -cp "myclasspath" -processor nullness MyFile.java
        if platform.system() == linux_system_identifier:
            if build_system == "javac":
                java_path = os.path.join(extracted_jdk_abs_path, "bin", "javac")
            else:
                java_path = os.path.join(extracted_jdk_abs_path, "bin", "java")
        elif platform.system() == macos_system_identifier:
            if build_system == "javac":
                java_path = os.path.join(extracted_jdk_abs_path, "Contents", "Home", "bin", "javac")
            else:
                java_path = os.path.join(extracted_jdk_abs_path, "Contents", "Home", "bin", "java")
        elif platform.system() == windows_system_identifier:
            if build_system == "javac":
                java_path = os.path.join(extracted_jdk_abs_path, "bin", "javac.exe")
            else:
                java_path = os.path.join(extracted_jdk_abs_path, "bin", "java.exe")
        else:
            raise Exception(f"{platform_system} not supported")

        if build_system != "javac":
            checker_jar_path = os.path.join(cf_abs_path, "checker", "dist", "checker.jar")
            set_directory_exec_permission(checker_jar_path)

        targets = issue_data.get("build_targets", "src/**/*.java")
        
        if isJarMode:
            target_dir = os.path.join(issue_folder_abs_dir, issue_id, specimin_jar_output, repo_name, targets)
            log_file = os.path.join(issue_folder_abs_dir, issue_id, specimin_jar_output, repo_name, minimized_program_build_log_file)
        else:
            target_dir = os.path.join(issue_folder_abs_dir, issue_id, specimin_output, repo_name, targets)
            log_file = os.path.join(issue_folder_abs_dir, issue_id, specimin_output, repo_name, minimized_program_build_log_file)
        
        set_directory_exec_permission(java_path)
        
        if os.path.exists(log_file):
            os.remove(log_file)

        file_paths = glob.glob(target_dir, recursive=True)
        if build_system == "javac":
            command = [java_path]
            command.extend([*file_paths])
            command_str = ' '.join(command)
            compiler_option = issue_data.get("compiler_option", "")
            ## generate a shell script and execute that
            print(f"{issue_id}: executing this command to check preservation status: {command_str}")
            ##
            if isWindows():
                shell_script = os.path.join(issue_folder_abs_dir, issue_id, specimin_jar_output if isJarMode else specimin_output, repo_name, "build.bat")
                shell_script = os.path.normpath(shell_script)
            else:
                shell_script = os.path.join(issue_folder_abs_dir, issue_id, specimin_jar_output if isJarMode else specimin_output, repo_name, "build.sh")
            with open(shell_script, 'w') as script:
                if isWindows():
                    script.write("@echo off\n")
                    # compiler_option is export ___="___", so we want to use set "___=___" instead
                    script.write(compiler_option.replace("\"", "", 1).replace("export", "set \"") + "\n")
                    script.write(command_str + "\n")
                else:
                    script.write("#!/bin/sh\n")
                    script.write(compiler_option + "\n")
                    script.write(command_str + "\n")
            with open(log_file, 'w') as f:
                if isWindows():
                    st = subprocess.run(shell_script, stderr=f)
                else:
                    st = subprocess.run(["bash", shell_script], stderr=f)
                if st.returncode == 0:
                    result.set_preservation_status("FAIL", "Min program is not showing issue with modular analyses")
                    return result
        else:
            flags = issue_data.get("build_flags", [])
            command = [java_path, '-jar', checker_jar_path]
            command.extend(flags)
            command.extend([*file_paths])
            command_str = ' '.join(command)
            print(f"{issue_id}: executing this command to check preservation status: {command_str}")
            try:
                execute_shell_command_with_logging(command, log_file)
            except Exception as e:
                print("Exception:", str(e))
                result.set_preservation_status("FAIL", "Min program is not showing issue with modular analyses")
                return result
        
    expected_log_file = os.path.join(issue_folder_abs_dir, issue_id, specimin_input, repo_name, specimin_project_name, "expected_log.txt")
    if not os.path.exists(expected_log_file):
        print(f"{issue_id}: {expected_log_file} do not exists")
        result.set_preservation_status("FAIL", "Expected log file missing")
        return result
    
    status = False
    if (JsonKeys.BUG_TYPE.value in issue_data and issue_data[JsonKeys.BUG_TYPE.value] == "crash"):
        require_stack = issue_data.get("require_stack", False)
        status = compare_crash_log(expected_log_file, log_file, require_stack)
    else:
        try:
            status = compare_pattern_data(expected_log_file, log_file, issue_data[JsonKeys.BUG_PATTERN.value])
        except ValueError as e:
            result.set_preservation_status("FAIL", f"{e}")
            return result
        
    result.set_preservation_status("PASS" if status else "FAIL", "" if status else f"log mismatched between target and min program")
    return result


def compare_pattern_data(expected_log_path, actual_log_path, bug_pattern_data):
    with open(expected_log_path, "r") as file:
        expected_log_file_content = file.read()

    with open(actual_log_path, "r") as file:
        actual_log_file_content = file.read()

    #Algorithm steps:
    #1.extract data from expected log file. One matched item should be there since only desired log information is in expected log file
    #2.extract data from build log file. Multiple matched items can be found. 
    #3.checked if item of st:2 is in items of st:3. if not there immediate return False. otherwise continue
    #4.return True at method end since no mismatch found.
    for key in bug_pattern_data:
        pattern = bug_pattern_data[key]
        expected_content = re.search(pattern, expected_log_file_content)
        if not expected_content: #TODO: this should trigger error. it indicates pattern error 
            raise ValueError(f"{pattern} not matched")  
        expected_content = expected_content.group(1) 
        actual_content = re.findall(pattern, actual_log_file_content)

        if key == "file_pattern":
            expected_content = os.path.basename(expected_content)
            actual_content = [os.path.basename(item) for item in actual_content]

        if expected_content in actual_content:
            continue
        else:
            return False

    return True


def get_exception_data(log_file: str, require_stack = False):
    '''
    Parse the exception data from the log file

    Returns:
        exception_data (ExceptionData): exception data
    '''

    with open(log_file, "r") as file:
        logs = file.read()

    lines_of_logs = logs.split('\n')

    return_data = []
    cf_crash_line = [line_no for line_no, line in enumerate(lines_of_logs) if line.lstrip().startswith('; The Checker Framework crashed.')]
    if len(cf_crash_line) == 0:
        print(f"No crash data in {log_file}")
        return []

    for line_no in cf_crash_line: # if multiple crash location found, one shoud match exactly with the expected crash information
        crashed_class_name_line = -1
        for i in range(line_no, line_no + 5): # should be immediate next line of crash line
            if lines_of_logs[i].strip().startswith("Compilation unit:"):
                crashed_class_name_line = i
                break
        if crashed_class_name_line == -1:
            continue  # start looking for next crash location
        class_name_abs_path = lines_of_logs[crashed_class_name_line].split(" ")[-1]
        crashed_class_name = os.path.basename(class_name_abs_path)

        exception_line = -1
        # + 10 is necessary for Windows; the error log has random empty lines which we should ignore
        for i in range(crashed_class_name_line, crashed_class_name_line + 10): # should be immediate next line of crash line
            if i >= len(lines_of_logs):
                break
            if lines_of_logs[i].strip().startswith("Exception:"):
                exception_line = i
                break
        exception_stack = [] #compare it with actual stack trace
        exception_line_str = lines_of_logs[exception_line] #Exception: java.lang.NullPointerException; java.lang.NullPointerException
        exception_line_sub_str = (exception_line_str[exception_line_str.index("Exception:") + 10:]).split()[0] # java.lang.NullPointerException; java.lang.NullPointerException
        exception_cause = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', exception_line_sub_str) # java.lang.NullPointerException
        
        if not require_stack and crashed_class_name and exception_cause: # if stack is not required, not adding them in exception data. 
            exception_data = ExceptionData(crashed_class_name, exception_cause)
            return_data.append(exception_data)
            continue
        
        for i in range(exception_line + 1, exception_line + 6):
            if lines_of_logs[i].lstrip().startswith("at"):
                exception_stack.append(lines_of_logs[i].split()[-1].strip())
        
        if crashed_class_name and exception_cause and len(exception_stack) > 0:
            exception_data = ExceptionData(crashed_class_name, exception_cause, exception_stack)
            return_data.append(exception_data)

    return return_data

def compare_crash_log(expected_log_path, actual_log_path, require_stack = True):
    '''
    Compare the crash log of the minimized program with the expected crash log
    '''

    expected_crash_datas = get_exception_data(expected_log_path, require_stack) # there should be 1 crash data
    actual_crash_data = get_exception_data(actual_log_path, require_stack)

    if not expected_crash_datas:
        raise ValueError(f"{expected_log_path} invalid. No crash data") # no crash data found in the expected log file
    
    expected_crash_data = expected_crash_datas[0]
        
    for data in actual_crash_data:
        if require_stack:
            if (expected_crash_data.exception == data.exception and
                expected_crash_data.exception_class == data.exception_class and
                expected_crash_data.stack_trace == data.stack_trace):
                return True
        else:
            if (expected_crash_data.exception == data.exception and
                expected_crash_data.exception_class == data.exception_class):
                return True
    return False

def isWindows():
    op_sys = platform.system()
    return op_sys == windows_system_identifier


def main():
    '''
    Main method of the script. It iterates over the json data and perform minimization for each cases.   
    '''
    op_sys = platform.system()
    if op_sys != linux_system_identifier and op_sys != macos_system_identifier and op_sys != windows_system_identifier:
        print(f"{op_sys} no supported")
        sys.exit(1)

    os.makedirs(issue_folder_dir, exist_ok=True)   # create the issue holder directory
    specimin_path = get_specimin_env_var()
    if specimin_path is not None and os.path.exists(specimin_path) and os.path.isdir(specimin_path):
        print("Local Specimin copy is being used")
    else:
        print("Local Specimin not found. Cloning a Specimin copy")
        clone_specimin(issue_folder_dir, specimin_source_url)

    parser = argparse.ArgumentParser(description='command line parser')
    parser.add_argument('-j', '--isJarMode', type=bool, help='pass "true" if jar mode execution')
    parser.add_argument('--debug', type=str, help='python main.py --debug #issue to run only that target')
    args = parser.parse_args()

    json_file_path = os.path.join("resources", "test_data.json")
    parsed_data = read_json_from_file(json_file_path)
    
    isJar = args.isJarMode
    debug_target = args.debug
    print("execution mode Jar = ", isJar)
    
    evaluation_results = []
    json_status: dict[str, str] = {} # Contains PASS/FAIL status of targets to be printed as a json file 
    preservation_status: dict[str, str] = {}
    if parsed_data:
        for issue in parsed_data:
            issue_id = issue["issue_id"]
            if debug_target and issue_id != debug_target:
                continue
            print(f"{issue_id} execution starts =========>")
            try:
                result = performEvaluation(issue, isJar)
            except Exception as e:
                print(f"Exception: {e}")
                print("Aborting execution")
                sys.exit(1)
            evaluation_results.append(result)
            json_status[issue_id] = result.status
            preservation_status[issue_id] = result.preservation_status
            print((f"{issue_id} <========= execution Ends."))            

    report_generator: TableGenerator = TableGenerator(evaluation_results)
    report_generator.generateTable()

    if isJar:
        json_status_file = os.path.join(issue_folder_dir, "jar_target_status.json")
        prev_status_file = os.path.join(issue_folder_dir, "jar_preservation_status.json")
    else:
        json_status_file = os.path.join(issue_folder_dir, json_status_file_name)
        prev_status_file = os.path.join(issue_folder_dir, preservation_status_file_name)
    # Write JSON data in a file. This can be compared from specimin to verify that the successful # of targets do not get reduced in a PR
    with open(json_status_file, "w") as json_file:
        json.dump(json_status, json_file, indent= 2)
    with open(prev_status_file, "w") as json_file:
        json.dump(preservation_status, json_file, indent= 2)

    global run_time
    print(json.dumps(run_time))
    mean_runtime = statistics.mean(list(run_time.values()))
    mean_runtime = round(mean_runtime)
    print(f"Avg runtime = {mean_runtime}")

    print("\n\n\n\n")
    print(f"issue_name    |    status    |  Fail reason  | preservation_status | preservation reason ")
    print("------------------------------------------------------------------------------------------")
    case = 1
    for minimization_result in evaluation_results:
        print(f"({case}){minimization_result.name}    |    {minimization_result.status}     |    {minimization_result.reason}            | {minimization_result.preservation_status}           |   {minimization_result.preservation_status_reason}")
        case +=1

    

    

if __name__ == "__main__":
    main()
