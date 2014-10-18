#!/usr/bin/env python
"""Use this script to control the Dalek remotely. This is the script
you run on the controlling machine; run remote_receiver.py on the
Dalek itself."""


import argparse
import sys
import pygame
import time
from dalek_network import Controller, DRIVE, TURN

parser = argparse.ArgumentParser(description="Control the Dalek remotely from another machine")
parser.add_argument("addr", help="Address of the Dalek")

args = parser.parse_args()

pygame.init()
screen = pygame.display.set_mode((320, 240))
font = pygame.font.Font(None, 40)
text = ""
controller = Controller(args.addr)

repeat_command = None
next_repeat = 0

def begin_cmd(cmd, value):
    global repeat_command
    controller.begin_cmd(cmd, value)
    def action():
        controller.begin_cmd(cmd, value)
    repeat_command = action

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            text = "down: " + pygame.key.name(event.key)
            if event.key == pygame.K_w:
                begin_cmd(DRIVE, 1.0)
            elif event.key == pygame.K_s:
                begin_cmd(DRIVE, -1.0)
            elif event.key == pygame.K_a:
                begin_cmd(TURN, 1.0)
            elif event.key == pygame.K_d:
                begin_cmd(TURN, -1.0)
        elif event.type == pygame.KEYUP:
            text = "up: " + pygame.key.name(event.key)
            if event.key == pygame.K_w:
                controller.release_cmd(DRIVE, 1.0)
                repeat_command = None
            elif event.key == pygame.K_s:
                controller.release_cmd(DRIVE, -1.0)
                repeat_command = None
            elif event.key == pygame.K_a:
                controller.release_cmd(TURN, 1.0)
                repeat_command = None
            elif event.key == pygame.K_d:
                controller.release_cmd(TURN, -1.0)
                repeat_command = None


    screen.fill((255, 255, 255))
    disp = font.render(text, True, (0, 0, 0))
    rect = disp.get_rect()
    rect.left = 100
    rect.top = 100
    screen.blit(disp, rect)
    pygame.display.flip()
    time.sleep(1/60.0)
    next_repeat += 1

    if next_repeat >= 5 * 60:
        next_repeat = 0
        if repeat_command:
            repeat_command()
