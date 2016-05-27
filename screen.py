import numpy as np
from pygame.surfarray import make_surface


class Pixel:
    def __init__(self, _pos, _color):
        self.color = _color
        self.pos = _pos


class Screen:
    def __init__(self, _w, _h, _scale):
        self.height = _h
        self.width = _w
        self.scale = _scale
        self.white_pixel = make_surface(np.ones((self.scale, self.scale), dtype=int)*255)
        self.black_pixel = make_surface(np.zeros((self.scale, self.scale), dtype=int))
        self.surface_pixels = {0: self.black_pixel, 1: self.white_pixel}
        self.pixels_matrix = []
        self.to_redraw = []
        self.clear()

    def clear(self):
        self.pixels_matrix = [[Pixel((i*self.scale, j*self.scale), 0) for j in range(self.height)]
                              for i in range(self.width)]
        self.to_redraw = [(i, j) for j in range(self.height) for i in range(self.width)]

    def redraw(self, background):
        for pos in self.to_redraw:
            pixel = self.pixels_matrix[pos[0]][pos[1]]
            background.blit(self.surface_pixels[pixel.color], pixel.pos)
        self.to_redraw = []
