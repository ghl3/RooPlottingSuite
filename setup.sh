# The SETUP file for this Plotting Package
# Simply add this directory to the 
# PythonPath

#DIR="$( cd "$( dirname "$0" )" && pwd )"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PATH=${DIR}:${PATH}
export PYTHONPATH=${DIR}:${PYTHONPATH}