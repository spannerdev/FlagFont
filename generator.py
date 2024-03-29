from os import listdir,mkdir,makedirs
from os.path import join,dirname,abspath,getmtime
from shutil import rmtree, copyfile
from math import floor,ceil,sqrt,log
from PIL import Image

BASE = abspath(dirname(__file__))
IMAGE_SIZE = 8
CHARACTER_START = 0xE000
FLAG_DIR = join(BASE,"./flags")
GENERATE_ITEM_MODELS = False # not yet implemented

try:
    rmtree(join(BASE,"./assets"))
except:
    pass
try:
    rmtree(join(BASE,"./src"))
except:
    pass

makedirs(join(BASE,"./assets/flagfont"))
makedirs(join(BASE,"./assets/flagfont/textures/font"))
makedirs(join(BASE,"./src/main/java/dev/spnr/flagfont/"))
mkdir(join(BASE,"./assets/flagfont/font"))

filenames = listdir(FLAG_DIR)
filenames.sort(key=lambda x: getmtime(join(FLAG_DIR,x)))
country = [f for f in filenames if f.startswith("flag_")]
pride = [f for f in filenames if not f in country and not f=="blank.png"]

def get_atlas_size(images):
    area = 1
    while area < len(images):
        area *= 4
    return floor(sqrt(area))*IMAGE_SIZE

def get_image_position(n,atlas_size):
    x = n*IMAGE_SIZE % (atlas_size)
    y = floor(n*IMAGE_SIZE / (atlas_size))*IMAGE_SIZE
    return (x,y)

def create_atlas(images,name):
    atlas_size = get_atlas_size(country)
    atlas = Image.new('RGBA',(atlas_size,atlas_size))
    n = 0
    for filename in images:
        img = Image.open(join(FLAG_DIR,filename))
        pos = get_image_position(n,atlas_size)
        atlas.paste(img,pos)
        img.close()
        n+=1
    atlas.save(join(BASE,f"assets/flagfont/textures/font/{name}.png"))
    return atlas_size

def create_font_json(images,name,atlas_size):
    num_rows = int(atlas_size/IMAGE_SIZE)
    
    chars = []
    for _ in range(num_rows):
        chars.append([" "]*num_rows)
    n = 0
    flag_char_map = {}
    for image in images:
        row = floor(n*IMAGE_SIZE/atlas_size)
        column = int((n*IMAGE_SIZE%atlas_size)/IMAGE_SIZE)
        char = hex(CHARACTER_START+n).replace('0x','\\u')
        chars[row][column] = char
        flag_char_map[image] = char
        n+=1
    chars = [''.join(row) for row in chars]
    charsstr = str(chars).replace("'",'"').replace("\\\\","\\")
    s = f"""{{
    "providers": [
        {{
            "type":"bitmap",
            "file":"flagfont:font/{name}.png",
            "ascent":{IMAGE_SIZE},
            "chars":{charsstr}
        }}
    ]
}}"""
    with open(join(BASE,f"assets/flagfont/font/{name}.json"),"w+") as f:
        f.write(s)
    return flag_char_map

def create_nested_text_class(flag_char_map,name):
    head = f"   public static final class {name} {{\n"
    foot = "    }\n"
    body = ""
    for flag,char in flag_char_map.items():
        java_name = flag.replace('.png','').upper()
        body+=f"    public static final char {java_name} = '{char}';\n"
    return head+body+foot

def create_java_class(text_classes):
    head = f"""package dev.spnr.flagfont;

public final class FlagFont {{
    
"""
    foot = "\n}"
    body = ""
    for text_class in text_classes:
        body += text_class
    with open(join(BASE,"./src/main/java/dev/spnr/flagfont/FlagFont.java"),"w+") as f:
        f.write(head+body+foot)

def generate_one(images,name):
    atlas_size = create_atlas(images,name)
    flag_char_map = create_font_json(images,name,atlas_size)
    text_class = create_nested_text_class(flag_char_map,name.title())
    return text_class

def generate_all():
    classes = []
    classes.append(generate_one(country,"country"))
    classes.append(generate_one(pride,"pride"))
    create_java_class(classes)

generate_all()
