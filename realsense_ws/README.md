# realsense_ws (source only)

Source build of librealsense v2.58.4 + realsense-ros 4.58.4 with the RSUSB backend, because the apt
librealsense cannot read the D435i IMU on this Jetson kernel (no hid_sensor modules).
build/ and install/ are not stored here (380 MB); rebuild on the car with:

    cd ~/realsense_ws && source /opt/ros/jazzy/setup.bash
    colcon build --cmake-args -DFORCE_RSUSB_BACKEND=ON -DBUILD_EXAMPLES=OFF -DBUILD_GRAPHICAL_EXAMPLES=OFF \
        -DBUILD_PYTHON_BINDINGS=ON -DPYTHON_EXECUTABLE=/usr/bin/python3 \
        -DPYTHON_INSTALL_DIR=/home/nvidia/realsense_ws/install/librealsense2/lib/python3.12/dist-packages \
        -DCMAKE_BUILD_TYPE=Release
    sudo cp src/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/ && sudo udevadm control --reload-rules && sudo udevadm trigger

Camera firmware was updated to 5.16.0.1 and the IMU calibrated with tools/rs-imu-calibration on 2026-11-15.
