import os
from main import read_json_from_file
from main import get_repository_name
import json
import subprocess

'''
This script depends on scc tool: https://github.com/boyter/scc
'''

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

    total_specimin_line = 0
    total_hand_written_line = 0
    for key in code_count:
        total_specimin_line += code_count.get(key).get("specimin")
        total_hand_written_line += code_count.get(key).get("test")

    sp_avg = round(total_specimin_line/19)
    hand_avg = round(total_hand_written_line/18)
    print(f"sp_avg: {sp_avg}")
    print(f"hand_avg: {hand_avg}")


if __name__ == "__main__":
    main()