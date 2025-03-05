import pygame
from pygame.locals import *

width = 64
height = 32

class Chip8:
    def __init__(self):
        # Memory, Registers, Stack
        self.memory = [0] * 4096 #4kb Memory
        self.V = [0] * 16  #16 General-purpose registers V0-VF
        self.I = 0  #Index register
        self.sp = 0  #Stack pointer
        self.delay_timer = 0 #Delay timer
        self.sound_timer = 0 #Sound timer
        self.pc = 0x200  #Program counter starts at 0x200
        self.stack = [] #Stack
        self.keypad = [0] * 16 #Keyboard
        self.gfx = [[0] * width for _ in range(height)] #Screen

        # Load fontset (0x050-0x09F)
        self.fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        self.memory[0:len(self.fontset)] = self.fontset #Load fontset in Interpreter's memory => Never overwritten

    #Loading a rom
    def load_rom(self, rom_path):
        with open(rom_path, "rb") as rom:
            rom_data = rom.read()
            self.memory[self.pc : self.pc + len(rom_data)] = rom_data

#Screen config
pygame.init()
screen = pygame.display.set_mode((width*10, height*10))

run = True
while run:
    for event in pygame.event.get():
        
        if event.type == QUIT:
            run = False