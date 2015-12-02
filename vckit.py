from bitarray import bitarray
import functools
import operator
from PIL import Image, ImageOps
from random import SystemRandom
random = SystemRandom()

class Pix:
    def from_file(f):
        img = Image.open(f)
        return Pix.from_image(img)

    def from_image(img):
        bw = img.convert(mode='1')
        pixels = bw.load()

        pix = Pix(bw.size[0], bw.size[1])
        for x in range(bw.size[0]):
            for y in range(bw.size[1]):
                pix[x, y] = pixels[x, y]
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
                pixels[x, y] = 0 if self[x, y] else 1
        return img

    def to_file(self, f, scale=1, border=0):
        i = self.to_image()
        if scale != 1:
            i = i.resize((i.size[0] * scale, i.size[1] * scale))
        if border:
            i = ImageOps.expand(i, border)
        i.save(f)

    def ascii_art(self):
        for y in range(self.height):
            for x in range(self.width):
                print('.' if self[x, y] else ' ', end='')
            print()

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
    e = 2

    shares = [Pix(pix.width * e, pix.height * e) for _ in range(k)]
    total = pix.width * pix.height
    for y in range(pix.height):
        for x in range(pix.width):
            print("Block %d/%d" % (y * pix.width + x + 1, total), end='\r')
            if pix[x, y]:
                p = permute(s1)
            else:
                p = permute(s0)

            for i in range(k):
                for y2 in range(e):
                    for x2 in range(e):
                        shares[i][x*e + x2, y*e + y2] = p[i][x2 + y2 * e]
    print()

    return shares

def main():
    z = 'cse207'
    pix = Pix.from_file('%s.png' % z)

    k = 3
    shares = encrypt(pix, k=k, n=k)
    assert len(shares) == k

    for n, s in enumerate(shares):
        f = '%s_enc%d.png' % (z, n)
        print("Saving %s" % f, end='\r')

        i = s.to_file(f, scale=4, border=1)
    print()

    p = Pix(shares[0].width, shares[0].height)
    p.overlay(*shares)
    #p.ascii_art()

    p.to_file('%s_overlay.png' % z, scale=4, border=1)

if __name__ == '__main__':
    main()
s0 = s(0, 4)
