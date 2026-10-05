# Theory notes for Painter's Order

## The tile as a waveform
The outline is a closed curve p(φ), φ ∈ [0, 1), made of n cubic Béziers that each get 1/n of the period. Played at
frequency f, the left channel is x(f·t) and the right is −y(f·t) (screen y points down). Its Fourier series gives the
timbre directly; `po_kit.tess.spectrum()` prints it.

- **180° point symmetry** (p(φ + ½) = −p(φ) about the centre) cancels every even harmonic, leaving odd harmonics
  only. That is the clarinet's spectral signature.
- Sharp horns and cusps push energy into higher harmonics (brighter); round tiles sound close to a sine.
- Rotating the tile by θ rotates the (L, R) pair. A 90° rotation swaps the channels with one sign flipped, so the four
  voices of a p4 tiling share a timbre but sit differently in the stereo field.

The picture is drawn from the raw signal, including the DC offset that places the tile at its lattice site, as a
DC-coupled scope would see it. The speaker feed is high-passed at 25 Hz and low-passed at 7 kHz.

## The lattice as a Tonnetz
Site (i, j) has frequency `C_ref · 3^i · 5^j`, folded into each voice's register. Moving along lattice vector a is a
perfect fifth (3/2) and along b a just major third (5/4). Triads are triangles:

- C major: (0,0) C, (0,1) E, (1,0) G
- A minor: (−1,1) A, (0,0) C, (0,1) E

On a hexagonal lattice this is Euler's classic triangular Tonnetz. On a square lattice it is the same graph drawn
with a right angle.

Note names use Helmholtz–Ellis comma marks. Spell along the line of fifths (position i + 4j), then count syntonic
commas as −j, because a just major third is a comma below the Pythagorean ditone (81/64 · 80/81 = 5/4). So E reached
by one major third from C is "E−1".

## The comma pump
Hold every common tone through C → Am → Dm → G → C:
- Am keeps C and E, and adds A = (−1, 1).
- Dm keeps A, and adds D = (−2, 1) and F = (−1, 0).
- G keeps D, and adds G = (−3, 1) and B = (−3, 2).
- The next C is a fifth below that G: (−4, 1).

(−4, 1) means 3⁻⁴·5 = 80/81: home has sunk one syntonic comma, 21.5 cents. After N cycles the drift is
N · 21.51 cents, and the walk spans 4N fifths. With 6 cycles that is −129 cents and 24 fifths, which is why the film
travels a long way across the tiling.

At the end the opening chord sounds again as a "ghost" a whole walk away. The two chords are the same notes by name
but N commas apart in pitch, so they clash audibly, and the two lit regions sit far apart on screen.

## Painter's order
Prototiles from tessellation tools often self-intersect, so copies overlap and what you see depends on paint order.
An order that is the same under every lattice translation (class, then position along a fixed direction) gives a
periodic image. The reveal instead paints unvisited tiles first, in muted shades, and visited tiles last in order of
first visit, so the music's history decides which overlaps win.
