#!/bin/bash

function stop()
{
    echo 0 > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/run
    echo 0 > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/run
}

function drive()
{
    echo on > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/regulation_mode
    echo on > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/regulation_mode
    echo "${1}" > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/pulses_per_second_sp
    echo "${1}" > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/pulses_per_second_sp
    echo 1 > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/run
    echo 1 > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/run
}

function turn-left()
{
    echo on > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/regulation_mode
    echo on > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/regulation_mode
    echo -500 > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/pulses_per_second_sp
    echo 500 > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/pulses_per_second_sp
    echo 1 > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/run
    echo 1 > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/run
}

function turn-right()
{
    echo on > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/regulation_mode
    echo on > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/regulation_mode
    echo 500 > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/pulses_per_second_sp
    echo -500 > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/pulses_per_second_sp
    echo 1 > /sys/bus/legoev3/devices/outA/outA:motor/tacho-motor/tacho-motor0/run
    echo 1 > /sys/bus/legoev3/devices/outD/outD:motor/tacho-motor/tacho-motor2/run

}

function cleanup()
{
    stop
    exit 0
}

trap "cleanup" SIGINT SIGTERM SIGHUP

while true; do
    read -n 1 CMD
    echo

    case "${CMD}" in
        'w' ) drive -700 ;;
        's' ) drive 700 ;;
        'a' ) turn-left ;;
        'd' ) turn-right ;;
        'q' ) stop ;;
        'e' ) cleanup ;;
        *   ) echo 'Invalid command' ;;
    esac
done

stop
