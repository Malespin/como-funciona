#!/usr/bin/env python3
"""
CÓMO FUNCIONA — motor de plantilla para videos verticales estilo monigote.

Uso:
    python3 comofunciona.py episodios/lapicero.py                 # video completo
    python3 comofunciona.py episodios/lapicero.py --fotos 1:3.0 4:5.5
        (guarda PNG de la escena 1 en el segundo 3.0, etc., para revisar)

Un episodio es un archivo .py que define:
    TITULO   = "UN LAPICERO"          # aparece en la portada
    ESCENAS  = [ {...}, {...} ]        # ver README.md
Cada escena trae su función de dibujo: dibujo(lz, t) donde lz es un Lienzo
y t los segundos transcurridos dentro de la escena.
"""
import math, random, subprocess, os, sys, wave, importlib.util, argparse, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- ajustes
W, H = 1080, 1920          # salida vertical (YouTube Shorts)
S = 2                      # superesmuestreo: se dibuja a 2x y se reduce (bordes suaves)
FPS = 30
DIR = os.path.dirname(os.path.abspath(__file__))
FUENTE_B = '/usr/share/fonts/truetype/google-fonts/ofl/comicrelief/ComicRelief-Bold.ttf'
FUENTE_R = '/usr/share/fonts/truetype/google-fonts/ofl/comicrelief/ComicRelief-Regular.ttf'
for alt in (os.path.join(DIR, 'fuentes', 'ComicRelief-Bold.ttf'),):
    if os.path.exists(alt):
        FUENTE_B = alt
        FUENTE_R = alt.replace('Bold', 'Regular')

C = dict(
    papel=(251, 247, 238), cuadricula=(222, 231, 242), margen=(242, 178, 172),
    tinta=(31, 36, 48), azul=(47, 91, 234), azul_claro=(205, 222, 252),
    rojo=(232, 87, 74), amarillo=(255, 214, 72), verde=(46, 170, 104),
    naranja=(245, 146, 52), gris=(150, 156, 168), gris_claro=(222, 225, 232),
    metal=(196, 202, 214), blanco=(255, 255, 255), rosa=(255, 196, 196),
    celeste=(214, 234, 250),
)

# Zona segura de Shorts: evita abajo (título/canal) y la franja derecha (botones)
SEGURA = dict(x0=60, x1=980, y0=130, y1=1500)


# ---------------------------------------------------------------- utilidades
_fuentes = {}
def fuente(tam, negrita=True):
    tam = max(6, int(round(tam)))
    k = (tam, negrita)
    if k not in _fuentes:
        _fuentes[k] = ImageFont.truetype(FUENTE_B if negrita else FUENTE_R, int(tam * S))
    return _fuentes[k]

def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def aparece(t, ini, dur=0.5):
    """0→1 suavizado entre ini e ini+dur (segundos)."""
    return suave((t - ini) / dur) if dur > 0 else float(t >= ini)

