#!/usr/bin/env python

import sys
import pygame
import time
from Mastermind import *

pygame.init()
screen = pygame.display.set_mode((320, 240))
font = pygame.font.Font(None, 40)
text = ""
sock = MastermindClientTCP()
sock.connect("192.168.0.11", 12345)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            text = "down: " + pygame.key.name(event.key)
            sock.send(text + "\n")
        elif event.type == pygame.KEYUP:
            text = "up: " + pygame.key.name(event.key)
            sock.send(text + "\n")

    screen.fill((255, 255, 255))
    disp = font.render(text, True, (0, 0, 0))
    rect = disp.get_rect()
    rect.left = 100
    rect.top = 100
    screen.blit(disp, rect)
    pygame.display.flip()
    time.sleep(1/60.0)
