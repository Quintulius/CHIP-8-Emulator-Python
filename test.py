import pytest
from ConfigParser import ConfigParser
from random import randint, seed
import numpy as np

from cpu import CPU
from screen import Screen, Pixel
from keyboard import Keyboard

class TestCPUBasic:
    @pytest.fixture(scope='function')
    def cpu(self):
        config = ConfigParser()
        config.read('config.cfg')
        return CPU(config, None, None, None)

    def test_return_from_subroutine(self, cpu):
        """
        0x00EE - RET
        """
        for s in range(0, cpu.stack_size):
            cpu.stack[s] = randint(0x0, 0xFFFF)
        for sp in range(1, cpu.stack_size):
            cpu.stack_pointer = sp
            cpu.return_from_subroutine()
            cpu.program_counter += 2
            assert(cpu.stack_pointer == sp - 1)
            assert(cpu.program_counter == cpu.stack[sp]+2)

    def test_jump_to_location(self, cpu):
        """
        0x1nnn
        """
        for location in range(cpu.memory_start, cpu.memory_size):
            cpu.opcode = 0x1000 | location
            cpu.jump_to_location()
            cpu.program_counter += 2
            assert(cpu.program_counter == location)

    def test_call_subroutine_at(self, cpu):
        """
        0x2nnn - CALL addr
        """
        for nnn in range(cpu.memory_start, cpu.memory_size):
            cpu.opcode = 0x2000 | nnn
            for sp in range(0, cpu.stack_size-1):
                for pc in [cpu.memory_start, cpu.memory_size-2]:
                    cpu.stack_pointer = sp
                    cpu.program_counter = pc
                    cpu.call_subroutine_at()
                    cpu.program_counter += 2
                    assert(cpu.stack_pointer == sp+1)
                    assert(cpu.stack[cpu.stack_pointer] == pc)
                    assert(cpu.program_counter == nnn)

    def test_skip_next_if_vx_equals_kk(self, cpu):
        """
        0x3xkk - SE Vx, byte
        """
        for x in range(0x0, 0xF):
            for v in range(0x0, 0xFF):
                cpu.V_register[x] = v
                for kk in range(0x0, 0xFF):
                    cpu.opcode = 0x3000 | (x << 8) | kk
                    for pc in [cpu.memory_start, cpu.memory_size - 4]:
                        cpu.program_counter = pc
                        cpu.skip_next_if_vx_equals_kk()
                        if v == kk:
                            assert(cpu.program_counter == pc + 2)
                        else:
                            assert(cpu.program_counter == pc)

    def test_skip_next_if_vx_not_equals_kk(self, cpu):
        """
        0x4xkk - SNE Vx, byte
        """
        for x in range(0x0, 0xF):
            for v in range(0x0, 0xFF):
                cpu.V_register[x] = v
                for kk in range(0x0, 0xFF):
                    cpu.opcode = 0x4000 | (x << 8) | kk
                    for pc in [cpu.memory_start, cpu.memory_size - 4]:
                        cpu.program_counter = pc
                        cpu.skip_next_if_vx_not_equals_kk()
                        if v != kk:
                            assert(cpu.program_counter == pc + 2)
                        else:
                            assert(cpu.program_counter == pc)

    def test_skip_next_if_vx_equals_vy(self, cpu):
        """
        0x5xy0 - SE Vx , Vy
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                cpu.opcode = 0x5000 | (x << 8) | (y << 4)
                if x != y:
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            for pc in [cpu.memory_start, cpu.memory_size - 4]:
                                cpu.program_counter = pc
                                cpu.skip_next_if_vx_equals_vy()
                                if v1 == v2:
                                    assert(cpu.program_counter == pc + 2)
                                else:
                                    assert(cpu.program_counter == pc)

    def test_set_vx_to_kk(self, cpu):
        """
        0x6xkk - LD Vx, byte
        """
        for x in range(0x0, 0xF):
            for v in range(0x0, 0xFF):
                for kk in range(0x0, 0xFF):
                    cpu.V_register[x] = v
                    cpu.opcode = 0x6000 | (x << 8) | kk
                    cpu.set_vx_to_kk()
                    assert(cpu.V_register[x] == kk)

    def test_add_to_vx(self, cpu):
        """
        0x7xkk - ADD Vx, byte
        """
        for x in range(0x0, 0xF):
            for v in range(0x0, 0xFF):
                for kk in range(0x0, 0xFF):
                    cpu.V_register[x] = v
                    cpu.opcode = 0x7000 | (x << 8) | kk
                    cpu.add_to_vx()
                    assert(cpu.V_register[x] == (v + kk) & 0xFF)

    def test_skip_next_if_vx_not_equals_vy(self, cpu):
        """
        0x9xy0 - SNE Vx, Vy
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                cpu.opcode = 0x9000 | (x << 8) | (y << 4)
                if x != y:
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            for pc in [cpu.memory_start, cpu.memory_size - 4]:
                                cpu.program_counter = pc
                                cpu.skip_next_if_vx_not_equals_vy()
                                if v1 != v2:
                                    assert(cpu.program_counter == pc + 2)
                                else:
                                    assert(cpu.program_counter == pc)

    def test_set_i_register(self, cpu):
        """
        0xAnnn - LD I, addr
        """
        for address in range(0x0, 0xFFF):
            cpu.opcode = 0xA000 | address
            cpu.set_i_register()
            assert(cpu.I == address)

    def test_jump_to_location_shift(self, cpu):
        """
        0xBnnn - JP V0, addr
        """
        for shift in range(0x0, 0xFFF):
            cpu.opcode = 0xB000 | shift
            cpu.jump_to_location_shift()
            cpu.program_counter += 2
            assert(cpu.program_counter == cpu.V_register[0] + shift)

    def test_set_vx_random(self, cpu):
        """
        0xCxkk - RND Vx, byte
        """
        blanck_v = bytearray(cpu.register_size)
        for s in [0, 23 ,45, 89]:
            for x in range(0x0, 0xF):
                cpu.V_register[:] = blanck_v
                for val in range(0x0, 0xFF):
                    seed(s)
                    ref_rnd = randint(0x0, 0xFF)
                    outval = ref_rnd & val
                    cpu.opcode = 0xC000 | (x << 8) | val
                    cpu.set_seed(s)
                    cpu.set_vx_random()
                    for v in range(0x0, 0xF):
                        if v == x:
                            assert(cpu.V_register[v] == outval)
                        else:
                            assert(cpu.V_register[v] == 0)

    def test_set_vx_to_vy(self, cpu):
        """
        0x8xy0 - LD Vx, Vy
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8000 | (x << 8) | (y << 4)
                    for v in range(0x0, 0xFF):
                        cpu.V_register[y] = v
                        cpu.set_vx_to_vy()
                        assert(cpu.V_register[x] == v)

    def set_vx_to_vx_or_vy(self, cpu):
        """
        0x8xy1 - OR Vx, Vy.
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8001 | (x << 8) | (y << 4)
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            cpu.set_vx_to_vx_or_vy()
                            assert(cpu.V_register[x] == v1 | v2)

    def test_set_vx_to_vx_or_vy(self, cpu):
        """
        0x8xy1 - XOR Vx, Vy.
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8003 | (x << 8) | (y << 4)
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            cpu.set_vx_to_vx_or_vy()
                            assert(cpu.V_register[x] == v1 | v2)

    def test_set_vx_to_vx_and_vy(self, cpu):
        """
        0x8xy2 - AND Vx, Vy.
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8002 | (x << 8) | (y << 4)
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            cpu.set_vx_to_vx_and_vy()
                            assert(cpu.V_register[x] == v1 & v2)

    def test_set_vx_to_vx_xor_vy(self, cpu):
        """
        0x8xy3 - XOR Vx, Vy.
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8003 | (x << 8) | (y << 4)
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            cpu.set_vx_to_vx_xor_vy()
                            assert(cpu.V_register[x] == v1 ^ v2)

    def test_set_vx_to_vx_plus_vy(self, cpu):
        """
        0x8xy4 - ADD Vx, Vy.
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8004 | (x << 8) | (y << 4)
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            cpu.set_vx_to_vx_plus_vy()
                            value = v1 + v2
                            if value > 0xFF:
                                assert(cpu.V_register[0xF] == 1)
                                assert(cpu.V_register[x] == value & 0xFF)
                            else:
                                assert(cpu.V_register[0xF] == 0)
                                assert(cpu.V_register[x] == value)

    def test_set_vx_to_vx_minus_vy(self, cpu):
        """
        0x8xy5 - SUB Vx, Vy
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8005 | (x << 8) | (y << 4)
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            cpu.set_vx_to_vx_minus_vy()
                            value = v1 - v2
                            if value > 0:
                                assert(cpu.V_register[0xF] == 1)
                            else:
                                assert(cpu.V_register[0xF] == 0)
                            if value >= 0:
                                assert(cpu.V_register[x] == value)
                            else:
                                assert(cpu.V_register[x] == 0x100 + value)

    def test_set_vx_to_vx_shr(self, cpu):
        """
        0x8xy6 - SHR Vx, {Vy}
        """
        for x in range(0x0, 0xF):
            for v in range(0x0, 0xFF):
                cpu.V_register[x] = v
                cpu.opcode = 0x8006 | (x << 8)
                cpu.set_vx_to_vx_shr()
                if v & 0x1 == 1:
                    assert(cpu.V_register[0xF] == 1)
                else:
                    assert(cpu.V_register[0xF] == 0)
                assert(cpu.V_register[x] == v/2)

    def test_set_vx_to_vy_minus_vx(self, cpu):
        """
        0x8xy7 - SUBN Vx, Vy
        """
        for x in range(0x0, 0xF):
            for y in range(0x0, 0xF):
                if x != y:
                    cpu.opcode = 0x8007 | (x << 8) | (y << 4)
                    for v1 in range(0x0, 0xFF):
                        for v2 in range(0x0, 0xFF):
                            cpu.V_register[x] = v1
                            cpu.V_register[y] = v2
                            cpu.set_vx_to_vy_minus_vx()
                            value = v2 - v1
                            if value > 0:
                                assert(cpu.V_register[0xF] == 1)
                            else:
                                assert(cpu.V_register[0xF] == 0)
                            if value >= 0:
                                assert(cpu.V_register[x] == value)
                            else:
                                assert(cpu.V_register[x] == 0x100 + value)

    def test_set_vx_to_vx_shl(self, cpu):
        """
        0x8xyE - SHL Vx, {Vy}
        """
        for x in range(0x0, 0xF):
            for v in range(0x0, 0xFF):
                cpu.V_register[x] = v
                cpu.opcode = 0x800E | (x << 8)
                cpu.set_vx_to_vx_shl()
                if v <= 0x7F:
                    assert(cpu.V_register[0xF] == 0)
                    assert(cpu.V_register[x] == 2*v)
                else:
                    assert(cpu.V_register[0xF] == 1)
                    assert(cpu.V_register[x] == 2*v & 0xFF)

    def test_set_vx_dt_value(self, cpu):
        """
        0xFx07 - LD Vx, DT
        """
        cpu.delay_timer = 0xFF
        for x in range(0x0, 0xF):
            cpu.V_register = bytearray(cpu.register_size)
            cpu.opcode = 0xF007 | (x << 8)
            cpu.set_vx_dt_value()
            for v in range(0x0, 0xF):
                if x == v:
                    assert(cpu.V_register[v] == cpu.delay_timer)
                else:
                    assert(cpu.V_register[v] == 0)

    def test_set_dt_to_vx(self, cpu):
        """
        0xFx15 - LD DT, Vx
        """
        cpu.V_register = bytearray([1, 5, 8, 12, 15, 18, 29, 53,
                                    78, 102, 158, 183, 202, 234, 255, 0])
        for x in range(0x0, 0xF):
            cpu.opcode = 0xF015 | (x << 8)
            cpu.set_dt_to_vx()
            assert(cpu.delay_timer == cpu.V_register[x])

    def test_set_st_to_vx(self, cpu):
        """
        0xFx18 - LD ST, Vx
        """
        cpu.V_register = bytearray([1, 5, 8, 12, 15, 18, 29, 53,
                                    78, 102, 158, 183, 202, 234, 255, 0])
        for x in range(0x0, 0xF):
            cpu.opcode = 0xF018 | (x << 8)
            cpu.set_st_to_vx()
            assert(cpu.sound_timer == cpu.V_register[x])

    def test_add_to_i(self, cpu):
        """
        0xFx1E - ADD I, Vx
        """
        cpu.V_register = bytearray([1, 5, 8, 12, 15, 18, 29, 53,
                                    78, 102, 158, 183, 202, 234, 255, 0])
        for x in range(0x0, 0xF):
            cpu.opcode = 0xF01E | (x << 8)
            for i in range(cpu.memory_start, cpu.memory_size):
                cpu.I = i
                cpu.add_to_i()
                assert(cpu.I == (i+cpu.V_register[x]) & 0xFFF)

    def test_set_i_to_vx_sprite(self, cpu):
        """
        0xFx29 - LD I, Vx
        """
        for sprite in range(0x0, 0xF+1):
            for x in range(0x0, 0xF):
                cpu.opcode = 0xF029 | (x << 8)
                cpu.V_register[x] = sprite
                cpu.set_i_to_vx_sprite()
                assert(cpu.I == 5*sprite)

    def test_store_vx_in_i(self, cpu):
        """
        0xFx33 - LD B, Vx
        """
        blank_memory = bytearray(cpu.memory_size)

        cpu.V_register = bytearray([1, 5, 8, 12, 15, 18, 29, 53,
                                    78, 102, 158, 183, 202, 234, 255, 0])
        for x in range(0x0, 0xF):
            cpu.opcode = 0xF033 | (x << 8)
            vx = cpu.V_register[x]
            bcd = '{:03d}'.format(vx)
            for i in range(cpu.memory_start, cpu.memory_size-2):
                cpu.memory[:] = blank_memory
                cpu.I = i
                cpu.store_vx_in_i()
                for m in range(cpu.memory_start, cpu.memory_size):
                    if m < cpu.I or m > cpu.I+2:
                        assert(cpu.memory[m] == 0)
                    else:
                        shift = m - cpu.I
                        assert(int(bcd[shift]) == cpu.memory[cpu.I+shift])

    def test_write_vx_in_memory(self, cpu):
        """
        0xFx55 - LD [I], Vx

        """
        blank_memory = bytearray(cpu.memory_size)

        for v in range(0x0, 0xF):
            cpu.V_register[v] = randint(0x01, 0xFF)
        for x in range(0x0, 0xF):
            cpu.opcode = 0xF055 | (x << 8)
            for i in range(cpu.memory_start, cpu.memory_size-x):
                cpu.memory[:] = blank_memory
                cpu.I = i
                cpu.write_vx_in_memory()
                for m in range(cpu.memory_start, cpu.memory_size):
                    if m < cpu.I or m > cpu.I+x:
                        assert(cpu.memory[m] == 0)
                    else:
                        assert(cpu.memory[m] == cpu.V_register[m-cpu.I])

    def test_read_vx_from_memory(self, cpu):
        """
        0xFx65 - LD Vx, [I]
        """
        for i in range(cpu.memory_start, cpu.memory_size):
            cpu.memory[i] = randint(0x01, 0xFF)

        for x in range(0x0, 0xF):
            for v in range(0x0, 0xF):
                cpu.V_register[v] = 0
            for i in range(cpu.memory_start, cpu.memory_size-x):
                cpu.I = i
                cpu.opcode = 0xF065 | (x << 8)
                cpu.read_vx_from_memory()
                for to_change in range(0x0, x+1):
                    assert(cpu.V_register[to_change] == cpu.memory[cpu.I+to_change])
                for to_keep in range(x+1, 0xF):
                    assert(cpu.V_register[to_keep] == 0)

class TestCPUKeyboard:
    @pytest.fixture(scope='function')
    def cpu(self):
        config = ConfigParser()
        config.read('config.cfg')
        keyboard = Keyboard()
        return CPU(config, None, keyboard, None)

    def test_skip_next_if_key_pressed(self, cpu):
        """
        0xEx9E - SKP Vx
        """
        for key in range(0x0, 0xF+1):
            cpu.opcode = 0xE09E
            cpu.V_register[0] = key
            cpu.keyboard.key_down = key
            cpu.program_counter = 0
            cpu.skip_next_if_key_pressed()
            assert(cpu.program_counter == 2)

    def test_skip_next_if_key_not_pressed(self, cpu):
        """
        0xExA1 - SKNP Vx
        """
        for key_ref in range(0x0, 0xF+1):
            for key in range(0x0, 0xF+1):
                cpu.opcode = 0xE0A1
                cpu.V_register[0] = key_ref
                cpu.keyboard.key_down = key
                cpu.program_counter = 0
                cpu.skip_next_if_key_not_pressed()
                if key_ref != key:
                    assert(cpu.program_counter == 2)
                else:
                    assert(cpu.program_counter == 0)

    def test_wait_for_key_pressed(self, cpu):
        """
        0xFx0A - LD Vx, K
        """
        keys_to_test = [None] + range(0x0, 0xF+1)
        for key in keys_to_test:
            cpu.program_counter = 0
            cpu.opcode = 0xF00A
            cpu.V_register[0] = 0
            cpu.keyboard.key_down = key
            cpu.wait_for_key_pressed()
            cpu.program_counter += 2
            if key is None:
                assert(cpu.V_register[0] == 0)
                assert(cpu.program_counter == 0)
            else:
                assert(cpu.program_counter == 2)
                assert(cpu.V_register[0] == key)

class TestCPUScreen:
    @pytest.fixture(scope='function')
    def cpu(self):
        config = ConfigParser()
        config.read('config.cfg')
        width, height = 64, 32
        screen = Screen(width, height, config.getint('SCREEN', 'scale_factor'))
        return CPU(config, screen, None, None)

    def test_clear_display(self, cpu):
        for i in range(cpu.screen.width):
            for j in range(cpu.screen.height):
                cpu.screen.pixels_matrix[i][j].color == 1
        cpu.clear_display()
        for i in range(cpu.screen.width):
            for j in range(cpu.screen.height):
                assert(cpu.screen.pixels_matrix[i][j].color == 0)

    def test_display_sprite(self, cpu):
        """
        0xDxyn - DRW Vx , Vy , nibble
        """
        cpu.opcode = 0xD000 | (0 << 8) | (1 << 4) | 4
        pixel1 = Pixel((63, 1), 1)
        pixel2 = Pixel((63, 2), 1)
        cpu.screen.pixels_matrix[63][1] = pixel1
        cpu.screen.pixels_matrix[63][2] = pixel2
        cpu.V_register[0] = 62
        cpu.V_register[1] = 31
        cpu.V_register[0xF] = 0
        cpu.I = 0x200
        cpu.memory[0x200] = 0b00000000
        cpu.memory[0x201] = 0b01110000
        cpu.memory[0x202] = 0b01110000
        cpu.memory[0x203] = 0b01110000
        cpu.display_sprite()
        target = np.zeros((cpu.screen.width, cpu.screen.height), dtype=int)
        target[0:2, 0:3] = 1
        target[63, 0] = 1
        output = np.empty((cpu.screen.width, cpu.screen.height), dtype=int)
        for i in range(output.shape[0]):
            for j in range(output.shape[1]):
                output[i, j] = cpu.screen.pixels_matrix[i][j].color
        assert(np.array_equal(output, target))
        assert(cpu.V_register[0xF] == 1)
