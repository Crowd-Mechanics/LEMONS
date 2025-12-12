# How to run ```CrowdMechanics```

We'll show here how to run the crowd simulation from Python or C++, assuming the XML input files have already been prepared (see [`use_mechanical_layer.md`](./use_mechanical_layer.md)).

## Python

The code for the Mechanical Layer has been written to be easily usable with the Python ctypes library, which we find the most easy to use, and that has the advantage of being installed by default with Python.

The following minimal code is sufficient to call the simulation, assuming we run it from the root directory of the library:

```python
import ctypes

## Load the shared library into ctypes
c_lib = ctypes.CDLL(r'path/to/libCrowdMechanics.so')         # Linux
# c_lib = ctypes.CDLL(r'path/to/libCrowdMechanics.dylib')    # macOS
# c_lib = ctypes.CDLL(r'path/to/libCrowdMechanics.dll')      # Windows

## Input of the CrowdMechanics main function
files = [b"/AbsolutePath/Parameters.xml",
         b"Materials.xml",
         b"Geometry.xml",
         b"Agents.xml",
         b"AgentDynamics.xml"]
## Convert the files variable to something ctypes will understand
nFiles = len(files)
filesInput = (ctypes.c_char_p * nFiles)()
filesInput[:] = files

## The following two lines are optional, they tell ctypes
## what is the type of the input and output variables
# c_lib.CrowdMechanics.argtypes = [ctypes.POINTER(ctypes.c_char_p * nFiles)]
# c_lib.CrowdMechanics.restype = ctypes.c_int

## The actual call to the library -- Always check the return code!
if c_lib.CrowdMechanics(filesInput) != 0:
    print("Crowd mechanics engine failed!")
    exit(0)
```

## C++

Assuming you have built ```CrowdMechanics``` as a shared library as intended, the following minimal code will run the simulation:

```c++
//  Include the main header of the library
#include "CrowdMechanics.h"

int main(void)
{
    char* files[5] =
        {"/AbsolutePath/Parameters.xml",
         "Materials.xml",
         "Geometry.xml",
         "Agents.xml",
         "AgentDynamics.xml"};
    //  Call the library
    CrowdMechanics(files);

    return 0;
}
```
In order to compile this code, the include paths should be mentioned, either explicitly (```-I```) or in environment variables. The path to the library should be mentioned as well (```-L```). An example, assuming compilation from the root directory of ```CrowdMechanics```:
```bash
g++ -Iinclude -I3rdparty/tinyxml -o test test.cpp -Lbuild -lCrowdMechanics
```
In order for the linking to work when executing, the path to the library should also be mentioned in an environment variable (ie ```LD_LIBRARY_PATH``` on MacOsX and Linux).
