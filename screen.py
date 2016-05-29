import numpy as np
from pygame.surfarray import make_surface


class Screen:
    def __init__(self, _w, _h, _scale):
        self.height = _h
        self.width = _w
        self.scale = _scale
        white_pixel = make_surface(np.ones((self.scale, self.scale), dtype=int)*255)
        black_pixel = make_surface(np.zeros((self.scale, self.scale), dtype=int))
        self.surface_pixels = {0: black_pixel, 1: white_pixel}
        self.pixels_matrix = None
        self.to_redraw = None
        self.clear()

    def clear(self):
        self.pixels_matrix = np.zeros((self.width, self.height), dtype=int)
        self.to_redraw = [(i, j) for j in range(self.height) for i in range(self.width)]

    def redraw(self, background):
        for pos in self.to_redraw:
            background.blit(self.surface_pixels[self.pixels_matrix[pos]], (pos[0]*self.scale, pos[1]*self.scale))
        self.to_redraw = []
