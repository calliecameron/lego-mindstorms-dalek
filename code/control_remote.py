#!/usr/bin/env python
"""Use this script to control the Dalek remotely. This is the script
you run on the controlling machine; run remote_receiver.py on the
Dalek itself."""


import argparse
import sys
import pygame
import time
from dalek_network import Controller, DRIVE, TURN, HEAD_TURN

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
            controller.exit()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            text = "down: " + pygame.key.name(event.key)
            if event.key == pygame.K_ESCAPE:
                controller.exit()
                sys.exit(0)
            elif event.key == pygame.K_w:
                begin_cmd(DRIVE, 1.0)
            elif event.key == pygame.K_s:
                begin_cmd(DRIVE, -1.0)
            elif event.key == pygame.K_a:
                begin_cmd(TURN, -1.0)
            elif event.key == pygame.K_d:
                begin_cmd(TURN, 1.0)
            elif event.key == pygame.K_q:
                controller.begin_cmd(HEAD_TURN, -1.0)
            elif event.key == pygame.K_e:
                controller.begin_cmd(HEAD_TURN, 1.0)
            elif event.key == pygame.K_1:
                controller.play_sound("exterminate")
            elif event.key == pygame.K_2:
                controller.play_sound("gun")
            elif event.key == pygame.K_3:
                controller.play_sound("exterminate-exterminate-exterminate")
            elif event.key == pygame.K_4:
                controller.play_sound("identify-yourself")
            elif event.key == pygame.K_5:
                controller.play_sound("report")
            elif event.key == pygame.K_6:
                controller.play_sound("social-interaction-will-cease")
            elif event.key == pygame.K_7:
                controller.play_sound("why")
            elif event.key == pygame.K_8:
                controller.play_sound("you-would-make-a-good-dalek")
            elif event.key == pygame.K_9:
                controller.play_sound("doctor")
            elif event.key == pygame.K_0:
                controller.play_sound("the-doctor")
        elif event.type == pygame.KEYUP:
            text = "up: " + pygame.key.name(event.key)
            if event.key == pygame.K_w:
                controller.release_cmd(DRIVE, 1.0)
                repeat_command = None
            elif event.key == pygame.K_s:
                controller.release_cmd(DRIVE, -1.0)
                repeat_command = None
            elif event.key == pygame.K_a:
                controller.release_cmd(TURN, -1.0)
                repeat_command = None
            elif event.key == pygame.K_d:
                controller.release_cmd(TURN, 1.0)
                repeat_command = None
            elif event.key == pygame.K_q:
                controller.release_cmd(HEAD_TURN, -1.0)
            elif event.key == pygame.K_e:
                controller.release_cmd(HEAD_TURN, 1.0)


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
