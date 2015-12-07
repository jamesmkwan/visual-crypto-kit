import argparse
from bitarray import bitarray
import functools
import operator
import os
from PIL import Image, ImageOps
from random import SystemRandom
import sys
random = SystemRandom()

class Pix:
    """
    Defines an image with only black and white pixels.
    White is represented as 0.
    Black is represented as 1.
    Supports converting to and from PIL Image mode 1
    """

    def from_file(f):
        img = Image.open(f)
        return Pix.from_image(img)

    def from_image(img):
        bw = img.convert(mode='1')
        pixels = bw.load()

        pix = Pix(bw.size[0], bw.size[1])
        for x in range(bw.size[0]):
            for y in range(bw.size[1]):
                pix[x, y] = not pixels[x, y]
        return pix

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = bitarray(width * height)
        self.data.setall(0)

    def to_image(self):
        img = Image.new('1', (self.width, self.height))
        pixels = img.load()
        for y in range(self.height):
            for x in range(self.width):
                pixels[x, y] = not self[x, y]
        return img

    def to_transparent_image(self):
        img = self.to_image().convert('RGBA')
        pixels = img.load()
        for y in range(self.height):
            for x in range(self.width):
                if pixels[x, y] == (255, 255, 255, 255):
                    pixels[x, y] = (255, 255, 255, 0)
        return img

    def to_file(self, f, scale=1, border=0):
        i = self.to_transparent_image()
        if scale != 1:
            i = i.resize((i.size[0] * scale, i.size[1] * scale))
        if border:
            i = ImageOps.expand(i, border)
        i.save(f)

    def print(self):
        for y in range(self.height):
            for x in range(self.width):
                print('\033[40m ' if self[x, y] else '\033[47m ', end='')
            print('\033[0m')

    def overlay(self, *pix):
        assert all(self.width == p.width for p in pix)
        assert all(self.height == p.height for p in pix)
        for p in pix:
            for i in range(len(self.data)):
                if not self.data[i]:
                    self.data[i] = p.data[i]

    def __getitem__(self, p):
        x, y = p
        assert 0 <= x < self.width
        assert 0 <= y < self.height
        return self.data[y*self.width + x]

    def __setitem__(self, p, v):
        x, y = p
        assert 0 <= x < self.width
        assert 0 <= y < self.height
        self.data[y*self.width + x] = v


def s(t, k):
    r = []
    for i in range(k - 1):
        a = []
        for j in range(2 ** (k - 1)):
            a.append(j >> i & 1)
        r.append(a)

    a = []
    for j in range(2 ** (k - 1)):
        x = t
        for z in r:
            x = x ^ z[j]
        a.append(x)
    r.append(a)
    return r

def permute(s):
    n = len(s[0])
    assert all(len(x) == n for x in s)
    for i in range(n - 1):
        j = random.randrange(i, n)
        for x in s:
            x[i], x[j] = x[j], x[i]
    return s

def encrypt(pix, k, n):
    if k == n:
        return encrypt_kk(pix, k)
    raise Exception("Unsupported parameters")

def encrypt_kk(pix, k):
    s0 = s(0, k)
    s1 = s(1, k)

    # double the pixels if not square
    if k % 2 == 0:
        s0 = [x + x for x in s0]
        s1 = [x + x for x in s1]

    e = 2 ** (k // 2)
    assert len(s0[0]) == e * e

    shares = [Pix(pix.width * e, pix.height * e) for _ in range(k)]
    total = pix.width * pix.height
    for y in range(pix.height):
        for x in range(pix.width):
            i = y * pix.width + x + 1
            print("Block %d/%d" % (i, total), end='\r', file=sys.stderr)
            if pix[x, y]:
                p = permute(s1)
            else:
                p = permute(s0)

            for i in range(k):
                for y2 in range(e):
                    for x2 in range(e):
                        shares[i][x*e + x2, y*e + y2] = p[i][x2 + y2 * e]
    print(file=sys.stderr)
    return shares

def make_playground(n):
    x = '''<html>
<head>
<title>vckit playground</title>
<style type="text/css">
img.share {
  position: absolute;
  top: 0;
  left: 0;
  max-width: 100%%;
  max-height: 100%%;
  z-index: 5;
}

#controller {
  position: absolute;
  right: 0;
  bottom: 0;
  z-index: 100;
}
</style>
<script type="text/javascript">
function update() {
  var ctl = document.getElementById("controller");
  console.log(ctl);

  for (var i = 0; i < ctl.length; i++) {
    var v = ctl[i].selected ? 'visible' : 'hidden';
    document.getElementById(ctl[i].value).style.visibility = v;
  }
}
</script>
</head>
<body>
%s
<select id="controller" onchange="update()" multiple>
%s
</select>
</body>
</html>'''
    imgs = []
    for i in range(n):
        imgs.append('<img src="share_%d.png" id="share_%d" class="share">' % (i, i))

    opts = []
    for i in range(n):
        opts.append('<option value="share_%d" selected>share_%d.png</option>' % (i, i))

    return x % ('\n'.join(imgs), '\n'.join(opts))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True,
            help="input image")
    parser.add_argument('-o', '--output', required=True,
            help="output directory")
    parser.add_argument('-n', type=int, required=True,
            help="number of images to generate")
    parser.add_argument('-p', '--preview', action='store_true',
            help="print preview to stdout")
    parser.add_argument('--playground', action='store_true',
            help="make playground")
    parser.add_argument('-s', '--scale', type=int, default=8,
            help="output image scale")
    parser.add_argument('-b', '--border', type=int, default=1,
            help="output image border (added after scaling)")
    args = parser.parse_args()

    os.mkdir(args.output)

    pix = Pix.from_file(args.input)
    shares = encrypt(pix, k=args.n, n=args.n)

    for n, s in enumerate(shares):
        f = os.path.join(args.output, 'share_%d.png' % n)
        print("Saving %s" % f, end='\r', file=sys.stderr)
        i = s.to_file(f, scale=args.scale, border=args.border)
    print(file=sys.stderr)

    p = Pix(shares[0].width, shares[0].height)
    p.overlay(*shares)
    f = os.path.join(args.output, 'overlay.png')
    p.to_file(f, scale=args.scale, border=args.border)
    if args.preview:
        p.print()

    if args.playground:
        with open(os.path.join(args.output, 'playground.html'), 'w') as f:
            out = make_playground(args.n)
            f.write(out)

if __name__ == '__main__':
    main()
