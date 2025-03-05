import pygame
from pygame.locals import *

width = 64
height = 32

pygame.init()
screen = pygame.display.set_mode((width*10, height*10))

run = True
while run:
    for event in pygame.event.get():
        
        if event.type == QUIT:
            run = False