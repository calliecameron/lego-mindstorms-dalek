#!/usr/bin/env python

import sys
import pygame
import time
from Mastermind import *
from dalek import DALEK_PORT

pygame.init()
screen = pygame.display.set_mode((320, 240))
font = pygame.font.Font(None, 40)
text = ""
sock = MastermindClientTCP()
sock.connect(sys.argv[1], DALEK_PORT)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            text = "down: " + pygame.key.name(event.key)
            if event.key == pygame.K_w:
                sock.send("forward\n")
            elif event.key == pygame.K_s:
                sock.send("reverse\n")
        elif event.type == pygame.KEYUP:
            text = "up: " + pygame.key.name(event.key)
            if event.key == pygame.K_w:
                sock.send("stop\n")
            elif event.key == pygame.K_s:
                sock.send("stop\n")

    screen.fill((255, 255, 255))
    disp = font.render(text, True, (0, 0, 0))
    rect = disp.get_rect()
    rect.left = 100
    rect.top = 100
    screen.blit(disp, rect)
    pygame.display.flip()
    time.sleep(1/60.0)
