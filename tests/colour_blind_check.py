"""Colour-blind check of the colours that carry meaning (Water Sort liquids, Remi tile colours, Othello discs).

    python3 tests/colour_blind_check.py

Simulates the three kinds of colour blindness (Machado et al. 2009, full strength) and prints how far apart each
pair of colours stays (CIEDE2000; under ~10 is hard to tell apart at a glance, under ~5 nearly the same).
Needs: numpy, scikit-image.
"""
import itertools, re, os
import numpy as np
from skimage.color import rgb2lab, deltaE_ciede2000

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = {
    'normal': np.eye(3),
    'protan (red-blind)': [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    'deutan (green-blind)': [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
    'tritan (blue-blind)': [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
}


def lin(c): c = np.asarray(c) / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def unlin(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
def hexrgb(h): return [int(h[i:i + 2], 16) for i in (1, 3, 5)]
def sim(h, m): return unlin(np.asarray(m) @ lin(hexrgb(h)))


def arr(name, file):
    src = open(os.path.join(ROOT, 'games', file)).read()
    return re.findall(r"#[0-9a-fA-F]{6}", re.search(name + r"\s*=\s*\[([^\]]+)\]", src).group(1))


SETS = {
    'Water Sort liquids': (arr('COLORS', 'Water_Sort.html'), ['magenta', 'cyan', 'yellow', 'orange', 'green', 'purple', 'red', 'white', 'blue']),
    'Remi tiles': (arr('COL', 'Remi.html'), ['red', 'yellow', 'blue', 'white']),
    'Othello discs (rims)': (['#19f3ff', '#ff2bd6'], ['you/P1 cyan', 'CPU/P2 magenta']),
}
if __name__ == '__main__':
    for title, (cols, names) in SETS.items():
        print('\n' + title)
        for kind, m in M.items():
            labs = [rgb2lab(sim(c, m).reshape(1, 1, 3)).reshape(3) for c in cols]
            pairs = sorted((float(deltaE_ciede2000(labs[a], labs[b])), names[a], names[b])
                           for a, b in itertools.combinations(range(len(cols)), 2))
            close = ['%s/%s %.0f' % (a, b, d) for d, a, b in pairs if d < 12]
            print('  %-22s closest: %s/%s %.0f%s' % (kind, pairs[0][1], pairs[0][2], pairs[0][0],
                  ('   | under 12: ' + ', '.join(close)) if close else ''))
