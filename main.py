import sys
from ConfigParser import ConfigParser
import pygame
from cpu import CPU
from screen import Screen
from keyboard import Keyboard

config = ConfigParser()
config.read('config.cfg')
scale_factor = config.getint('SCREEN', 'scale_factor')
size = width, height = 64*scale_factor, 32*scale_factor
pygame.init()
pygame.mixer.init()

app_screen = pygame.display.set_mode(size, pygame.DOUBLEBUF)
pygame.display.set_caption('Chip8 Emulator')

sound = pygame.mixer.Sound("Buzzer_short.ogg")
screen = Screen(width, height, scale_factor)
keyboard = Keyboard()
cpu = CPU(config, screen, keyboard, sound)
cpu.load_rom_into_memory(config.get('ROM', 'path'))

run_loop = True
while run_loop:
    pygame.time.wait(cpu.clock_freq)
    cpu.execute_instruction()
    cpu.screen.redraw(app_screen)
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run_loop = False
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if pygame.key.name(event.key) in keyboard.keymap.keys():
                keyboard.set_key_down(pygame.key.name(event.key))
        if event.type == pygame.KEYUP:
            if pygame.key.name(event.key) in keyboard.keymap.keys():
                keyboard.reset_key_state()
