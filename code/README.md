Dalek Code
==========

On the Dalek
------------

Install [ev3dev](http://www.ev3dev.org/) using the instructions on their site, and make sure you can SSH into the brick. To set up the code, in a terminal on the brick run:

    sudo apt-get -y install git
    git clone https://github.com/CallumCameron/lego-mindstorms-dalek
    cd lego-mindstorms-dalek/code
    ./install_dependencies_dalek.sh

Make sure the Dalek and the computer are on the same WiFi network.

To run the code, select `lego-mindstorms-dalek/code/run_on_dalek.sh` from the brick's file browser (or you can run it through SSH).


On your computer
----------------

This assumes you are running Ubuntu 14.04, Mint 17, or a similar Linux distribution (only tested on Mint 17).

In a terminal, run:

    sudo apt-get -y install git
    git clone https://github.com/CallumCameron/lego-mindstorms-dalek
    cd lego-mindstorms-dalek/code
    ./install_dependencies_computer.sh
    ./create_desktop_shortcut.sh

To run the code, either use the desktop icon, or run `lego-mindtstorms-dalek/code/run_on_computer.sh` in a terminal. The code on the Dalek must already be running. You will need to enter the Dalek's IP address; this can be found on the brick.


Credits
-------

- Overlay image from http://chriscastielredy.deviantart.com/art/Doctor-Who-Dalek-Vision-515731932
- Dalek icon from http://www.veryicon.com/icons/movie--tv/doctor-who/dalek.html
