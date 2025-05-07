# Lego Mindstorms Dalek

Code for a Lego Mindstorms [Dalek](https://en.wikipedia.org/wiki/Dalek), from [Doctor Who](https://en.wikipedia.org/wiki/Doctor_Who), using the Mindstorms EV3 brick running [ev3dev](http://www.ev3dev.org/).

[Video!](http://www.youtube.com/watch?v=Li0pRmRHNx0)

![Dalek with normal eye-stalk](dalek1.jpg)

With a Logitech C270 webcam:

![Dalek with webcam](dalek2.jpg)

Taking a selfie in the mirror:

![Dalek mirror selfie](dalek3.jpg)

## Installation

1. Install ev3dev Stretch using [these instructions](https://www.ev3dev.org/docs/getting-started/), including the steps to set up SSH and update apt.

2. The following commands use a local copy of the SD card for the rest of the installation; this is much faster than running on the EV3:

    a. Plug the SD card into the computer, and find its device name, typically `/dev/sda`, `/dev/sdb`, etc. Assuming `/dev/sda`, run:

    ```shell
    sudo umount /dev/sda1
    sudo umount /dev/sda2
    sudo dd bs=4M if=/dev/sda of=dalek.img
    sudo chown "$(id -u):$(id -g)" dalek.img
    ```

    b. Remove the SD card.

    c. Ensure qemu is installed; assuming Ubuntu 24.04, run:

    ```shell
    sudo apt-get install qemu-user-static
    ```

    d. Chroot into the image:

    ```shell
    mkdir dalek
    sudo losetup -P /dev/loop0 dalek.img
    sudo mount /dev/loop0p2 dalek
    sudo systemd-nspawn -D dalek --resolv-conf=bind-host --user=1000
    ```

    e. Inside the image, run:

    ```shell
    git clone https://github.com/calliecameron/lego-mindstorms-dalek
    ./lego-mindstorms-dalek/utils/setup_ev3.sh
    ./lego-mindstorms-dalek/utils/install_dependencies.sh
    exit
    ```

    f. Unmount the image:

    ```shell
    sudo umount dalek
    sudo losetup -d /dev/loop0
    ```

    g. Write the image back to the SD card using the same tool used to install ev3dev.

## Usage

1. Make sure the Dalek and the computer are on the same WiFi network.
2. Select `lego-mindstorms-dalek/run.sh` from the brick's file browser (or you can run it through SSH).
3. Find the Dalek's IP address (displayed on the brick), and in your browser go to port 12345. E.g. if the Dalek is 192.168.0.2, the address you want is `http://192.168.0.2:12345`.

## Credits

- Overlay image from http://chriscastielredy.deviantart.com/art/Doctor-Who-Dalek-Vision-515731932
- Dalek icon from http://www.veryicon.com/icons/movie--tv/doctor-who/dalek.html
