from __future__ import division

from random import randint, seed
import array


class CPU:
    def __init__(self, config, _screen, _keyboard, _sound):
        self.memory_size = config.getint('CPU', 'memory_size')
        self.memory_start = config.getint('CPU', 'memory_start')
        self.register_size = config.getint('CPU', 'register_size')
        self.stack_size = config.getint('CPU', 'stack_size')
        self.sp_size = config.getint('CPU', 'sp_size')
        self.clock_freq = config.getint('CPU', 'clock_freq')
        self.screen = _screen
        self.keyboard = _keyboard
        self.memory = bytearray(self.memory_size)  # 4096 * 8-bits
        self.V_register = bytearray(self.register_size)  # 16 * 8-bits
        self.I = 0  # 1 * 16-bits
        self.stack = array.array('H', [0]*self.stack_size)
        self.stack_pointer = 0  # 1 * 8-bits
        self.program_counter = self.memory_start  # 1 * 16-bits
        self.opcode = 0x0000
        self.delay_timer = 0
        self.sound_timer = 0
        self.sprites = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,
            0x20, 0x60, 0x20, 0x20, 0x70,
            0xF0, 0x10, 0xF0, 0x80, 0xF0,
            0xF0, 0x10, 0xF0, 0x10, 0xF0,
            0x90, 0x90, 0xF0, 0x10, 0x10,
            0xF0, 0x80, 0xF0, 0x10, 0xF0,
            0xF0, 0x80, 0xF0, 0x90, 0xF0,
            0xF0, 0x10, 0x20, 0x40, 0x40,
            0xF0, 0x90, 0xF0, 0x90, 0xF0,
            0xF0, 0x90, 0xF0, 0x10, 0xF0,
            0xF0, 0x90, 0xF0, 0x90, 0x90,
            0xE0, 0x90, 0xE0, 0x90, 0xE0,
            0xF0, 0x80, 0x80, 0x80, 0xF0,
            0xE0, 0x90, 0x90, 0x90, 0xE0,
            0xF0, 0x80, 0xF0, 0x80, 0xF0,
            0xF0, 0x80, 0xF0, 0x80, 0x80
        ]
        self.zero_functions = {
            0x00E0: self.clear_display,
            0x00EE: self.return_from_subroutine
        }
        self.eight_functions = {
            0x0: self.set_vx_to_vy,
            0x1: self.set_vx_to_vx_or_vy,
            0x2: self.set_vx_to_vx_and_vy,
            0x3: self.set_vx_to_vx_xor_vy,
            0x4: self.set_vx_to_vx_plus_vy,
            0x5: self.set_vx_to_vx_minus_vy,
            0x6: self.set_vx_to_vx_shr,
            0x7: self.set_vx_to_vy_minus_vx,
            0xE: self.set_vx_to_vx_shl
        }
        self.main_functions = {
            0x1: self.jump_to_location,
            0x2: self.call_subroutine_at,
            0x3: self.skip_next_if_vx_equals_kk,
            0x4: self.skip_next_if_vx_not_equals_kk,
            0x5: self.skip_next_if_vx_equals_vy,
            0x6: self.set_vx_to_kk,
            0x7: self.add_to_vx,
            0x9: self.skip_next_if_vx_not_equals_vy,
            0xA: self.set_i_register,
            0xB: self.jump_to_location_shift,
            0xC: self.set_vx_random,
            0xD: self.display_sprite
        }
        self.e_functions = {
            0x9E: self.skip_next_if_key_pressed,
            0xA1: self.skip_next_if_key_not_pressed
        }
        self.f_functions = {
            0x07: self.set_vx_dt_value,
            0x0A: self.wait_for_key_pressed,
            0x15: self.set_dt_to_vx,
            0x18: self.set_st_to_vx,
            0x1E: self.add_to_i,
            0x29: self.set_i_to_vx_sprite,
            0x33: self.store_vx_in_i,
            0x55: self.write_vx_in_memory,
            0x65: self.read_vx_from_memory
        }
        self.load_sprites()
        self.sound = _sound
        self.set_seed(56)

    @staticmethod
    def set_seed(s):
        seed(s)

    def clear_display(self):
        """
        0x00E0 - CLR
        """
        if self.screen:
            self.screen.clear()

    def return_from_subroutine(self):
        """
        0x00EE - RET
        """
        self.program_counter = self.stack[self.stack_pointer]
        self.stack_pointer -= 1

    def jump_to_location(self):
        """
        0x1nnn - JP addr
        """
        self.program_counter = (self.opcode & 0x0FFF) - 2

    def call_subroutine_at(self):
        """
        0x2nnn - CALL addr
        """
        self.stack_pointer += 1
        self.stack[self.stack_pointer] = self.program_counter
        self.program_counter = (self.opcode & 0x0FFF) - 2

    def skip_next_if_vx_equals_kk(self):
        """
        0x3xkk - SE Vx, byte
        """
        if self.V_register[(self.opcode >> 8) & 0xF] == self.opcode & 0x00FF:
            self.program_counter += 2

    def skip_next_if_vx_not_equals_kk(self):
        """
        0x4xkk - SNE Vx, byte
        """
        if self.V_register[(self.opcode >> 8) & 0xF] != self.opcode & 0x00FF:
            self.program_counter += 2

    def skip_next_if_vx_equals_vy(self):
        """
        0x5xy0 - SE Vx , Vy
        """
        if self.V_register[(self.opcode >> 8) & 0xF] == self.V_register[(self.opcode >> 4) & 0xF]:
            self.program_counter += 2

    def set_vx_to_kk(self):
        """
        0x6xkk - LD Vx, byte
        """
        self.V_register[(self.opcode >> 8) & 0xF] = self.opcode & 0x00FF

    def add_to_vx(self):
        """
        0x7xkk - ADD Vx, byte
        """
        x_address = (self.opcode >> 8) & 0xF
        self.V_register[x_address] = ((self.opcode & 0x00FF) + self.V_register[x_address]) & 0xFF

    def skip_next_if_vx_not_equals_vy(self):
        """
        0x9xy0 - SNE Vx, Vy
        """
        if self.V_register[(self.opcode >> 8) & 0xF] != self.V_register[(self.opcode >> 4) & 0xF]:
            self.program_counter += 2

    def set_i_register(self):
        """
        0xAnnn - LD I, addr
        """
        self.I = self.opcode & 0x0FFF

    def jump_to_location_shift(self):
        """
        0xBnnn - JP V0, addr
        """
        self.program_counter = self.V_register[0] + (self.opcode & 0x0FFF) - 2

    def set_vx_random(self):
        """
        0xCxkk - RND Vx, byte
        """
        self.V_register[(self.opcode >> 8) & 0xF] = (self.opcode & 0x00FF) & randint(0, 0xFF)

    def display_sprite(self):
        """
        0xDxyn - DRW Vx , Vy , nibble
        """
        x_pos_init = self.V_register[(self.opcode >> 8) & 0xF]
        y_pos_init = self.V_register[(self.opcode >> 4) & 0xF]
        self.V_register[0xF] = 0
        for y_shift in range(self.opcode & 0xF):
            byte = self.memory[self.I+y_shift]
            byte = '{0:0{1}b}'.format(byte, 8)
            y_pos = (y_pos_init + y_shift) % self.screen.height
            for x_shift, bit in enumerate(byte):
                x_pos = (x_pos_init + x_shift) % self.screen.width
                color = int(bit)
                curr_color = self.screen.pixels_matrix[x_pos, y_pos]
                if not (color == 0 and curr_color == 0):
                    self.V_register[0xF] = not((color == 1) and (curr_color == 1))
                    self.screen.to_redraw.append((x_pos, y_pos))
                    self.screen.pixels_matrix[x_pos, y_pos] = color ^ curr_color

    def set_vx_to_vy(self):
        """
        0x8xy0 - LD Vx, Vy
        """
        self.V_register[(self.opcode >> 8) & 0xF] = self.V_register[(self.opcode >> 4) & 0xF]

    def set_vx_to_vx_or_vy(self):
        """
        0x8xy1 - OR Vx, Vy.
        """
        self.V_register[(self.opcode >> 8) & 0xF] |= self.V_register[(self.opcode >> 4) & 0xF]

    def set_vx_to_vx_and_vy(self):
        """
        0x8xy2 - AND Vx, Vy.
        """
        self.V_register[(self.opcode >> 8) & 0xF] &= self.V_register[(self.opcode >> 4) & 0xF]

    def set_vx_to_vx_xor_vy(self):
        """
        0x8xy3 - XOR Vx, Vy.
        """
        self.V_register[(self.opcode >> 8) & 0xF] ^= self.V_register[(self.opcode >> 4) & 0xF]

    def set_vx_to_vx_plus_vy(self):
        """
        0x8xy4 - ADD Vx, Vy.
        """
        x_address = (self.opcode >> 8) & 0xF
        y_address = (self.opcode >> 4) & 0xF
        add_value = self.V_register[x_address] + self.V_register[y_address]
        self.V_register[x_address] = add_value & 0xFF
        self.V_register[0xF] = add_value > 0xFF

    def set_vx_to_vx_minus_vy(self):
        """
        0x8xy5 - SUB Vx, Vy
        """
        x_address = (self.opcode >> 8) & 0xF
        y_address = (self.opcode >> 4) & 0xF
        value = self.V_register[x_address] - self.V_register[y_address]
        self.V_register[0xF] = value > 0
        self.V_register[x_address] = value if value >= 0 else 0x100 + value

    def set_vx_to_vx_shr(self):
        """
        0x8xy6 - SHR Vx, {Vy}
        """
        self.V_register[0xF] = (self.V_register[(self.opcode >> 8) & 0xF] & 0x1) == 1
        self.V_register[(self.opcode >> 8) & 0xF] >>= 1

    def set_vx_to_vy_minus_vx(self):
        """
        0x8xy7 - SUBN Vx, Vy
        """
        x_address = (self.opcode >> 8) & 0xF
        y_address = (self.opcode >> 4) & 0xF
        value = self.V_register[y_address] - self.V_register[x_address]
        self.V_register[0xF] = 1 if value > 0 else 0
        self.V_register[x_address] = value if value >= 0 else 0x100 + value

    def set_vx_to_vx_shl(self):
        """
        0x8xyE - SHL Vx, {Vy}
        """
        x_address = (self.opcode >> 8) & 0xF
        self.V_register[0xF] = self.V_register[x_address] >> 7
        self.V_register[x_address] = (self.V_register[x_address] << 1) & 0xFF

    def skip_next_if_key_pressed(self):
        """
        0xEx9E - SKP Vx
        """
        if self.keyboard.key_down == self.V_register[(self.opcode >> 8) & 0xF]:
            self.program_counter += 2

    def skip_next_if_key_not_pressed(self):
        """
        0xExA1 - SKNP Vx
        """
        if self.keyboard.key_down != self.V_register[(self.opcode >> 8) & 0xF]:
            self.program_counter += 2

    def set_vx_dt_value(self):
        """
        0xFx07 - LD Vx, DT
        """
        self.V_register[(self.opcode >> 8) & 0xF] = self.delay_timer

    def wait_for_key_pressed(self):
        """
        0xFx0A - LD Vx, K
        """
        if self.keyboard.key_down is None:
            self.program_counter -= 2
        else:
            self.V_register[(self.opcode >> 8) & 0xF] = self.keyboard.key_down

    def set_dt_to_vx(self):
        """
        0xFx15 - LD DT, Vx
        """
        self.delay_timer = self.V_register[(self.opcode >> 8) & 0xF]

    def set_st_to_vx(self):
        """
        0xFx18 - LD ST, Vx
        """
        self.sound_timer = self.V_register[(self.opcode >> 8) & 0xF]

    def add_to_i(self):
        """
        0xFx1E - ADD I, Vx
        """
        x_address = (self.opcode >> 8) & 0xF
        value = (self.I + self.V_register[x_address]) & 0xFFF
        self.I = value

    def set_i_to_vx_sprite(self):
        """
        0xFx29 - LD I, Vx
        """
        x_address = (self.opcode >> 8) & 0xF
        self.I = 5*self.V_register[x_address]

    def store_vx_in_i(self):
        """
        0xFx33 - LD B, Vx
        """
        x_val = self.V_register[(self.opcode >> 8) & 0xF]
        self.memory[self.I] = x_val // 100
        self.memory[self.I+1] = (x_val // 10) % 10
        self.memory[self.I+2] = x_val % 10

    def write_vx_in_memory(self):
        """
        0xFx55 - LD [I], Vx
        """
        x_address = (self.opcode >> 8) & 0xF
        for v in range(0, x_address+1):
            self.memory[self.I+v] = self.V_register[v]

    def read_vx_from_memory(self):
        """
        0xFx65 - LD Vx, [I]
        """
        x_address = (self.opcode >> 8) & 0xF
        for v in range(0, x_address+1):
            self.V_register[v] = self.memory[self.I+v]

    def get_opcode_function(self):
        opcode_class = (self.opcode >> 12) & 0xf
        if opcode_class == 0:
            return self.zero_functions[self.opcode]
        elif opcode_class == 8:
            opcode_type = self.opcode & 0xf
            return self.eight_functions[opcode_type]
        elif opcode_class == 0xE:
            opcode_type = self.opcode & 0x00ff
            return self.e_functions[opcode_type]
        elif opcode_class == 0xF:
            opcode_type = self.opcode & 0x00ff
            return self.f_functions[opcode_type]
        else:
            opcode_type = (self.opcode & 0xf000) >> 12
            return self.main_functions[opcode_type]

    def load_sprites(self):
        self.memory[0:0xF*5] = self.sprites

    def load_rom_into_memory(self, filename):
        with open(filename, 'rb') as f:
            program_binaries = f.read()
        rom_size = len(program_binaries)
        assert (rom_size <= self.memory_size - self.memory_start), \
            'ROM {} is too big to fit in memory ({} bytes)'.format(filename, rom_size)
        self.memory[self.memory_start:self.memory_start+rom_size] = program_binaries

    def execute_instruction(self):
        self.opcode = self.memory[self.program_counter] << 8 | self.memory[self.program_counter+1]
        fun = self.get_opcode_function()
        fun()
        self.program_counter += 2
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 0:
                self.sound.play()
