#!/bin/sh

# This script runs javac on all of the minimized outputs under ISSUES/ .
# It returns 2 if any of them fail to compile, 1 if there are any malformed directories,
# and 0 if all of them do compile.
#
# It is desirable that all of the expected Specimin's minimized program gets compiled, because Specimin
# should produce independently-compilable programs.

# when this script is invoked from specimin CI, 
# compilation result will be compared with "expected" result and CI will be passed/failed accordingly.

# usage: shell check_compilation.sh 1 --> for approximate mode
# or
# usage: shell check_compilation.sh 2 --> for exact/jar mode

param="$1"

if [ $param -eq 1 ]; then
   min_program_dir="output"
   status_file="compile_status.json"
elif [ $param -eq 2 ]; then
   min_program_dir="jar_output"
   status_file="jar_compile_status.json"
else
   echo "Invalid parameter"
   exit 1
fi

returnval=0
compile_status_json="{"
echo "Specimin path: $SPECIMIN"

#read all issue_idjson from json file
issue_ids="$(jq -r '.[].issue_id' resources/test_data.json)"
cd ISSUES || exit 1

issues_root=`pwd`

for target in $issue_ids; do
    echo "Target = ${target}"
    
   if [ "$target" = "jdk-8319461" ]; then continue; fi

    cd "${target}/${min_program_dir}/"
    if [ $? -eq 1 ]; then
      compile_status_json="$compile_status_json\n  \"$target\": \"FAIL\","
      continue
    fi
    # check if any directory exists inside output. If no directory there, specimin failed on the input target
    # in that case, ignoring it.
    directory_count="$(find ./ -mindepth 1 -type d | wc -l)"
    if [ "$directory_count" -eq 0 ]; then 
        echo "No directories inside ${target}/output. Ignoring it."
        compile_status_json="$compile_status_json\n  \"$target\": \"FAIL\","
        cd "${issues_root}"
        continue
    fi

    # javac relies on word splitting
    # shellcheck disable=SC2046
    javac -classpath "$SPECIMIN/src/test/resources/shared/checker-qual-3.42.0.jar" $(find . -name "*.java")
    javac_status=$?
    if [ $javac_status -eq 0 ]; then 
       echo "Running javac on ${target}/output PASSES"
       compile_status_json="$compile_status_json\n  \"$target\": \"PASS\","
    else
        echo "Running javac on ${target}/output FAILS. Please check logs above."
        compile_status_json="$compile_status_json\n  \"$target\": \"FAIL\","
        returnval=2
    fi
    cd "${issues_root}" || exit 1

done

if [ "${returnval}" = 0 ]; then
  echo "All expected test outputs compiled successfully."
elif [ "${returnval}" = 2 ]; then
  echo "Some expected test outputs do not compile successfully. See the above error output for details."
fi

compile_status_json="${compile_status_json%,}"
compile_status_json="$compile_status_json\n}"
rm "$status_file"
echo "$compile_status_json" > "$status_file"
find . -name "*.class" -exec rm {} \;
