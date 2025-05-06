# Lego Mindstorms Dalek

Code for a Lego Mindstorms [Dalek](https://en.wikipedia.org/wiki/Dalek), from [Doctor Who](https://en.wikipedia.org/wiki/Doctor_Who), using the Mindstorms EV3 brick running [ev3dev](http://www.ev3dev.org/).

[Video!](http://www.youtube.com/watch?v=Li0pRmRHNx0)

![Dalek with normal eye-stalk](dalek1.jpg)

With a Logitech C270 webcam:

![Dalek with webcam](dalek2.jpg)

Taking a selfie in the mirror:

![Dalek mirror selfie](dalek3.jpg)

## Installation

Install [ev3dev](http://www.ev3dev.org/) Stretch using the instructions on their site, and make sure you can SSH into the brick. To set up the code, in a shell on the brick run:

```shell
sudo apt-get -y install git
git clone https://github.com/calliecameron/lego-mindstorms-dalek
cd lego-mindstorms-dalek
./install_dependencies.sh
```

Alternatively, mount the brick's SD card on your computer and run the commands inside a chroot using `sudo systemd-nspawn -D $PATH_TO_EV3DEV_ROOTFS --chdir=/ --resolv-conf=bind-host` - this will be faster than running on the brick, and you don't have to worry about the batteries going flat. You may have to install `qemu-user-static` or equivalent for this to work.

## Usage

1. Make sure the Dalek and the computer are on the same WiFi network.
2. Select `lego-mindstorms-dalek/run.sh` from the brick's file browser (or you can run it through SSH).
3. Find the Dalek's IP address (displayed on the brick), and in your browser go to port 12345. E.g. if the Dalek is 192.168.0.2, the address you want is `http://192.168.0.2:12345`.

## Credits

- Overlay image from http://chriscastielredy.deviantart.com/art/Doctor-Who-Dalek-Vision-515731932
- Dalek icon from http://www.veryicon.com/icons/movie--tv/doctor-who/dalek.html
