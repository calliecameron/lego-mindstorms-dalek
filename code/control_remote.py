#!/usr/bin/env python
"""Use this script to control the Dalek remotely. This is the script
you run on the controlling machine; run remote_receiver.py on the
Dalek itself."""


import argparse
from dalek_network import Controller, DRIVE, TURN, HEAD_TURN
import io
import PIL.Image
import pygame
import subprocess
import sys
import time



class RemoteController(Controller):
    def __init__(self, addr, snapshot_file):
        super(RemoteController, self).__init__(addr)
        self.snapshot_file = snapshot_file

    def snapshot_received(self, data):
        PIL.Image.open(io.BytesIO(data)).rotate(90).save(self.snapshot_file, "JPEG")
        with open("/dev/null", "w") as f:
            subprocess.call(["xdg-open", self.snapshot_file], stdout=f, stderr=f)


class Main(object):

    FRAME_RATE = 60
    REPEAT_TIME = 5 * FRAME_RATE

    sound_dict = {pygame.K_1: "exterminate",
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

    def __init__(self, addr, snapshot_file):
        super(Main, self).__init__()
        self.screen = pygame.display.set_mode((320, 240))
        self.font = pygame.font.Font(None, 40)
        self.screen_text = ""
        self.controller = RemoteController(addr, snapshot_file)

        self.repeat_command = None
        self.next_repeat = 0

        self.random_mode = False
        self.next_random_event = 0

        try:
            self.main_loop()
        finally:
            self.controller.exit()

    def begin_drive_cmd(self, cmd, value):
        self.controller.begin_cmd(cmd, value)
        self.repeat_command = None
        self.random_mode = False

    def begin_repeated_drive_cmd(self, cmd, value):
        self.controller.begin_cmd(cmd, value)
        def action():
            self.controller.begin_cmd(cmd, value)
        self.repeat_command = action
        self.next_repeat = Main.REPEAT_TIME
        self.random_mode = False

    def release_drive_cmd(self, cmd, value):
        self.controller.release_cmd(cmd, value)
        self.repeat_command = None
        self.random_mode = False

    def begin_head_cmd(self, cmd, value):
        self.controller.begin_cmd(cmd, value)
        self.random_mode = False

    def release_head_cmd(self, cmd, value):
        self.controller.release_cmd(cmd, value)
        self.random_mode = False

    def main_loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    self.screen_text = "down: " + pygame.key.name(event.key)
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_w:
                        self.begin_repeated_drive_cmd(DRIVE, 1.0)
                    elif event.key == pygame.K_s:
                        self.begin_repeated_drive_cmd(DRIVE, -1.0)
                    elif event.key == pygame.K_a:
                        self.begin_repeated_drive_cmd(TURN, -1.0)
                    elif event.key == pygame.K_d:
                        self.begin_repeated_drive_cmd(TURN, 1.0)
                    elif event.key == pygame.K_q:
                        self.begin_head_cmd(HEAD_TURN, -1.0)
                    elif event.key == pygame.K_e:
                        self.begin_head_cmd(HEAD_TURN, 1.0)
                    elif event.key == pygame.K_RETURN:
                        self.controller.snapshot()
                    elif event.key == pygame.K_v:
                        self.controller.toggle_verbose()
                    elif event.key == pygame.K_SPACE:
                        self.random_mode = True
                        self.next_random_event = 0
                    elif event.key in Main.sound_dict:
                        self.controller.play_sound(Main.sound_dict[event.key])
                elif event.type == pygame.KEYUP:
                    self.screen_text = "up: " + pygame.key.name(event.key)
                    if event.key == pygame.K_w:
                        self.release_drive_cmd(DRIVE, 1.0)
                    elif event.key == pygame.K_s:
                        self.release_drive_cmd(DRIVE, -1.0)
                    elif event.key == pygame.K_a:
                        self.release_drive_cmd(TURN, -1.0)
                    elif event.key == pygame.K_d:
                        self.release_drive_cmd(TURN, 1.0)
                    elif event.key == pygame.K_q:
                        self.release_head_cmd(HEAD_TURN, -1.0)
                    elif event.key == pygame.K_e:
                        self.release_head_cmd(HEAD_TURN, 1.0)


            self.screen.fill((255, 255, 255))
            disp = self.font.render(self.screen_text, True, (0, 0, 0))
            rect = disp.get_rect()
            rect.left = 100
            rect.top = 100
            self.screen.blit(disp, rect)
            pygame.display.flip()
            time.sleep(1/float(Main.FRAME_RATE))

            if self.random_mode:
                self.next_random_event -= 1
                if self.next_random_event <= 0:
                    self.begin_drive_cmd(DRIVE, 0.5)
                    self.next_random_event = 10 * Main.FRAME_RATE

            if self.repeat_command:
                self.next_repeat -= 1
                if self.next_repeat <= 0:
                    self.next_repeat = Main.REPEAT_TIME
                    self.repeat_command()


pygame.init()

parser = argparse.ArgumentParser(description="Control the Dalek remotely from another machine")
parser.add_argument("addr", help="Address of the Dalek")
parser.add_argument("snapshotFile", help="File in which to save snapshots")

args = parser.parse_args()

Main(args.addr, args.snapshotFile)
sys.exit(0)
