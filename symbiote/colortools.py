#!/usr/bin/env python3
#
# symbiote/colortools.py

import colorsys
import webcolors
import matplotlib.pyplot as plt
import numpy as np

class ColorConverter:
    def convert(self, input_color, output_format=None):
        if isinstance(input_color, tuple) and len(input_color) == 3:
            # Input is RGB
            if output_format.lower() == 'hex':
                return self.rgb_to_hex(input_color)
            elif output_format.lower() == 'color':
                return self.rgb_to_name(input_color)
        elif isinstance(input_color, str):
            if input_color.startswith('#'):
                # Input is Hex
                if output_format.lower() == 'rgb':
                    return self.hex_to_rgb(input_color)
                elif output_format.lower() == 'color':
                    return self.hex_to_name(input_color)
            else:
                # Input is color name
                if output_format.lower() == 'rgb':
                    return self.name_to_rgb(input_color)
                elif output_format.lower() == 'hex':
                    return self.name_to_hex(input_color)
        else:
            raise ValueError("Invalid input color")

    def get_color_format(self, input_color):
        if isinstance(input_color, tuple):
            output_format = 'rgb'
        elif input_color.startswith('#'):
            output_format = 'hex'
        elif input_color in webcolors.CSS3_NAMES_TO_HEX:
            output_format = 'color'
        else:
            raise ValueError("Invalid input color")

        return output_format

    def get_complimentary_colors(self, input_color, output_format=None, num_colors=5):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        rgb = self.convert(input_color, 'rgb')
        r, g, b = [x/255.0 for x in rgb]  # Convert RGB values to [0, 1] range
        h, s, l = colorsys.rgb_to_hls(r, g, b)

        hue_shift = 360.0 / num_colors

        # Generate complimentary colors
        colors = []
        for i in range(num_colors):
            h_new = (h + (i * hue_shift / 360.0)) % 1  # Adjust hue and wrap around if it goes over 1
            r_new, g_new, b_new = colorsys.hls_to_rgb(h_new, s, l)
            comp_color = (int(r_new*255), int(g_new*255), int(b_new*255))
            print(comp_color)
            formatted_color = self.convert(comp_color, output_format)
            colors.append(formatted_color)

        return colors

    def get_contrasting_colors(self, input_color, output_format=None, num_colors=5):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        print(output_format)

        rgb = self.convert(input_color, 'rgb')
        r, g, b = rgb

        # Generate contrasting colors
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        colors = []
        for i in range(num_colors):
            if brightness < 128:
                contrast_color = ((255 - i) % 256, (255 - i) % 256, (255 - i) % 256)  # white
            else:
                contrast_color = (i % 256, i % 256, i % 256)  # black

            formatted_color = self.convert(contrast_color, output_format)
            colors.append(formatted_color)

        return colors

    def get_analogous_colors(self, input_color, output_format=None, num_colors=5):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        rgb = self.convert(input_color, 'rgb')
        h, s, l = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        # Generate analogous colors
        colors = []
        for i in range(num_colors):
            h_new = (h + i/float(num_colors)) % 1
            r, g, b = [int(x*255) for x in colorsys.hls_to_rgb(h_new, s, l)]
            formatted_color = self.convert((r, g, b), output_format)
            colors.append(formatted_color)
        return colors

    def get_triadic_colors(self, input_color, output_format=None, *args, **kwargs):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        if output_format != 'rgb':
            rgb = self.convert(input_color, 'rgb')
        else:
            rgb = input_color

        colors = []

        h, s, l = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        h0 = (h) % 1 
        h1 = (h + 1/3) % 1
        h2 = (h + 2/3) % 1
        for h_new in [h0, h1, h2]:
            print("***", h_new)
            r, g, b = [int(x*255) for x in colorsys.hls_to_rgb(h_new, s, l)]
            formatted_color = self.convert((r, g, b), 'hex')
            colors.append(formatted_color)
        return colors

    def get_split_complementary_colors(self, input_color, output_format=None, *args, **kwargs):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        rgb = self.convert(input_color, 'rgb')
        h, s, l = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        h0 = (h) % 1
        h1 = (h + 1/2 + 1/12) % 1
        h2 = (h + 1/2 - 1/12) % 1
        colors = []
        for h_new in [h0, h1, h2]:
            r, g, b = [int(x*255) for x in colorsys.hls_to_rgb(h_new, s, l)]
            formatted_color = self.convert((r, g, b), output_format)
            colors.append(formatted_color)
        return colors

    def get_tetradic_colors(self, input_color, output_format=None, *args, **kwargs):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        rgb = self.convert(input_color, 'rgb')
        h, s, l = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        colors = []
        for i in range(1, 4):
            h_new = (h + i/4) % 1
            r, g, b = [int(x*255) for x in colorsys.hls_to_rgb(h_new, s, l)]
            formatted_color = self.convert((r, g, b), output_format)
            colors.append(formatted_color)
        return colors

    def get_square_colors(self, input_color, output_format=None, *args, **kwargs):
        return self.get_tetradic_colors(input_color, output_format)

    def get_monochromatic_colors(self, input_color, output_format=None,  num_colors=5):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        r, g, b = self.convert(input_color, 'rgb')
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        h, s, l = colorsys.rgb_to_hls(r/255, g/255, b/255)
        colors = []
        for i in range(num_colors):
            l_new = l * (i+1)/float(num_colors)
            r, g, b = [int(x*255) for x in colorsys.hls_to_rgb(h, s, l_new)]
            formatted_color = self.convert((r, g, b), output_format)
            colors.append(formatted_color)
        return colors

    def get_grayscale_colors(self, input_color, output_format=None, num_colors=5):
        if output_format is None:
            output_format = self.get_color_format(input_color)

        r, g, b = self.convert(input_color, 'rgb')
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        print(gray)

    def rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

    def hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def name_to_rgb(self, name):
        rgb = webcolors.name_to_rgb(name)
        return rgb.red, rgb.green, rgb.blue

    def name_to_hex(self, name):
        return webcolors.name_to_hex(name)

    def rgb_to_name(self, rgb):
        try:
            return webcolors.rgb_to_name(rgb)
        except ValueError:
            return None

    def hex_to_name(self, hex_color):
        try:
            return webcolors.hex_to_name(hex_color)
        except ValueError:
            return None

    def get_color_names(self, format='hex'):
        hex_name = webcolors.CSS3_NAMES_TO_HEX
        rgb_name = {}
        if format == 'hex':
            return hex_name 
        elif format == 'rgb':
            for name, hex_color in hex_name.items():
                rgb_color = self.convert(hex_color, 'rgb')
                rgb_name[name] = rgb_color
            return rgb_name
        elif format == 'rgba':
            for name, hex_color in hex_name.items():
                rgb_color = self.convert(hex_color, 'rgb')
                rgb_alpha = rgb_color + (255,)
                print(name, rgb_alpha)
                rgb_name[name] = rgb_alpha 
            return rgb_name
        else:
            raise ValueError("Invalid format")

    def iterate_all_colors(self):
        for r in range(256):
            for g in range(256):
                for b in range(256):
                    rgb = (r, g, b)
                    hex_color = self.rgb_to_hex(rgb)
                    color_name = self.rgb_to_name(rgb)
                    # ANSI escape code for colored output
                    colored_block = f"\033[48;2;{r};{g};{b}m    \033[m"
                    print(f"RGB: {rgb}, Hex: {hex_color}, Color Name: {color_name} {colored_block}")

    def display_color_chart(self, input_color, num_colors=5):
        format = self.get_color_format(input_color)
        if format != ('hex'):
            input_color = self.convert(input_color, 'hex')

        color_methods = [
            ('Complimentary', self.get_complimentary_colors),
            ('Contrasting', self.get_contrasting_colors),
            ('Analogous', self.get_analogous_colors),
            ('Triadic', self.get_triadic_colors),
            ('Split Complementary', self.get_split_complementary_colors),
            ('Tetradic', self.get_tetradic_colors),
            ('Square', self.get_square_colors),
            ('Monochromatic', self.get_monochromatic_colors)
        ]

        for label, method in color_methods:
            
            method_colors = method(input_color, output_format='hex', num_colors=num_colors)
            print(f"{label}:")
            for hex_color in method_colors:
                if hex_color:
                    # ANSI escape code for colored output
                    colored_block = self.color_to_ascii_block(hex_color)
                    color_name = self.convert(hex_color, 'color') or "N/A"
                    rgb_color = self.convert(hex_color, 'rgb')
                    print(rgb_color, hex_color, color_name)
                    print(f"{colored_block} RGB: {rgb_color} Hex: {hex_color} Name: {color_name}")

            # Create a matplotlib chart
            fig, ax = plt.subplots(1, 1, figsize=(10, 2), dpi=80, facecolor='w', edgecolor='k')
            bars = ax.bar(np.arange(len(method_colors)), [1]*len(method_colors), color=method_colors)
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ['top', 'right', 'left', 'bottom']:
                ax.spines[sp].set_visible(False)
            plt.title(label)
            plt.show()

            print("\n" + "-"*50 + "\n")

    def color_to_ascii_block(self, input_color):
        format = self.get_color_format(input_color)

        if format != 'rgb':
            rgb_color = self.convert(input_color, 'rgb')
        else:
            rgb_color = input_color

        r, g, b = rgb_color
        return '\033[48;2;{};{};{}m \033[0m'.format(r, g, b)

    # method aliases
    co = convert
    gc = get_color_names
    ic = iterate_all_colors
    contrast = get_contrasting_colors
    compliment = get_complimentary_colors

