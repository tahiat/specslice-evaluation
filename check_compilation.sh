#!/bin/sh

# This script runs javac on all of the expected test outputs under src/test/resources.
# It returns 2 if any of them fail to compile, 1 if there are any malformed test directories,
# and 0 if all of them do compile.
#
# It is desirable that all of the expected test outputs compile, because Specimin
# should produce independently-compilable programs.

returnval=0

cd ISSUES || exit 1
for target in * ; do
    echo "Target = ${target}"
    if [ "${target}" = "output.html" ] || [ "${target}" = "target_status.json" ] ||  [ "${target}" = "specimin" ]; then 
        continue; 
    fi

    cd "${target}/output/" || exit 1
    # check if any directory exists inside output. If no directory there, specimin failed on the input target
    # in that case, ignoring it.
    directory_count="$(find ./ -mindepth 1 -type d | wc -l)"
    if [ "$directory_count" -eq 0 ]; then 
        echo "No directories inside ${target}/output. Ignoring it."
        cd ../..
        continue
    fi

    echo "Running javac on ${target}/output"
    # javac relies on word splitting
    # shellcheck disable=SC2046
    javac -classpath "../../../resources/checker-qual-3.42.0.jar" $(find . -name "*.java") \
      || { echo "Running javac on ${target}/expected issues one or more errors, which are printed above."; returnval=2; }
    cd ../.. || exit 1
done

if [ "${returnval}" = 0 ]; then
  echo "All expected test outputs compiled successfully."
elif [ "${returnval}" = 2 ]; then
  echo "Some expected test outputs do not compile successfully. See the above error output for details."
fi

find . -name "*.class" -exec rm {} \;

exit ${returnval}
