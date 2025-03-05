import random
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

    #Basically the main
    def emulate_cycle(self):
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]  # Fetch opcode
        self.pc += 2  # Move to next instruction

        # Decode & Execute
        first = opcode >> 12 #get the first bit
        match first:
            case 0x0:
                #Ignoring 0nnn - Sys addr
                if opcode == 0x00E0:  # CLS - Clear screen
                    self.gfx = [[0] * width for _ in range(height)]
                elif opcode == 0x00EE:  # RET - Return from subroutine
                    self.pc = self.stack.pop()
            
            case 0x1: #1nnn - JP addr - jump to nnn
                self.pc = opcode & 0xFFF
            
            case 0x2: #2nnn - CALL addr - call subroutine at nnn
                self.stack.append(self.pc)
                self.pc = opcode & 0xFFF

            case 0x3: #SE Vx byte - skip inst
                x = (opcode & 0x0F00) >> 8
                if self.V[x] == (opcode & 0x00FF):
                    pc += 2 #skip the next instruction

            case 0x4: #SNE Vx byte - skip inst
                x = (opcode & 0x0F00) >> 8
                if self.V[x] != (opcode & 0x00FF):
                    pc += 2 #skip the next instruction
            
            case 0x5: #SE Vx Vy - skip inst
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                if self.V[x] == self.V[y]:
                    pc += 2 #skip the next instruction

            case 0x6:
                x = (opcode & 0x0F00) >> 8
                self.V[x] = (opcode & 0x00FF)
            
            case 0x7:
                x = (opcode & 0x0F00) >> 8
                self.V[x] += (opcode & 0x00FF)
                if self.V[x] > 255: self.V[x] -= 255
            
            case 0x8:
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                temp = opcode & 0x000F

                match temp:
                    case 0:
                        self.V[x] = self.V[y]

                    case 1:
                        self.V[x] |= self.V[y]
                    
                    case 2:
                        self.V[x] &= self.V[y]
                    
                    case 3:
                        self.V[x] ^= self.V[y]

                    case 4:
                        self.V[x] = self.V[x] + self.V[y]
                        self.V[0xF] = 1 if (self.V[x] > 255) else 0

                    case 5:
                        self.V[0xF] = 1 if (self.V[x] > self.V[y]) else 0
                        self.V[x] -= self.V[y]

                    case 6:
                        self.V[0xF] = 1 if ((self.V[x] & 1) == 1) else 0
                        self.V[x] //= 2

                    case 7:
                        self.V[0xF] = 1 if (self.V[y] > self.V[x]) else 0
                        self.V[x] = self.V[y] - self.V[x]

                    case 14:
                        self.V[0xF] = 1 if ((self.V[x] & 1) == 1) else 0
                        self.V[x] *= 2

            
            case 0x9: #SNE Vx Vy - skip inst
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                if self.V[x] != self.V[y]:
                    pc += 2 #skip the next instruction

            case 0xA:
                self.I = (opcode & 0x0FFF)

            case 0xB:
                self.pc = (opcode & 0x0FFF) + self.V[0]

            case 0xC:
                x = (opcode & 0x0F00) >> 8
                k = (opcode & 0x00FF)
                rb = random.randint(0,255)
                self.V[x] = k & rb

            case 0xD:
                pass

            case 0xE:
                pass

            case 0xF:
                x = (opcode & 0x0F00) >> 8
                temp = (opcode & 0x00FF)

                match temp:
                    case 0x07:
                        self.V[x] = self.delay_timer
                    case 0x0A:
                        pass
                    case 0x15:
                        self.delay_timer = self.V[x]
                    case 0x18:
                        self.sound_timer = self.V[x]
                    case 0x1E:
                        self.I += self.V[x]
                    case 0x29:
                        pass
                    case 0x33:
                        self.memory[self.I] = self.V[x] // 100
                        self.memory[self.I + 1] = (self.V[x] % 100) // 10
                        self.memory[self.I + 2] = self.V[x] % 10
                    case 0x55:
                        for i in range(x+1):
                            self.memory[self.I + i] = self.V[i]
                    case 0x55:
                        for i in range(x+1):
                            self.V[i] = self.memory[self.I + i]

#Screen config
pygame.init()
screen = pygame.display.set_mode((width*10, height*10))

run = True
while run:
    for event in pygame.event.get():
        
        if event.type == QUIT:
            run = False