import unittest

class TestColorConverter(unittest.TestCase):
    def setUp(self):
        self.converter = ColorConverter()

    def test_convert(self):
        self.assertEqual(self.converter.convert('red', 'hex'), '#ff0000')
        self.assertEqual(self.converter.convert('#ff0000', 'rgb'), (255, 0, 0))
        self.assertEqual(self.converter.convert((255, 0, 0), 'hex'), '#ff0000')

    def test_get_color_format(self):
        self.assertEqual(self.converter.get_color_format('red'), 'color')
        self.assertEqual(self.converter.get_color_format('#ff0000'), 'hex')
        self.assertEqual(self.converter.get_color_format((255, 0, 0)), 'rgb')

    def test_get_complimentary_colors(self):
        self.assertEqual(len(self.converter.get_complimentary_colors('red', num_colors=5)), 5)

    def test_get_contrasting_colors(self):
        self.assertEqual(len(self.converter.get_contrasting_colors('red', num_colors=5)), 5)

    def test_get_analogous_colors(self):
        self.assertEqual(len(self.converter.get_analogous_colors('red', num_colors=5)), 5)

    def test_get_triadic_colors(self):
        self.assertEqual(len(self.converter.get_triadic_colors('red')), 3)

    def test_get_split_complementary_colors(self):
        self.assertEqual(len(self.converter.get_split_complementary_colors('red')), 3)

    def test_get_tetradic_colors(self):
        self.assertEqual(len(self.converter.get_tetradic_colors('red')), 4)

    def test_get_square_colors(self):
        self.assertEqual(len(self.converter.get_square_colors('red')), 4)

    def test_get_monochromatic_colors(self):
        self.assertEqual(len(self.converter.get_monochromatic_colors('red', num_colors=5)), 5)

    def test_rgb_to_hex(self):
        self.assertEqual(self.converter.rgb_to_hex((255, 0, 0)), '#ff0000')

    def test_hex_to_rgb(self):
        self.assertEqual(self.converter.hex_to_rgb('#ff0000'), (255, 0, 0))

    def test_name_to_rgb(self):
        self.assertEqual(self.converter.name_to_rgb('red'), (255, 0, 0))

    def test_name_to_hex(self):
        self.assertEqual(self.converter.name_to_hex('red'), '#ff0000')

    def test_rgb_to_name(self):
        self.assertEqual(self.converter.rgb_to_name((255, 0, 0)), 'red')

    def test_hex_to_name(self):
        self.assertEqual(self.converter.hex_to_name('#ff0000'), 'red')

# unittest.main()

# Example usage
'''
color = ColorConverter()
colors = []
colors.append(color.co('red', 'hex'))  # Output: '#ff0000'
colors.append(color.co('#ff0000', 'rgb'))  # Output: (255, 0, 0)
colors.append(color.co('#ff0000', 'color'))  # Output: 'red'

colors.append(color.co('purple', 'hex'))
colors.append(color.co('magenta', 'rgb'))
colors.append(color.contrast('magenta', 'hex'))
colors.append(color.compliment('magenta', 'hex'))

for i in colors:
    print(i)

color = ColorConverter()
color.display_color_chart('red')
'''