def rebote(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def lerp(a, b, x):
    return a + (b - a) * x

def rotar(pts, ang, cx=0, cy=0):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


# ---------------------------------------------------------------- lienzo
class Lienzo:
    """Todo se dibuja en coordenadas de 1080x1920. Cada trazo 'tiembla' un poco
    y cambia cada 4 fotogramas (efecto 'boil' de dibujo a mano)."""

    def __init__(self, fondo, fotograma):
        self.img = fondo.copy()
        self.d = ImageDraw.Draw(self.img)
        self.boil = fotograma // 4
        self.k = 0

    # -- internos
    def _clave(self):
        self.k += 1
        return random.Random(self.k * 7919 + self.boil * 104729 + 17)

    def _temblor(self, pts, wob, cerrado, rng):
        pts = list(pts)
        if cerrado:
            pts = pts + [pts[0]]
        res = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 12))
            for i in range(n):
                f = i / n
                res.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
        res.append(pts[-1])
        if wob <= 0:
            return res
        f1, f2 = rng.uniform(.012, .025), rng.uniform(.04, .07)
        ph = [rng.uniform(0, 6.283) for _ in range(4)]
        out, s = [], 0.0
        for i, (x, y) in enumerate(res):
            if i:
                s += math.hypot(x - res[i - 1][0], y - res[i - 1][1])
            dx = wob * (.7 * math.sin(s * f1 + ph[0]) + .3 * math.sin(s * f2 + ph[1]))
            dy = wob * (.7 * math.sin(s * f1 + ph[2]) + .3 * math.sin(s * f2 + ph[3]))
            out.append((x + dx, y + dy))
        if cerrado:
            out[-1] = out[0]
        return out

    @staticmethod
    def _cortar(pts, p):
        if p >= 1:
            return pts
        L = [0.0]
        for a, b in zip(pts, pts[1:]):
            L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        obj = L[-1] * p
        out = [pts[0]]
        for i in range(1, len(pts)):
            if L[i] <= obj:
                out.append(pts[i])
            else:
                seg = L[i] - L[i - 1]
                f = (obj - L[i - 1]) / seg if seg else 0
                a, b = pts[i - 1], pts[i]
                out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                break
        return out

    def _sc(self, pts):
        return [(x * S, y * S) for x, y in pts]

    # -- primitivas públicas
    def linea(self, pts, ancho=6, color=None, p=1, wob=2.2, cerrado=False,
              relleno=None, sombra=False):
        """Trazo a mano. p (0-1) = cuánto del trazo se ha dibujado."""
        rng = self._clave()
        if p <= 0:
            return
        color = color or C['tinta']
        wp = self._temblor(pts, wob, cerrado, rng)
        if relleno is not None and p > 0.55:
            if sombra:
                self.d.polygon(self._sc([(x + 7, y + 8) for x, y in wp]), fill=C['tinta'])
            self.d.polygon(self._sc(wp), fill=relleno)
        seg = self._cortar(wp, p)
        if len(seg) < 2:
            return
        sc = self._sc(seg)
        w = max(1, int(ancho * S))
        self.d.line(sc, fill=color, width=w, joint='curve')
        r = w / 2
        for (x, y) in (sc[0], sc[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def circulo(self, cx, cy, r, ancho=6, color=None, p=1, relleno=None, wob=2.0,
                sombra=False, rx=None):
        rx = rx or r
        n = max(24, int(r / 3))
        a0 = -1.9
        pts = [(cx + rx * math.cos(a0 + 2 * math.pi * i / n),
                cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]
        self.linea(pts, ancho, color, p, wob, cerrado=True, relleno=relleno, sombra=sombra)

    def arco(self, cx, cy, r, a0, a1, ancho=6, color=None, p=1, wob=1.5):
        n = max(8, int(abs(a1 - a0) * r / 10))
        pts = [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
                cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
        self.linea(pts, ancho, color, p, wob)

    def rect(self, x0, y0, x1, y1, ancho=6, color=None, p=1, relleno=None, radio=18,
             wob=2.0, sombra=False):
        r = min(radio, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = []
        for (cx, cy, a) in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0),
                            (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for i in range(5):
                ang = math.radians(a + 90 * i / 4)
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        pts = pts[-1:] + pts[:-1]  # empezar arriba-izquierda
        self.linea(pts, ancho, color, p, wob, cerrado=True, relleno=relleno, sombra=sombra)

    def poligono(self, pts, ancho=6, color=None, p=1, relleno=None, wob=2.0, sombra=False):
        self.linea(pts, ancho, color, p, wob, cerrado=True, relleno=relleno, sombra=sombra)

    def mancha(self, pts, color):
        """Relleno sin borde (sin temblor)."""
        self.k += 1
        self.d.polygon(self._sc(pts), fill=color)

    def flecha(self, p0, p1, curva=0.0, ancho=6, color=None, p=1, punta=26):
        """Flecha (curva>0 dobla a la izquierda). p anima el dibujo."""
        color = color or C['rojo']
        (x0, y0), (x1, y1) = p0, p1
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        nx, ny = -(y1 - y0), (x1 - x0)
        cx, cy = mx + nx * curva, my + ny * curva
        pts = [((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1,
                (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1)
               for u in [i / 20 for i in range(21)]]
        self.linea(pts, ancho, color, min(1, p / 0.8), 1.5)
        hp = (p - 0.8) / 0.2
        ex, ey = pts[-1]
        dx, dy = ex - pts[-3][0], ey - pts[-3][1]
        a = math.atan2(dy, dx)
        for s in (2.6, -2.6):
            q = (ex + punta * math.cos(a + s), ey + punta * math.sin(a + s))
            self.linea([(ex, ey), q], ancho, color, hp, 1.0)

    def texto(self, txt, x, y, tam=48, color=None, ancla='mm', p=1, negrita=True,
              temblor=True):
        """Texto. p revela letra por letra (máquina de escribir). Admite '\\n'."""
        rng = self._clave()
        if p <= 0 or not txt:
            return
        color = color or C['tinta']
        f = fuente(tam, negrita)
        lineas = txt.split('\n')
        lh = tam * 1.18
        total = sum(len(l) for l in lineas)
        visibles = int(round(total * min(1, p)))
        jx = rng.uniform(-1, 1) if temblor else 0
        jy = rng.uniform(-1, 1) if temblor else 0
        alto = lh * len(lineas)
        if ancla[1] == 'm':
            y0 = y - alto / 2
        elif ancla[1] in 'bd':
            y0 = y - alto
        else:
            y0 = y
        for i, l in enumerate(lineas):
            if visibles <= 0:
                break
            parte = l[:visibles]
            visibles -= len(l)
            ancho = self.d.textlength(l, font=f) / S
            if ancla[0] == 'm':
                lx = x - ancho / 2
            elif ancla[0] == 'r':
                lx = x - ancho
            else:
                lx = x
            self.d.text(((lx + jx) * S, (y0 + i * lh + lh / 2 + jy) * S), parte,
                        font=f, fill=color, anchor='lm')

    def ancho_texto(self, txt, tam=48, negrita=True):
        f = fuente(tam, negrita)
        return max(self.d.textlength(l, font=f) for l in txt.split('\n')) / S

    def etiqueta(self, txt, pos, objetivo, p=1, tam=40, color=None, flecha_color=None,
                 curva=0.25):
        """Texto en 'pos' con flecha que apunta a 'objetivo'."""
        color = color or C['tinta']
        self.texto(txt, pos[0], pos[1], tam, color, 'mm', p=aparece(p, 0, 0.5))
        if objetivo is None:
            return
        n = txt.count('\n') + 1
        wt = self.ancho_texto(txt, tam) / 2 + 14
        ht = tam * 1.18 * n / 2 + 10
        dx, dy = objetivo[0] - pos[0], objetivo[1] - pos[1]
        # salir del borde del cuadro de texto
        tx = wt / abs(dx) if dx else 1e9
        ty = ht / abs(dy) if dy else 1e9
        k = min(tx, ty)
        inicio = (pos[0] + dx * k, pos[1] + dy * k)
        fin = (objetivo[0] - dx * 0.06, objetivo[1] - dy * 0.06)
        self.flecha(inicio, fin, curva, 5, flecha_color or C['rojo'], aparece(p, 0.35, 0.65), 20)

    def burbuja(self, txt, x, y, cola, p=1, tam=42, ancho_max=420, relleno=None):
        """Globo de diálogo centrado en (x,y) con la colita hacia 'cola'."""
        if p <= 0:
            self.k += 3
            return
        e = rebote(min(1, p * 1.4))
        lineas = envolver(self, txt, tam, ancho_max)
        txt2 = '\n'.join(lineas)
        w = self.ancho_texto(txt2, tam) + 60
        h = tam * 1.18 * len(lineas) + 44
        w, h = w * e, h * e
        self.poligono([(x - 30 * e, y + h / 2 - 6), (cola[0], cola[1]), (x + 20 * e, y + h / 2 - 6)],
                      5, relleno=relleno or C['blanco'])
        self.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, 5, relleno=relleno or C['blanco'],
                  radio=40)
        self.texto(txt2, x, y, tam, p=aparece(p, 0.25, 0.5))

    # -- composición
    def resaltado(self, x0, y0, x1, y1, color=None, p=1):
        """Trazo de marcador detrás de algo."""
        if p <= 0:
            self.k += 1
            return
        color = color or C['amarillo']
        x1 = lerp(x0, x1, p)
        rng = self._clave()
        pts = [(x0 - 4, y0 + rng.uniform(-2, 2)), (x1 + 6, y0 + 4 + rng.uniform(-2, 2)),
               (x1 + 2, y1 + rng.uniform(-2, 2)), (x0, y1 - 3 + rng.uniform(-2, 2))]
        self.d.polygon(self._sc(pts), fill=color)


def envolver(lz, txt, tam, ancho_max, negrita=True):
    palabras = txt.replace('*', '').split()
    lineas, act = [], ''
    for w in palabras:
        prueba = (act + ' ' + w).strip()
        if lz.ancho_texto(prueba, tam, negrita) <= ancho_max or not act:
            act = prueba
        else:
            lineas.append(act)
            act = w
    if act:
        lineas.append(act)
    return lineas


# ---------------------------------------------------------------- monigote
def monigote(lz, x, pies, t, alto=340, habla=False, apunta=None, expresion='feliz',
             saluda=False, color_detalle=None, mira=None, boca=None):
    """El presentador. apunta=(x,y) estira el brazo derecho hacia ese punto.
    expresion: 'feliz' | 'sorpresa' | 'duda' | 'guiño'."""
    tinta = C['tinta']
    an = 7
    bob = math.sin(t * 2.6) * 5
    r = alto * 0.135
    cab = (x, pies - alto + r + bob)
    cuello = (x, cab[1] + r)
    cadera = (x + math.sin(t * 1.3) * 3, cuello[1] + alto * 0.36)
    hombro = (x, cuello[1] + alto * 0.07)
    pierna = alto * 0.36 - bob
    # piernas
    lz.linea([cadera, (x - 38, cadera[1] + pierna * 0.55), (x - 52, pies)], an, tinta)
    lz.linea([cadera, (x + 36, cadera[1] + pierna * 0.55), (x + 50, pies)], an, tinta)
    lz.linea([(x - 52, pies), (x - 84, pies)], an + 3, tinta)
    lz.linea([(x + 50, pies), (x + 82, pies)], an + 3, tinta)
    # torso
    lz.linea([cuello, cadera], an, tinta)
    # bufanda (sello de la serie)
    cd = color_detalle or C['naranja']
    lz.poligono([(x - 26, cuello[1] - 2), (x + 26, cuello[1] - 2), (x + 22, cuello[1] + 16),
                 (x - 22, cuello[1] + 16)], 5, relleno=cd, wob=1)
    lz.poligono([(x + 6, cuello[1] + 10), (x + 26, cuello[1] + 12), (x + 34, cuello[1] + 66),
                 (x + 14, cuello[1] + 62)], 5, relleno=cd, wob=1)
    brazo = alto * 0.33
    # brazo izquierdo (relajado o en la cintura)
    if expresion == 'duda':
        lz.linea([hombro, (x - 60, hombro[1] + 50), (x - 10, hombro[1] + 20 - 50)], an, tinta)
    else:
        sw = math.sin(t * 2.1) * 0.08
        a = math.radians(115) + sw
        codo = (hombro[0] + brazo * .5 * math.cos(a), hombro[1] + brazo * .5 * math.sin(a))
        mano = (codo[0] + brazo * .5 * math.cos(a - 0.2), codo[1] + brazo * .5 * math.sin(a - 0.2))
        lz.linea([hombro, codo, mano], an, tinta)
    # brazo derecho
    if saluda:
        a = math.radians(-60) + math.sin(t * 9) * 0.35
        codo = (hombro[0] + brazo * .5, hombro[1] - 10)
        mano = (codo[0] + brazo * .55 * math.cos(a), codo[1] + brazo * .55 * math.sin(a))
        lz.linea([hombro, codo, mano], an, tinta)
        lz.circulo(mano[0], mano[1], 12, 5, relleno=C['papel'])
    elif apunta:
        a = math.atan2(apunta[1] - hombro[1], apunta[0] - hombro[0])
        a += math.sin(t * 3.0) * 0.04
        codo = (hombro[0] + brazo * .5 * math.cos(a + 0.35), hombro[1] + brazo * .5 * math.sin(a + 0.35))
        mano = (codo[0] + brazo * .55 * math.cos(a), codo[1] + brazo * .55 * math.sin(a))
        lz.linea([hombro, codo, mano], an, tinta)
        lz.linea([mano, (mano[0] + 26 * math.cos(a), mano[1] + 26 * math.sin(a))], an - 1, tinta)
    else:
        a = math.radians(65) - math.sin(t * 2.1) * 0.08
        codo = (hombro[0] + brazo * .5 * math.cos(a), hombro[1] + brazo * .5 * math.sin(a))
        mano = (codo[0] + brazo * .5 * math.cos(a + 0.2), codo[1] + brazo * .5 * math.sin(a + 0.2))
        lz.linea([hombro, codo, mano], an, tinta)
    # cabeza
    lz.circulo(cab[0], cab[1], r, an, tinta, relleno=C['blanco'])
    # pelito
    for dx, h in ((-14, 30), (0, 38), (14, 28)):
        lz.linea([(cab[0] + dx, cab[1] - r + 2), (cab[0] + dx * 1.6 + 6, cab[1] - r - h)], 5, tinta)
    # cara: mira hacia 'mira' o hacia donde apunta
    objetivo = mira or apunta
    ox = 0
    if objetivo:
        ox = max(-10, min(10, (objetivo[0] - cab[0]) * 0.03))
    ojo_y = cab[1] - r * 0.12
    parpadeo = (t % 3.3) < 0.12
    for dx in (-r * 0.36, r * 0.36):
        ex = cab[0] + dx + ox
        if parpadeo or (expresion == 'guiño' and dx > 0):
            lz.linea([(ex - 9, ojo_y), (ex + 9, ojo_y)], 5, tinta, wob=0.5)
        elif expresion == 'sorpresa':
            lz.circulo(ex, ojo_y, 10, 4, tinta, relleno=C['blanco'], wob=0.4)
            lz.circulo(ex, ojo_y, 4, 4, tinta, relleno=tinta, wob=0)
        else:
            lz.circulo(ex, ojo_y, 6, 4, tinta, relleno=tinta, wob=0.3)
    # cachetes
    for dx in (-r * 0.6, r * 0.6):
        lz.mancha([(cab[0] + dx + ox - 12, cab[1] + r * .25), (cab[0] + dx + ox + 12, cab[1] + r * .25),
                   (cab[0] + dx + ox + 10, cab[1] + r * .25 + 8), (cab[0] + dx + ox - 10, cab[1] + r * .25 + 8)],
                  C['rosa'])
    my = cab[1] + r * 0.42
    mx = cab[0] + ox
    if boca is not None:          # sincronizado con la voz grabada
        habla = boca > 0.10
    if habla:
        if boca is not None:
            ab = 4 + min(1.0, boca) * 20
        else:
            ab = 4 + abs(math.sin(t * 13)) * 13 * (0.5 + 0.5 * abs(math.sin(t * 3.7)))
        lz.circulo(mx, my, ab / 2 + 2, 4, tinta, relleno=C['rojo'], rx=16, wob=0.5)
    elif expresion == 'sorpresa':
        lz.circulo(mx, my + 2, 10, 4, tinta, relleno=C['tinta'], wob=0.4)
    elif expresion == 'duda':
        lz.linea([(mx - 16, my), (mx - 5, my - 5), (mx + 5, my + 3), (mx + 16, my - 2)], 4, tinta, wob=0.5)
    else:
        lz.arco(mx, my - 12, 18, 0.4, math.pi - 0.4, 5, tinta, wob=0.5)
    if expresion == 'duda':
        lz.texto('?', cab[0] + r + 28, cab[1] - r - 10 + math.sin(t * 4) * 6, 70, C['rojo'])
    if expresion == 'sorpresa':
        lz.texto('!', cab[0] + r + 24, cab[1] - r - 10 + math.sin(t * 6) * 5, 70, C['rojo'])


# ---------------------------------------------------------------- fondo y capas fijas
def crear_fondo():
    img = Image.new('RGB', (W * S, H * S), C['papel'])
    d = ImageDraw.Draw(img)
    paso = 54
    for x in range(0, W, paso):
        d.line([(x * S, 0), (x * S, H * S)], fill=C['cuadricula'], width=2)
    for y in range(0, H, paso):
        d.line([(0, y * S), (W * S, y * S)], fill=C['cuadricula'], width=2)
    d.line([(118 * S, 0), (118 * S, H * S)], fill=C['margen'], width=4)
    # grano de papel
    ruido = (np.random.default_rng(3).normal(0, 4, (H * S // 4, W * S // 4, 1))).astype(np.int16)
    ruido = np.repeat(np.repeat(ruido, 4, 0), 4, 1)
    arr = np.asarray(img).astype(np.int16) + ruido
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def insignia(lz, txt, x, y, color, p=1, tam=38, girar=-0.03, texto_color=None):
    """Etiqueta tipo cinta adhesiva."""
    if p <= 0:
        lz.k += 2
        return
    w = lz.ancho_texto(txt, tam) + 44
    h = tam + 30
    e = rebote(p)
    pts = rotar([(-w / 2 * e, -h / 2), (w / 2 * e, -h / 2), (w / 2 * e, h / 2), (-w / 2 * e, h / 2)],
                girar, x, y)
    lz.poligono(pts, 5, relleno=color, sombra=True)
    lz.texto(txt, x, y, tam, texto_color or C['tinta'], p=aparece(p, 0.3, 0.4))


def subtitulo(lz, txt, t, ini=0.3, vel=26, y_top=1290, revelar=None):
    """Caja de subtítulos con *palabras* resaltadas en amarillo."""
    tam, lh = 50, 64
    ancho_max = 860
    p = aparece(t, ini - 0.15, 0.35)
    if p <= 0:
        lz.k += 400
        return
    # parsear *resaltados*
    palabras, dentro = [], False
    for w in txt.split():
        empieza = w.startswith('*')
        w2 = w.lstrip('*')
        cierra = '*' in w2
        w2 = w2.replace('*', '')
        palabras.append((w2, dentro or empieza))
        dentro = (dentro or empieza) and not cierra
    f = fuente(tam)
    esp = lz.d.textlength(' ', font=f) / S
    lineas, act, ancho_act = [], [], 0
    for w, hl in palabras:
        wl = lz.d.textlength(w, font=f) / S
        if act and ancho_act + esp + wl > ancho_max:
            lineas.append((act, ancho_act))
            act, ancho_act = [], 0
        act.append((w, hl, wl))
        ancho_act += (esp if len(act) > 1 else 0) + wl
    lineas.append((act, ancho_act))
    alto = lh * len(lineas) + 50
    x0, x1 = 70, 1010
    e = rebote(p)
    cy = y_top + alto / 2
    lz.rect(540 - (540 - x0) * e, cy - alto / 2 * e, 540 + (x1 - 540) * e, cy + alto / 2 * e,
            6, relleno=C['blanco'], radio=26, sombra=True)
    total = sum(len(w) for l, _ in lineas for (w, _, _) in l)
    visibles = (t - ini) * vel if revelar is None else revelar * total
    cuenta = 0
    rng = random.Random(lz.boil)
    for i, (l, ancho_l) in enumerate(lineas):
        x = 540 - ancho_l / 2
        y = y_top + 25 + i * lh
        for j, (w, hl, wl) in enumerate(l):
            n = int(max(0, min(len(w), visibles - cuenta)))
            if hl and n > 0:
                ext = esp if (j + 1 < len(l) and l[j + 1][1]) else 0
                lz.resaltado(x - 6, y + 14, x + wl * (n / len(w)) + 6 + ext * (n == len(w)),
                             y + lh - 4)
            if n > 0:
                lz.d.text((x * S, (y + lh / 2 + 4) * S), w[:n], font=f, fill=C['tinta'], anchor='lm')
            cuenta += len(w)
            x += wl + esp


def capas_fijas(lz, ep, i, esc, t):
    tipo = esc.get('tipo', 'paso')
    pasos = [e for e in ep.ESCENAS if e.get('tipo', 'paso') == 'paso']
    if tipo == 'portada':
        p1 = aparece(t, 0.05, 0.45)
        insignia(lz, getattr(ep, 'SERIE', 'CÓMO FUNCIONA'), 540, 230, C['amarillo'], p1, 46)
        titulo = esc.get('titulo', ep.TITULO)
        tam = 112 if len(titulo) <= 12 else 92
        lz.texto('¿CÓMO FUNCIONA', 540, 360, 74, C['tinta'], p=aparece(t, 0.3, 0.5))
        pt = rebote(aparece(t, 0.6, 0.5))
        if pt > 0:
            lz.texto(titulo + '?', 540, 470, tam * (0.6 + 0.4 * pt), C['azul'])
        else:
            lz.k += 1
    else:
        insignia(lz, getattr(ep, 'SERIE', 'CÓMO FUNCIONA'), 290, 180, C['amarillo'], 1, 32, -0.04)
        chip = esc.get('chip')
        if chip is None:
            if tipo == 'paso':
                n = pasos.index(esc) + 1
                chip = f'PASO {n}/{len(pasos)}'
            elif tipo == 'dato':
                chip = '¿SABÍAS QUE…?'
            elif tipo == 'piezas':
                chip = 'LAS PIEZAS'
            else:
                chip = ''
        if chip:
            colores = dict(paso=C['celeste'], dato=C['rosa'], piezas=(214, 240, 222))
            insignia(lz, chip, 780, 182, colores.get(tipo, C['celeste']), aparece(t, 0.1, 0.4), 32, 0.035)
        else:
            lz.k += 2
        if esc.get('titulo'):
            lz.texto(esc['titulo'], 540, 300, 74 if len(esc['titulo']) < 20 else 62, C['tinta'],
                     p=aparece(t, 0.15, 0.5))
        else:
            lz.k += 1


# ---------------------------------------------------------------- voz
SR = 44100
VOZ_ANTES = 0.5     # silencio antes de que empieces a hablar en cada escena
VOZ_DESPUES = 1.0   # respiro después de tu última palabra
RITMO = 1.35        # sin voz: cuánto más lento que los tiempos 'dur' del episodio


def leer_audio(ruta):
    """Decodifica cualquier audio (m4a, mp3, ogg/opus de WhatsApp, wav…) a mono float."""
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', ruta, '-ac', '1', '-ar', str(SR),
                          '-af', 'highpass=f=70', '-f', 'f32le', '-'], capture_output=True, check=True)
    return np.frombuffer(out.stdout, dtype=np.float32).copy()


def _rms(x, ventana):
    n = len(x) // ventana
    if n == 0:
        return np.zeros(1)
    return np.sqrt((x[:n * ventana].reshape(n, ventana) ** 2).mean(1) + 1e-12)


def _umbral(rms):
    piso = np.percentile(rms, 10)
    return max(piso * 3.0, rms.max() * 0.05)


def recortar(x):
    v = int(0.02 * SR)
    r = _rms(x, v)
    voz = np.where(r > _umbral(r))[0]
    if len(voz) == 0:
        return x
    a = max(0, (voz[0] - 3) * v)
    b = min(len(x), (voz[-1] + 6) * v)
    return x[a:b]


def cortar_voz(fuente_voz, n):
    """Devuelve n trozos de voz, uno por escena.
    - Carpeta: un archivo por escena, en orden (1.m4a, 2.m4a… o como se ordenen por nombre).
    - Un solo archivo: se corta por las pausas más largas (deja ~2 s de silencio entre escenas)."""
    if os.path.isdir(fuente_voz):
        import re
        ext = ('.m4a', '.mp3', '.wav', '.ogg', '.opus', '.aac', '.flac', '.webm', '.mp4', '.mov', '.3gp')
        arch = [f for f in os.listdir(fuente_voz) if f.lower().endswith(ext)]
        arch.sort(key=lambda s: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)])
        if len(arch) == 1:
            return cortar_voz(os.path.join(fuente_voz, arch[0]), n)
        if len(arch) != n:
            sys.exit(f'La carpeta {fuente_voz} tiene {len(arch)} audios y el episodio tiene {n} escenas.')
        trozos = [recortar(leer_audio(os.path.join(fuente_voz, a))) for a in arch]
    else:
        x = leer_audio(fuente_voz)
        v = int(0.02 * SR)
        r = _rms(x, v)
        silencio = r < _umbral(r)
        # tramos de silencio (en ventanas)
        tramos, ini = [], None
        for k, s in enumerate(silencio):
            if s and ini is None:
                ini = k
            elif not s and ini is not None:
                tramos.append((ini, k))
                ini = None
        voz_idx = np.where(~silencio)[0]
        if len(voz_idx) == 0:
            sys.exit('No encontré voz en la grabación.')
        primero, ultimo = voz_idx[0], voz_idx[-1]
        tramos = [(a, b) for a, b in tramos if a > primero and b < ultimo and (b - a) * 0.02 >= 0.25]
        # Une "pausa · respiración · pausa" en un solo hueco (así separan párrafos
        # las voces de ElevenLabs y también las personas al cambiar de idea).
        unidos = []
        for a, b in tramos:
            if unidos and (a - unidos[-1][1]) * 0.02 < 0.6:
                unidos[-1] = (unidos[-1][0], b)
            else:
                unidos.append((a, b))
        if len(unidos) < n - 1:
            sys.exit(f'Encontré {len(unidos) + 1} bloques de voz y hacen falta {n}. '
                     'Deja una pausa de 2 segundos entre escena y escena.')
        cortes = sorted(sorted(unidos, key=lambda ab: ab[1] - ab[0], reverse=True)[:n - 1])
        inicios = [0] + [b * v for a, b in cortes]
        finales = [a * v for a, b in cortes] + [len(x)]
        trozos = [recortar(x[inicios[k]:finales[k]]) for k in range(n)]
        print('  cortes de voz (s):', ', '.join(f'{a * 0.02:.2f}–{b * 0.02:.2f}' for a, b in cortes))
    pico = max(float(np.abs(t).max()) for t in trozos) or 1.0
    return [t * (0.89 / pico) for t in trozos]


def envolvente(x):
    """Apertura de boca (0-1) por fotograma."""
    v = SR // FPS
    r = _rms(x, v)
    r = r / (np.percentile(r, 95) + 1e-9)
    r = np.convolve(r, [0.25, 0.5, 0.25], mode='same')
    return np.clip(r, 0, 1.2)


def planificar(ep, carpeta, fuente_voz=None):
    """Calcula la duración real de cada escena (y guarda la voz cortada)."""
    plan = []
    trozos = cortar_voz(fuente_voz, len(ep.ESCENAS)) if fuente_voz else None
    for i, e in enumerate(ep.ESCENAS):
        base = e['dur']
        if trozos is not None:
            vd = len(trozos[i]) / SR
            dur = max(base * 1.15, VOZ_ANTES + vd + VOZ_DESPUES)
            ruta = os.path.join(carpeta, f'voz_{i:02d}.wav')
            with wave.open(ruta, 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
                w.writeframes((trozos[i] * 32767).astype(np.int16).tobytes())
            plan.append(dict(dur=round(dur * FPS) / FPS, k=max(1.0, min(3.0, dur / base)),
                             voz=ruta, voz_dur=vd))
        else:
            r = getattr(ep, 'RITMO', RITMO)
            plan.append(dict(dur=round(base * r * FPS) / FPS, k=r, voz=None, voz_dur=0))
    return plan


def leer_wav(ruta):
    with wave.open(ruta) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767


# ---------------------------------------------------------------- sonido
def mezclar_audio(ep, plan, ruta):
    total = sum(p['dur'] for p in plan)
    pista = np.zeros(int(total * SR) + SR, dtype=np.float32)
    rng = np.random.default_rng(1)
    con_voz = any(p['voz'] for p in plan)
    g = 0.55 if con_voz else 1.0   # efectos más bajitos cuando hay voz

    def poner(i, s):
        i = max(0, i)
        n = min(len(s), len(pista) - i)
        pista[i:i + n] += s[:n]

    def pop(t0, tono=1.0, vol=0.22):
        n = int(0.09 * SR)
        tt = np.arange(n) / SR
        f = (520 + 900 * tt / 0.09) * tono
        poner(int(t0 * SR), g * vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 38))

    def whoosh(t0, vol=0.10):
        n = int(0.38 * SR)
        ruido = np.convolve(rng.normal(0, 1, n), np.ones(40) / 40, mode='same')
        poner(int(t0 * SR), g * vol * 4 * ruido * np.sin(np.linspace(0, np.pi, n)) ** 2)

    def ding(t0, vol=0.16):
        n = int(0.6 * SR)
        tt = np.arange(n) / SR
        s = (np.sin(2 * np.pi * 1318 * tt) + .5 * np.sin(2 * np.pi * 1975 * tt)) * np.exp(-tt * 6)
        poner(int(t0 * SR), g * vol * s)

    sfx = dict(pop=pop, whoosh=whoosh, ding=ding)
    acc = 0.0
    for e, p in zip(ep.ESCENAS, plan):
        if acc > 0:
            whoosh(acc)
        pop(acc + 0.3, 0.9, 0.12)
        for item in e.get('sonidos', []):
            sfx[item[1]](acc + item[0] * p['k'])
        if p['voz']:
            poner(int((acc + VOZ_ANTES) * SR), leer_wav(p['voz']))
        acc += p['dur']
    pista = np.clip(pista, -1, 1)
    with wave.open(ruta, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((pista * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- render
def dibujar_fotograma(ep, i, f, fondo, p, env=None):
    esc = ep.ESCENAS[i]
    t = f / FPS
    td = t / p['k']                      # tiempo de animación (más lento)
    dur = p['dur']
    lz = Lienzo(fondo, f)
    capas_fijas(lz, ep, i, esc, td)
    esc['dibujo'](lz, td)
    m = esc.get('monigote', {})
    if m is not None and m.get('ocultar') is not True:
        m = dict(m)
        x = m.pop('x', 175)
        pies = m.pop('pies', 1245)
        entra = rebote(aparece(t, 0, 0.5)) if i == 0 else 1
        if env is not None:
            k = f - int(VOZ_ANTES * FPS)
            m['boca'] = float(env[k]) if 0 <= k < len(env) else 0.0
        habla = 0.3 < t < dur - 0.7
        monigote(lz, x - (1 - entra) * 300, pies, t + i * 1.7, habla=habla, **m)
    if esc.get('texto'):
        if p['voz']:
            rev = max(0.0, min(1.0, (t - VOZ_ANTES + 0.15) / max(0.5, p['voz_dur'] * 0.92)))
            subtitulo(lz, esc['texto'], t, revelar=rev)
        else:
            subtitulo(lz, esc['texto'], t, vel=esc.get('vel', 26) / p['k'])
    img = lz.img
    salida = 0.3
    if i < len(ep.ESCENAS) - 1 and t > dur - salida:
        a = (t - (dur - salida)) / salida
        img = Image.blend(img, fondo, suave(a) * 0.92)
    return img.reduce(S)


def render_escena(ep, i, carpeta, fondo, p):
    n = int(round(p['dur'] * FPS))
    env = envolvente(leer_wav(p['voz'])) if p['voz'] else None
    final = os.path.join(carpeta, f'escena_{i:02d}.mp4')
    tmp = os.path.join(carpeta, f'escena_{i:02d}.tmp.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast',
           '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        pr.stdin.write(dibujar_fotograma(ep, i, f, fondo, p, env).tobytes())
    pr.stdin.close()
    if pr.wait() != 0:
        raise RuntimeError(f'ffmpeg falló en la escena {i}')
    os.replace(tmp, final)


def cargar_episodio(ruta):
    spec = importlib.util.spec_from_file_location('episodio', ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, DIR)
    spec.loader.exec_module(mod)
    return mod


def escribir_guion(ep, nombre, ruta):
    """Guion para grabar: el texto de cada escena, sin asteriscos."""
    L = [f'# Guion — ¿Cómo funciona {ep.TITULO.lower()}?', '',
         'Lee cada bloque tranquilo y deja **2 segundos de silencio** entre uno y otro',
         '(o graba un audio por escena: 1, 2, 3…).', '']
    for i, e in enumerate(ep.ESCENAS, 1):
        txt = e.get('texto', '').replace('*', '')
        seg = len(txt.split()) / 2.4
        L += [f'**{i}. {e.get("titulo") or "Portada"}**  (~{seg:.0f} s)', '', txt, '']
    with open(ruta, 'w') as fh:
        fh.write('\n'.join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('episodio')
    ap.add_argument('--voz', help='grabación: un archivo con pausas, o una carpeta con un audio por escena')
    ap.add_argument('--salida')
    ap.add_argument('--fotos', nargs='*', help='escena:segundo, ej. 2:3.5')
    ap.add_argument('--escenas', help='solo re-renderizar estas, ej. 2,3')
    ap.add_argument('--guion', action='store_true', help='solo escribir el guion para grabar')
    ap.add_argument('--hilos', type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    ep = cargar_episodio(a.episodio)
    nombre = os.path.splitext(os.path.basename(a.episodio))[0]
    if a.guion:
        ruta = f'guion_{nombre}.md'
        escribir_guion(ep, nombre, ruta)
        print(ruta)
        return
    carpeta = os.path.join('render', nombre)
    os.makedirs(carpeta, exist_ok=True)
    plan = planificar(ep, carpeta, a.voz)
    for i, p in enumerate(plan):
        extra = f"  voz {p['voz_dur']:.1f}s" if p['voz'] else ''
        print(f"  escena {i}: {p['dur']:.1f}s (animación ×{p['k']:.2f}){extra}")
    fondo = crear_fondo()
    if a.fotos is not None:
        os.makedirs('fotos', exist_ok=True)
        for item in a.fotos:
            i, s = item.split(':')
            i = int(i)
            env = envolvente(leer_wav(plan[i]['voz'])) if plan[i]['voz'] else None
            img = dibujar_fotograma(ep, i, int(float(s) * FPS), fondo, plan[i], env)
            ruta = f'fotos/{nombre}_e{i}_{s}s.png'
            img.save(ruta)
            print(ruta)
        return
    indices = range(len(ep.ESCENAS))
    if a.escenas:
        indices = [int(x) for x in a.escenas.split(',')]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(a.hilos) as ex:
        list(ex.map(_render_job, [(a.episodio, i, carpeta, plan[i]) for i in indices]))
    lista = os.path.join(carpeta, 'lista.txt')
    with open(lista, 'w') as fh:
        for i in range(len(ep.ESCENAS)):
            fh.write(f"file 'escena_{i:02d}.mp4'\n")
    mudo = os.path.join(carpeta, 'mudo.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lista,
                    '-c', 'copy', mudo], check=True)
    wav = os.path.join(carpeta, 'audio.wav')
    mezclar_audio(ep, plan, wav)
    salida = a.salida or f'{nombre}.mp4'
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mudo, '-i', wav, '-map', '0:v',
                    '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest',
                    '-movflags', '+faststart', salida], check=True)
    print('Listo:', salida)


def _render_job(args):
    ruta, i, carpeta, p = args
    ep = cargar_episodio(ruta)
    render_escena(ep, i, carpeta, crear_fondo(), p)
    print(f'  escena {i} lista', flush=True)


if __name__ == '__main__':
    main()
