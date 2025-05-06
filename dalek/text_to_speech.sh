#!/bin/bash
# Espeak on ev3dev is a bit temperamental, and this is easier than messing with pipes in python

espeak -a 200 -s 120 --stdout "${1}" | aplay
