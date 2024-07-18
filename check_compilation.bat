@echo off

rem .bat port of check_compilation.sh

rem This script runs javac on all of the minimized outputs under ISSUES/ .
rem It returns 2 if any of them fail to compile, 1 if there are any malformed directories,
rem and 0 if all of them do compile.

rem It is desirable that all of the expected Specimin's minimized program gets compiled, because Specimin
rem should produce independently-compilable programs.

rem when this script is invoked from specimin CI, 
rem compilation result will be compared with "expected" result and CI will be passed/failed accordingly.

rem usage: shell check_compilation.sh 1 --> for approximate mode
rem or
rem usage: shell check_compilation.sh 2 --> for exact/jar mode

setlocal enabledelayedexpansion

set param="%1"

if !param!=="1" (
   set min_program_dir=output
   set status_file=compile_status.json
) else (
   if !param!=="2" (
      set min_program_dir=jar_output
      set status_file=jar_compile_status.json
   ) else (
      echo Invalid parameter 
      exit /b 1
   )
)

set returnval=0
set compile_status_json=^{
echo Specimin path: %SPECIMIN%

set issue_ids=

rem read all issue_idjson from json file
rem Use Powershell to extract the issue_ids and store them in a variable
rem No jq so we need to use Powershell
for /f "delims=" %%i in ('powershell -command ^
   "Get-Content -Raw -Path 'resources/test_data.json' | ConvertFrom-Json | ForEach-Object { $_.issue_id }"') do (
   set "issue_ids=!issue_ids!;%%i"
)


cd ISSUES || exit /b 1

set issues_root=%cd%
rem see https://stackoverflow.com/questions/3572291/assigning-newline-character-to-a-variable-in-a-batch-script
set LF=^


rem TWO empty lines are required

for %%t in (!issue_ids!) do (
   set testcase=%%t
   echo Target = !testcase!
   
   set continue=0

   if "!testcase!"=="jdk-8319461" set continue=1

   if !continue!==0 (
      cd !testcase!
      if !errorlevel!==1 (
         rem Due to how the specimin CI runs (choosing only a few test cases to run), we should
         rem ignore test cases which were not run
         echo !testcase! not found. Ignoring it.
         set continue=1
      )
   )

   if !continue!==0 (
      cd !min_program_dir!\
      if !errorlevel!==1 (
         set compile_status_json=!compile_status_json!^!LF!  "!testcase!": "FAIL",
         set continue=1
      )
   )

   if !continue!==0 (
      rem check if any directory exists inside output. If no directory there, specimin failed on the input target
      rem in that case, ignoring it.
      set directory_exists=0
      for /d %%d in (*) do (
         set directory_exists=1
      )

      if !directory_exists!==0 ( 
         echo No directories inside !testcase!/output. Ignoring it.
         set compile_status_json=!compile_status_json!^!LF!  "!testcase!": "FAIL",
         cd "!issues_root!"
         set continue=1
      )
   )

   if !continue!==0 (
      set JAVA_FILES=
      for /r %%F in (*.java) do (
         set "JAVA_FILES=!JAVA_FILES! %%F"
      )
      javac -classpath "%SPECIMIN%\src\test\resources\shared\checker-qual-3.42.0.jar" !JAVA_FILES!
      set javac_status=!errorlevel!
      if !javac_status!==0 ( 
         echo Running javac on !testcase!/output PASSES
         set compile_status_json=!compile_status_json!^!LF!  "!testcase!": "PASS",
      ) else (
         echo Running javac on !testcase!/output FAILS. Please check logs above.
         set compile_status_json=!compile_status_json!^!LF!  "!testcase!": "FAIL",
         set returnval=2
      )
   )
   cd !issues_root! || exit /b 1
)

if "!compile_status_json:~-1!"=="," set compile_status_json=!compile_status_json:~0,-1!

set compile_status_json=!compile_status_json!^!LF!^}

echo !compile_status_json!

if !returnval!==0 echo All expected test outputs compiled successfully.
if !returnval!==2 echo Some expected test outputs do not compile successfully. See the above error output for details.

del "!status_file!"
echo !compile_status_json! > "!status_file!"

for /r %%F in (*.class) do (
   del "\\?\%%F"
)

exit /b !returnval!