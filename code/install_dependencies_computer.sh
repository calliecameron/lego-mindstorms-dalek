#!/bin/bash
# Run this script once on the computer you will use to control the Dalek; it
# installs all the necessary software.

sudo apt-get -y install python-pygame zenity
easy_install --user pillow
