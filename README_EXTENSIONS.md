# Build

## Overview

In general, the build instructions on the official Carla documentation website are followed:

- For Linux: [https://carla.readthedocs.io/en/latest/build_linux/](https://carla.readthedocs.io/en/latest/build_linux/)
- For Windows: [https://carla.readthedocs.io/en/latest/build_windows/](https://carla.readthedocs.io/en/latest/build_windows/)

If you encounter problems when building Carla, we listed some problems we encountered in the troubleshooting section at the end of this document.

We recommend to have a look at the Carla build system overview [here](https://carla.readthedocs.io/en/latest/build_system/).

# Troubleshooting

## Build

After you built Carla (`make launch`) and the Python API (`make PythonAPI`), you will find the build in the Dist folder.
At this stage you can also build the package (`make package`), which is not really necessary during development.

### Running the simulator

Under `Dist/CARLA_Shipping[...]-dirty/LinuxNoEditor` you will find `CarlaUE4.sh` for starting the simulator.

### Installing the Python API

We recommend to create a new conda environment for testing the carla extensions.
After an API build (`make PythonAPI`), we recommend to update the Python API in the environment as follows:

```
pip uninstall carla
cd PythonAPI/carla/dist
python3 -m easy_install carla[...].egg
```

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

