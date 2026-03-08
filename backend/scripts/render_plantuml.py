import zlib, urllib.request, os

def plantuml_encode(text):
    data = zlib.compress(text.encode('utf-8'))
    data = data[2:-4]
    return _encode64(data)

def _encode64(data):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    res = []
    i = 0
    while i < len(data):
        b1 = data[i]
        b2 = data[i+1] if i+1 < len(data) else 0
        b3 = data[i+2] if i+2 < len(data) else 0
        c1 = (b1 >> 2) & 0x3F
        c2 = ((b1 & 0x3) << 4 | (b2 >> 4)) & 0x3F
        c3 = ((b2 & 0xF) << 2 | (b3 >> 6)) & 0x3F
        c4 = b3 & 0x3F
        res.append(chars[c1]); res.append(chars[c2]); res.append(chars[c3]); res.append(chars[c4])
        i += 3
    return ''.join(res)

base = os.path.join('backend','docs','diagrams')
files = ['class_diagram.puml','sequence_booking.puml']
for fname in files:
    path = os.path.join(base,fname)
    if not os.path.exists(path):
        print('Missing', path)
        continue
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    code = plantuml_encode(text)
    svg_url = f'http://www.plantuml.com/plantuml/svg/{code}'
    png_url = f'http://www.plantuml.com/plantuml/png/{code}'
    try:
        print('Fetching', svg_url)
        svg = urllib.request.urlopen(svg_url, timeout=15).read()
        with open(os.path.join(base, fname.replace('.puml','.svg')), 'wb') as out:
            out.write(svg)
        print('Saved', fname.replace('.puml','.svg'))
    except Exception as e:
        print('SVG fetch failed for', fname, e)
    try:
        print('Fetching', png_url)
        png = urllib.request.urlopen(png_url, timeout=15).read()
        with open(os.path.join(base, fname.replace('.puml','.png')), 'wb') as out:
            out.write(png)
        print('Saved', fname.replace('.puml','.png'))
    except Exception as e:
        print('PNG fetch failed for', fname, e)
print('Done')
