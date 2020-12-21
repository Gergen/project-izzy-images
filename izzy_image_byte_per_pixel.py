# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 14:39:45 2020

"""
import matplotlib

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import itertools

from PIL import Image

import os.path

input_dir = os.path.join(os.getcwd(), 'data', 'input')
output_dir = os.path.join(os.getcwd(), 'data', 'output')

FRAMEWIDTH = 320
FRAMEHEIGHT = 200

def encode_line( line):
    # line is an array of ints (0-3)
    encoded_line = [] # array of ints corresponding to bytes (0-255)
    for i in range(0, len(line)):
        b = line[ i ]             
        encoded_line.append(b)
    return encoded_line


# ------------------------------------------------------------------------
# Create a test Palette (test.pal)
# Array of arrays of bytes: R (0-63), G (0-63), B (0-63)

palette = []
for i in range(0,64):
    palette.append([i, i, i])
palette.append([0, 0, 63])
# palette.append([12, 39, 0])
palette.append([12, 39, 63])
for i in range(len(palette),256):
    palette.append([0, 0, 0])
assert len(palette) == 256
palette_merged = list(itertools.chain.from_iterable(palette))
  
with open(os.path.join(output_dir, 'test.pal'), mode='wb') as f_out:
    f_out.write(bytes(palette_merged))


# ------------------------------------------------------------------------
# Create a test image (test.bin)
# This is a full frame image: FRAMEWIDTH x FRAMEHEIGHT

image = [] # array of lines, every line is an arrays of ints
for l in range(0,FRAMEHEIGHT):
    line = []
    for c in range(0,FRAMEWIDTH):
        color = int( c * 64.0/FRAMEWIDTH)
        if (c+1) % 10 == 0:
            color = 64
        line.append( color)    
            
    image.append(line)

encoded_image = [] # array of arrays of bytes
for i in range(0,FRAMEHEIGHT):
    encoded_image.append(encode_line(image[i]))

merged_1 = list(itertools.chain.from_iterable(encoded_image))

with open(os.path.join(output_dir, 'test.bin'), mode='wb') as f_out:
    for i in range(0,1):
        f_out.write(bytes(merged_1))
        # f_out.write(bytes(merged_2))

# ------------------------------------------------------------------------
# Convert images to sprite and write out their files

SPRITEWIDTH = 32
SPRITEHEIGHT = 32

def append_suffix( path, suffix):
    (root, ext) = os.path.splitext(path)
    return f"{root}{suffix}{ext}"

def change_ext( path, new_ext):
    (root, ext) = os.path.splitext(path)
    return f"{root}{new_ext}"


image_list = [ 
    { 'name': 'Izzy.png',    'max_colors': 16, 'sprite_width': SPRITEWIDTH, 'sprite_height': SPRITEHEIGHT}, # Izzy is actually double height, is saved as 2 sprites
    { 'name': 'carrot.png',  'max_colors': 16, 'sprite_width': SPRITEWIDTH, 'sprite_height': SPRITEHEIGHT},
    { 'name': 'vet.png',     'max_colors':  2, 'sprite_width': SPRITEWIDTH, 'sprite_height': SPRITEHEIGHT},
    { 'name': 'chocbar.png', 'max_colors': 16, 'sprite_width': SPRITEWIDTH, 'sprite_height': SPRITEHEIGHT},
    { 'name': 'screen.png',  'max_colors': 16, 'sprite_width': FRAMEWIDTH, 'sprite_height': FRAMEHEIGHT},
]

for image in image_list:
    (name, max_colors) = (image['name'], image['max_colors'])
    name_quant = append_suffix(name, '_quant')
    image['name_quant'] = name_quant
    im = Image.open(os.path.join(input_dir, name))
    im_q = im.quantize(max_colors)
    im_q.save(os.path.join(output_dir, name_quant))

for image in image_list:
    (name_quant) = (image['name_quant'])
    print(f"Reading {name_quant}")
    image['image'] = mpimg.imread(os.path.join(output_dir, name_quant))

# create the palette from all the colors in the loaded images
print("Creating palette...")

def key_for_color(r,g,b):
    return f"{int(r)}-{int(g)}-{int(b)}"

COLOR_RGB_RANGE = 63 # mode 13H uses a palette with 256 colors, RGB values each 0-63
PALETTE_SIZE = 256 # we always have 256 colors in the palette

TRANSPARENT_KEY = key_for_color(COLOR_RGB_RANGE,0,0) # this is the color used to indicate transparancy in the input images

default_colors = [
    (0,0,0),                    # palette entry #0 = transparent
    (0, COLOR_RGB_RANGE, 0),    # palette entry #1 = background
]

palette_dict = {}
palette = []
for color in default_colors:
    r, g, b = color
    key = key_for_color(r,g,b)
    # print(key)
    idx = len(palette) # index of next element in palette
    palette.append([r, g, b])
    palette_dict[key] = idx

print(f"{len(palette)} fixed colors were added to the palette")

for image in image_list:
    (img_path, img) = (image['name_quant'], image['image'])
    height = len(img)
    width = len(img[0])
    print(f"Processing {img_path} width={width} height={height}")
    nbr_new_colors_in_image = 0
    for ri in range(0, height):
        for ci in range(0, width):
            r0,g0,b0 = img[ri][ci]
            r = int(r0 * COLOR_RGB_RANGE)
            g = int(g0 * COLOR_RGB_RANGE)
            b = int(b0 * COLOR_RGB_RANGE)
            key = key_for_color(r,g,b)
            if key == TRANSPARENT_KEY:
                pass # just skip this color, do not add it to the palette
            else:
                if key not in palette_dict:
                    idx = len(palette) # index of next element in palette
                    palette.append([r, g, b])
                    palette_dict[key] = idx
                    nbr_new_colors_in_image += 1
    print(f"Found {nbr_new_colors_in_image} new palette colors in this image")
print(f"Total number of colors in the palette is {len(palette)}")
print(f"Extending palette to {PALETTE_SIZE} colors")
for i in range(len(palette),PALETTE_SIZE):
    palette.append([0, 0, 0])
assert len(palette) == 256
palette_merged = list(itertools.chain.from_iterable(palette))
palette_out = os.path.join(output_dir, 'main.pal')
with open(palette_out, mode='wb') as f_out:
    f_out.write(bytes(palette_merged))
print(f"Palette saved as [{palette_out}]")

def save_part( img, width, from_line, to_line, image_out):
    count_total_pixels = width * (to_line - from_line)
    count_transparent_pixels = 0
    image = [] # array of lines, every line is an arrays of ints
    for ri in range(from_line, to_line):
        line = []
        for ci in range(0, width):
            r0,g0,b0 = img[ri][ci]
            r = int(r0 * COLOR_RGB_RANGE)
            g = int(g0 * COLOR_RGB_RANGE)
            b = int(b0 * COLOR_RGB_RANGE)
            key = f"{r}-{g}-{b}"
            if key == TRANSPARENT_KEY:
                count_transparent_pixels += 1 # found a transparent pixel
                c = 0 # palette entry #0 is transparent
            else:
                assert key in palette_dict, f"Unknown color key [{key}] This should be impossible... argghhh..."
                c = palette_dict[key] # palette entry that corresponds with this color
            line.append( c)        
        image.append(line)
    print(f"This image contains {count_transparent_pixels} transparent pixels on a total of {count_total_pixels} pixels ({count_transparent_pixels/count_total_pixels:.0%})")
    image_merged = list(itertools.chain.from_iterable(image))
    with open(image_out, mode='wb') as f_out:
        f_out.write(bytes(image_merged))
    print(f"Image saved as [{image_out}]")

# save all images as bin files and converted to use the palette we just created
print(f"Converting images to palette...")
for image in image_list:
    (orig_img_path, img_path, img, sprite_width, sprite_height) = (image['name'], image['name_quant'], image['image'], image['sprite_width'], image['sprite_height'])
    width = len(img[0])
    assert width == sprite_width
    height = len(img)
    assert height % sprite_height == 0
    assert int(height / sprite_height) <= 2 # allow for max double height sprites
    print(f"Processing {img_path} width={width} height={height}")
    # now some special logic to allow for double height sprites
    is_double_height = int(height / sprite_height) == 2

    if is_double_height:
        image_out = os.path.join(output_dir, change_ext( append_suffix( orig_img_path, '_t'), '.bin'))
        assert len(os.path.basename(image_out)) < 13, f"Output name [{image_out}] is too long"
        save_part( img, width, 0, int(height/2), image_out)

        image_out = os.path.join(output_dir, change_ext( append_suffix( orig_img_path, '_b'), '.bin'))
        assert len(os.path.basename(image_out)) < 13, f"Output name [{image_out}] is too long"
        save_part( img, width, int(height/2), height, image_out)
    else:
        image_out = os.path.join(output_dir, change_ext( orig_img_path, '.bin'))
        assert len(os.path.basename(image_out)) < 13, f"Output name [{image_out}] is too long"
        save_part( img, width, 0, height, image_out)
