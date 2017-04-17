Dalek Code
==========

On the Dalek
------------

Install [ev3dev](http://www.ev3dev.org/) using the instructions on their site, and make sure you can SSH into the brick. To set up the code, in a terminal on the brick run:

    sudo apt-get -y install git
    git clone https://github.com/CallumCameron/lego-mindstorms-dalek
    cd lego-mindstorms-dalek/code
    ./install_dependencies.sh

Make sure the Dalek and the computer are on the same WiFi network.

To run the code, select `lego-mindstorms-dalek/code/run.sh` from the brick's file browser (or you can run it through SSH).


In your browser
---------------

Find the Dalek's IP address (displayed on the brick), and go to port 12345. E.g. if the Dalek is 192.168.0.2, the address you want is `http://192.168.0.2:12345`.


Credits
-------

- Overlay image from http://chriscastielredy.deviantart.com/art/Doctor-Who-Dalek-Vision-515731932
- Dalek icon from http://www.veryicon.com/icons/movie--tv/doctor-who/dalek.html
