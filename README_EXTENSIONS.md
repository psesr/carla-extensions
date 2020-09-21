# Build

## Overview

In general, the build instructions on the official Carla documentation website are followed:

- For Linux: [https://carla.readthedocs.io/en/latest/build_linux/](https://carla.readthedocs.io/en/latest/build_linux/)
- For Windows: [https://carla.readthedocs.io/en/latest/build_windows/](https://carla.readthedocs.io/en/latest/build_windows/)

If you encounter problems when building Carla, we listed some problems we encountered in the troubleshooting section at the end of this document.

We recommend to have a look at the Carla build system overview [here](https://carla.readthedocs.io/en/latest/build_system/).

After you built Carla (`make launch` or `make LibCarla`) and the Python API (`make PythonAPI`), you will find the build in the Dist folder.
At this stage you can also build the package (`make package`), which is not really necessary during development.

## Running the simulator

Under `Dist/CARLA_Shipping[...]-dirty/LinuxNoEditor` you will find `CarlaUE4.sh` for starting the simulator.

## Installing the Python API

We recommend to create a new conda environment for testing the carla extensions.

After an API build (`make PythonAPI`), we recommend to first remove the old API and
to install the new one in the environment as described [here](https://carla.readthedocs.io/en/latest/build_system/#pythonapi):

```
pip uninstall carla
cd PythonAPI/carla/dist
python3 -m easy_install --no-deps PythonAPI/carla/dist/carla-X.X.X-py3.7-linux-x86_64.egg
```

# Troubleshooting

## Build Issues

#### Boost Include Errors

During `make launch`, the following include error may appear:

```
fatal error: 'boost/asio/buffer.hpp' file not found
```

Fix:

- `cd` to `Build`
- Remove all files related to boost:
    - There is probably three of them `boost-1.72.0-c7-source`, `boost-1.72.0-c7-install` and an archive file
- Source: [https://github.com/carla-simulator/carla/issues/2526](https://github.com/carla-simulator/carla/issues/2526) 


## Simulator Issues

#### Segmentation Fault when running with -opengl flag

This happens for example when a camera listener is added to a sensor.
It might be related to available GPU memory.
This behavior can be reproduced by using the `-opengl` flag and running the example `automatic_control.py`.

Simulator console output:

```
Signal 11 caught.
Malloc Size=65538 LargeMemoryPoolOffset=65554 
CommonUnixCrashHandler: Signal=11
Malloc Size=65535 LargeMemoryPoolOffset=131119 
Malloc Size=114736 LargeMemoryPoolOffset=245872 
Engine crash handling finished; re-raising signal 11 for the default handler. Good bye.
Segmentation fault (core dumped)
```

Workarounds:

- Run without the `-opengl` flag. This requires more computation resources.
- Another workaround is to reduce GPU memory consumption. This can be achieved in the following ways:
    - Reduce size of the carla main window by resizing it manually.
    - Reduce size of the carla main window at launch, e.g. `DISPLAY= ./CarlaUE4.sh  -opengl -windowed -ResX=400 -ResY=300`.
    - Starting carla in off-screen mode, i.e. `DISPLAY= ./CarlaUE4.sh`


