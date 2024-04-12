import os
from main import read_json_from_file
from main import get_repository_name
import json
import subprocess
def main():
    json_file_path = os.path.join("resources", "test_data.json")
    parsed_data = read_json_from_file(json_file_path)

    code_count = {}

    if parsed_data:
        for issue in parsed_data:
            issue_id = issue["issue_id"]
            url = issue["url"]
            repo_name = get_repository_name(url)

            # get hand min program loc
            hand_code_line = 0
            specimin_code_line = 0
            hand_min_program_path = os.path.join("ISSUES", issue_id, "input", repo_name, "specimin", "test")
            if os.path.exists(hand_min_program_path):
                output = subprocess.check_output(["scc", "-f", "json"], cwd=hand_min_program_path)
                data = json.loads(output) # this is array of dictionary
                for item in data:
                     if item.get("Name") == "Java":   # checking only java line code
                         hand_code_line += item.get("Code")
            else:
                print(f"Test code not available for {issue_id}")

            # get specimin min program loc
            specimin_min_program_path = os.path.join("ISSUES", issue_id, "output", repo_name, "src")
            if os.path.exists(specimin_min_program_path):
                output = subprocess.check_output(["scc", "-f", "json"], cwd=specimin_min_program_path)
                data = json.loads(output) # this is array of dictionary
                for item in data:
                     if item.get("Name") == "Java":   # checking only java line code
                         specimin_code_line += item.get("Code")
            else:
                print(f"Minimization was failed/ not executed {issue_id}")
            
            combined_code_info = {"test": hand_code_line, "specimin": specimin_code_line}
            code_count[issue_id] = combined_code_info


    pretty_json = json.dumps(code_count, indent=4)
    print(pretty_json)


if __name__ == "__main__":
    main()