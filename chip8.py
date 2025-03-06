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
                    self.pc += 2 #skip the next instruction

            case 0x4: #SNE Vx byte - skip inst
                x = (opcode & 0x0F00) >> 8
                if self.V[x] != (opcode & 0x00FF):
                    self.pc += 2 #skip the next instruction
            
            case 0x5: #SE Vx Vy - skip inst
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                if self.V[x] == self.V[y]:
                    self.pc += 2 #skip the next instruction

            case 0x6: #LD Vx, byte
                x = (opcode & 0x0F00) >> 8
                self.V[x] = (opcode & 0x00FF)
            
            case 0x7: #ADD Vx, byte
                x = (opcode & 0x0F00) >> 8
                self.V[x] += (opcode & 0x00FF)
                if self.V[x] > 255: self.V[x] -= 255
            
            case 0x8:
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                temp = opcode & 0x000F

                match temp:
                    case 0: #LD Vx, Vy
                        self.V[x] = self.V[y]

                    case 1: #OR Vx, Vy
                        self.V[x] |= self.V[y]
                    
                    case 2: #AND Vx, Vy
                        self.V[x] &= self.V[y]
                    
                    case 3: #XOR Vx, Vy
                        self.V[x] ^= self.V[y]

                    case 4: #ADD Vx, Vy
                        self.V[x] = self.V[x] + self.V[y]
                        self.V[0xF] = 1 if (self.V[x] > 255) else 0

                    case 5: #SUB Vx, Vy
                        self.V[0xF] = 1 if (self.V[x] > self.V[y]) else 0
                        self.V[x] -= self.V[y]

                    case 6: #SHR Vx {, Vy}
                        self.V[0xF] = 1 if ((self.V[x] & 1) == 1) else 0
                        self.V[x] //= 2

                    case 7: #SUBN Vx, Vy
                        self.V[0xF] = 1 if (self.V[y] > self.V[x]) else 0
                        self.V[x] = self.V[y] - self.V[x]

                    case 14: #SHL Vx {, Vy}
                        self.V[0xF] = 1 if ((self.V[x] & 1) == 1) else 0
                        self.V[x] *= 2

            
            case 0x9: #SNE Vx Vy - skip inst
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                if self.V[x] != self.V[y]:
                    self.pc += 2 #skip the next instruction

            case 0xA: #LD I, addr
                self.I = (opcode & 0x0FFF)

            case 0xB: #JP V0, addr
                self.pc = (opcode & 0x0FFF) + self.V[0]

            case 0xC: #RND Vx, byte
                x = (opcode & 0x0F00) >> 8
                k = (opcode & 0x00FF)
                rb = random.randint(0,255)
                self.V[x] = k & rb

            case 0xD: #DRW Vx, Vy, nibble
                self.V[0xF] = 0

                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                n = (opcode & 0x000F)

                vx = self.V[x]
                vy = self.V[y]

                for py in range(n):
                    sprite = self.memory[self.I + py]

                    for px in range(8):
                        pixel = (sprite >> (7-px)) & 1

                        scr_x = (vx + px) % width
                        scr_y = (vy + py) % height

                        if pixel == 1 and self.gfx[scr_y][scr_x] == 1:
                            self.V[0xF] = 1 #Collison
                        
                        self.gfx[scr_y][scr_x] ^= pixel
                        

            case 0xE: 
                x = (opcode & 0x0F00) >> 8
                kk = (opcode & 0x00FF)
                if (kk == 0x9E): #SKP Vx
                    if (self.keypad[self.V[x]] == 1): #key pressed
                        self.pc += 2
                elif (kk == 0xA1): #SKNP Vx
                    if (self.keypad[self.V[x]] != 1): #key not pressed
                        self.pc += 2


            case 0xF:
                x = (opcode & 0x0F00) >> 8
                temp = (opcode & 0x00FF)

                match temp:
                    case 0x07: #LD Vx, DT
                        self.V[x] = self.delay_timer
                    case 0x0A: #LD Vx, K
                        key_pressed = False

                        for i in self.keypad:
                            if i != 0:
                                self.V[x] = self.keypad.index(i)
                                key_pressed = True
                                break

                        if not(key_pressed):
                            self.pc -= 2  #Rerun = Wait for key press

                    case 0x15: #LD DT, Vx
                        self.delay_timer = self.V[x]
                    case 0x18: #LD ST, Vx
                        self.sound_timer = self.V[x]
                    case 0x1E: #ADD I, Vx
                        self.I += self.V[x]
                    case 0x29: #LD F, Vx
                        self.I = self.V[x] * 5 #each sprite is 5 bytes long
                    case 0x33: #LD B, Vx
                        self.memory[self.I] = self.V[x] // 100
                        self.memory[self.I + 1] = (self.V[x] % 100) // 10
                        self.memory[self.I + 2] = self.V[x] % 10
                    case 0x55: #LD [I], Vx
                        for i in range(x+1):
                            self.memory[self.I + i] = self.V[i]
                    case 0x65: #LD Vx, [I]
                        for i in range(x+1):
                            self.V[i] = self.memory[self.I + i]

        # Update timers
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

#Screen config
pygame.init()
screen = pygame.display.set_mode((width*10, height*10))
clock = pygame.time.Clock()

chip8 = Chip8()
chip8.load_rom("rom.ch8") #loading ROM  

#Main loop
run = True
while run:
    for event in pygame.event.get():
        
        if event.type == QUIT:
            run = False

    chip8.emulate_cycle()
    
    # Draw graphics
    for y in range(height):
        for x in range(width):
            if chip8.gfx[y][x] == 1:
                pygame.draw.rect(screen, (255, 255, 255), (x * 10, y * 10, 10, 10))

    pygame.display.flip()
    clock.tick(60)  # Run at 60Hz

pygame.quit()