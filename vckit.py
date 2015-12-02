from bitarray import bitarray
import functools
import operator
from PIL import Image

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
        i = Image.frombuffer(
                mode='1',
                size=(self.width, self.height),
                data=self.data
            )
        return i

    def to_file(self, f):
        self.to_image().save(f)

    def ascii_art(self):
        for y in range(self.height):
            for x in range(self.width):
                print('.' if self[x, y] else ' ', end='')
            print()

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

def main():
    pix = Pix.from_file('sss_w.png')
    pix.ascii_art()

if __name__ == '__main__':
    main()
s0 = s(0, 4)
