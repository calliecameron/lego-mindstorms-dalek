#!/usr/bin/env python
"""Use this script to control the Dalek remotely. This is the script
you run on the controlling machine; run remote_receiver.py on the
Dalek itself."""


import argparse
from dalek_network import Controller, DRIVE, TURN, HEAD_TURN
import io
import PIL.Image
import pygame
import sys
import time

parser = argparse.ArgumentParser(description="Control the Dalek remotely from another machine")
parser.add_argument("addr", help="Address of the Dalek")
parser.add_argument("snapshotFile", help="File in which to save snapshots")

args = parser.parse_args()

pygame.init()
screen = pygame.display.set_mode((320, 240))
font = pygame.font.Font(None, 40)
text = ""

class RemoteController(Controller):
    def __init__(self, addr):
        super(RemoteController, self).__init__(addr)

    def snapshot_received(self, data):
        PIL.Image.open(io.BytesIO(data)).rotate(90).save(args.snapshotFile, "JPEG")

controller = RemoteController(args.addr)

repeat_command = None
next_repeat = 0

def begin_cmd(cmd, value):
    global repeat_command
    controller.begin_cmd(cmd, value)
    def action():
        controller.begin_cmd(cmd, value)
    repeat_command = action


sound_dict = { pygame.K_1: "exterminate",
               pygame.K_2: "gun",
               pygame.K_3: "exterminate-exterminate-exterminate",
               pygame.K_4: "identify-yourself",
               pygame.K_5: "report",
               pygame.K_6: "social-interaction-will-cease",
               pygame.K_7: "why",
               pygame.K_8: "you-would-make-a-good-dalek",
               pygame.K_9: "doctor",
               pygame.K_0: "the-doctor",
               pygame.K_F1: "would-you-care-for-some-tea",
               pygame.K_F2: "can-i-be-of-assistance",
               pygame.K_F3: "please-excuse-me",
               pygame.K_F4: "explain",
               pygame.K_F5: "cease-talking",
               pygame.K_F6: "that-is-incorrect",
               pygame.K_F7: "you-will-follow",
               pygame.K_F8: "daleks-are-supreme",
               pygame.K_F9: "you-will-be-necessary",
               pygame.K_F10: "you-will-identify",
               pygame.K_F11: "it-is-the-doctor",
               pygame.K_F12: "the-doctor-must-die",
               pygame.K_p: "bring-him-to-me",
               pygame.K_i: "i-bring-you-the-human",
               pygame.K_u: "your-loyalty-will-be-rewarded",
               pygame.K_y: "daleks-do-not-question-orders",
               pygame.K_t: "which-of-you-is-least-important",
               pygame.K_l: "this-human-is-our-best-option",
               pygame.K_k: "i-have-duties-to-perform",
               pygame.K_j: "daleks-have-no-concept-of-worry",
               pygame.K_o: "then-hear-me-talk-now"}

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
            elif event.key == pygame.K_RETURN:
                controller.snapshot()
            elif event.key in sound_dict:
                controller.play_sound(sound_dict[event.key])
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
