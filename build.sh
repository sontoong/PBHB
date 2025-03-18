#!/bin/bash

# Clean up old build/dist files
echo "Cleaning up old build, dist, and spec files..."
rm -rf build dist *.spec

# Determine OS and adjust add-data flag separator
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    ADD_DATA_FLAG="bh_bot/images:images"
else
    ADD_DATA_FLAG="bh_bot/images;images"
fi

# Build the executable using PyInstaller with images folder
echo "Building executable..."
# pyinstaller --clean --onefile --noconsole --name "Bit Heroes Bot" --add-data "$ADD_DATA_FLAG" bh_bot/__main__.py
pyinstaller --clean --onedir --hide-console "minimize-early" --name "PBHB" --add-data "$ADD_DATA_FLAG" bh_bot/__main__.py

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "Build successful!"
else
    echo "Build failed!"
fi

# Pause to keep the terminal open and view the error message
echo "Press any key to exit..."
read -n 1 -s