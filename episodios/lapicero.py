"""Episodio de ejemplo: ¿Cómo funciona un lapicero?"""
import math
from comofunciona import C, aparece, rebote, rotar, lerp, suave

TITULO = 'UN LAPICERO'
SERIE = 'CÓMO FUNCIONA'


# ------------------------------------------------------------- dibujo reutilizable
def lapicero(lz, cx, cy, esc=1.0, ang=0.0, p=1.0, tinta=0.85, capuchon=True,
             cap_dx=0, cap_dy=0, etapas=None):
    """Lapicero vertical (punta abajo). p anima el dibujo completo;
    etapas=(p_cuerpo, p_carga, p_punta, p_capuchon) para animar pieza por pieza."""
    if etapas is None:
        etapas = (aparece(p, 0, .4), aparece(p, .25, .4), aparece(p, .45, .4), aparece(p, .6, .4))
    pc, pr, pp, pk = etapas

    def T(pts, dx=0, dy=0):
        return rotar([((x + dx) * esc, (y + dy) * esc) for x, y in pts], ang, cx, cy)

    # cuerpo transparente
    lz.poligono(T([(-70, -230), (70, -230), (70, 230), (-70, 230)]), 6, p=pc, relleno=C['celeste'])
    # brillo
    lz.linea(T([(-45, -200), (-45, 180)]), 6, C['blanco'], p=pc)
    # carga de tinta
    lz.poligono(T([(-15, -215), (15, -215), (15, 262), (-15, 262)]), 5, p=pr, relleno=C['blanco'])
    if pr > .6:
        top = 262 - 470 * tinta
        lz.mancha(T([(-11, top), (11, top), (11, 258), (-11, 258)]), C['azul'])
    else:
        lz.k += 1
    # cono y punta metálica
    lz.poligono(T([(-70, 230), (70, 230), (24, 330), (-24, 330)]), 6, p=pp, relleno=C['blanco'])
    lz.poligono(T([(-24, 330), (24, 330), (10, 378), (-10, 378)]), 5, p=pp, relleno=C['metal'])
    bx, by = T([(0, 384)])[0]
    lz.circulo(bx, by, 9 * esc, 4, p=pp, relleno=C['gris'])
    # capuchón
    if capuchon:
        dx, dy = cap_dx, cap_dy
        lz.poligono(T([(-78, -250), (78, -250), (78, -360), (60, -385), (-60, -385), (-78, -360)], dx, dy),
                    6, p=pk, relleno=C['azul'], sombra=False)
        lz.linea(T([(88, -370), (100, -370), (100, -170), (88, -160)], dx, dy), 6, p=pk)
    return (bx, by)


def zoom(lz, cx, cy, r, p, texto='ZOOM ×100'):
    lz.circulo(cx, cy, r + 14, 6, C['tinta'], p=p, relleno=C['blanco'], sombra=True)
    lz.circulo(cx, cy, r, 3, C['gris'], p=p)
    lz.k += 0
    from comofunciona import insignia
    insignia(lz, texto, cx + r * 0.62, cy - r * 0.88, C['amarillo'], aparece(p, .5, .5), 28, 0.08)


def punta_zoom(lz, bx, by, t, p=1, giro=None, r=95, tinta_alto=320):
    """Punta ampliada: paredes metálicas, tinta arriba y la bolita."""
    giro = t * 2.2 if giro is None else giro
    lz.poligono([(bx - 120, by - tinta_alto), (bx + 120, by - tinta_alto), (bx + 80, by - 55),
                 (bx - 80, by - 55)], 0.1, C['azul'], p=p, relleno=C['azul'], wob=1)
    # paredes
    for s in (-1, 1):
        lz.linea([(bx + s * 150, by - tinta_alto), (bx + s * 100, by - 20), (bx + s * 78, by + 60)],
                 26, (118, 124, 140), p=p, wob=1.2)
    # bolita
    pb = aparece(p, .4, .6)
    lz.circulo(bx, by, r, 7, p=pb, relleno=C['metal'])
    if pb > .6:
        lz.arco(bx, by, r - 14, math.pi * 1.1, math.pi * 1.9, 9, C['azul'], wob=0.6)
        lz.circulo(bx - r * .35, by - r * .35, 14, 0.1, C['blanco'], relleno=C['blanco'], wob=0)
        # marca que gira
        lz.linea([(bx + (r - 22) * math.cos(giro), by + (r - 22) * math.sin(giro)),
                  (bx - (r - 22) * math.cos(giro), by - (r - 22) * math.sin(giro))], 5, C['gris'], wob=0.5)
        lz.circulo(bx, by, 9, 3, relleno=C['tinta'], wob=0)
    else:
        lz.k += 4


# ------------------------------------------------------------- escenas
def d_portada(lz, t):
    p = aparece(t, 0.6, 1.6)
    ang = -0.55 + math.sin(t * 1.5) * 0.04
    lapicero(lz, 640, 900, 0.82, ang, p)
    # estrellitas
    for i, (x, y) in enumerate([(380, 640), (880, 700), (900, 1060)]):
        q = rebote(aparece(t, 1.8 + i * .25, .4))
        if q > 0:
            s = 22 * q
            lz.linea([(x - s, y), (x + s, y)], 6, C['naranja'])
            lz.linea([(x, y - s), (x, y + s)], 6, C['naranja'])
        else:
            lz.k += 2


def d_piezas(lz, t):
    cx, cy = 600, 790
    sep = suave(aparece(t, 1.4, 0.6)) * 55
    et = (aparece(t, .1, .5), aparece(t, .4, .5), aparece(t, .7, .5), aparece(t, 1.0, .5))
    lapicero(lz, cx, cy, 0.9, 0, etapas=et, cap_dy=-sep / 0.9)
    lz.etiqueta('capuchón', (860, 420), (690, 480 - sep), aparece(t, 1.5, .7), 40, curva=-.25)
    lz.etiqueta('cuerpo', (395, 640), (540, 680), aparece(t, 2.0, .7), 40, curva=.25)
    lz.etiqueta('carga\nde tinta', (850, 780), (615, 840), aparece(t, 2.6, .7), 40, curva=-.2)
    lz.etiqueta('punta +\nbolita', (850, 1080), (614, 1137), aparece(t, 3.3, .7), 40, curva=.2)


def d_bolita(lz, t):
    cx, cy, r = 610, 700, 265
    pz = aparece(t, .2, .6)
    zoom(lz, cx, cy, r, pz)
    punta_zoom(lz, cx, cy + 90, t, aparece(t, .6, 1.0), tinta_alto=300)
    # flecha de giro
    pa = aparece(t, 2.2, .8)
    if pa > 0:
        pts = [(cx + 135 * math.cos(a), cy + 90 + 135 * math.sin(a))
               for a in [math.radians(200 + i * 7 * pa) for i in range(21)]]
        lz.linea(pts, 6, C['rojo'])
        ex, ey = pts[-1]
        a = math.atan2(ey - pts[-3][1], ex - pts[-3][0])
        for s in (2.5, -2.5):
            lz.linea([(ex, ey), (ex + 22 * math.cos(a + s), ey + 22 * math.sin(a + s))], 6, C['rojo'])
    else:
        lz.k += 3
    lz.etiqueta('¡gira!', (420, 1060), (cx - 120, cy + 190), aparece(t, 2.6, .7), 42, C['rojo'], curva=.3)
    lz.etiqueta('no cabe\npor el hueco', (800, 1080), (cx + 78, cy + 155), aparece(t, 3.6, .7), 36, curva=-.25)


def d_tinta(lz, t):
    x0, x1 = 560, 680
    top, bot = 470, 990
    nivel = lerp(600, 640, aparece(t, 1.0, 5.0))
    ptubo = aparece(t, .2, .8)
    # tinta
    if ptubo > .5:
        lz.mancha([(x0 + 4, nivel), (x1 - 4, nivel), (x1 - 4, bot), (x0 + 4, bot)], C['azul'])
        lz.mancha([(x0 + 4, bot), (x1 - 4, bot), (640, 1075), (600, 1075)], C['azul'])
        # partículas bajando
        for k in range(10):
            fy = ((t * 70 + k * 53) % (bot - nivel - 20)) + nivel + 10
            fx = x0 + 20 + (k * 37) % 80
            lz.mancha([(fx - 5, fy), (fx + 5, fy), (fx + 5, fy + 14), (fx - 5, fy + 14)], C['azul_claro'])
    else:
        lz.k += 12
    lz.linea([(x0, top), (x0, bot), (600, 1078)], 7, p=ptubo)
    lz.linea([(x1, top), (x1, bot), (640, 1078)], 7, p=ptubo)
    lz.circulo(620, 1090, 14, 5, p=ptubo, relleno=C['gris'])
    # gravedad
    lz.flecha((440, 610), (440, 960), 0, 9, C['rojo'], aparece(t, 1.3, .8), 30)
    lz.texto('gravedad', 440, 560, 42, C['rojo'], p=aparece(t, 1.3, .6))
    # aire
    pa = aparece(t, 3.0, .6)
    for k in range(4):
        fase = (t * 0.9 + k * .25) % 1
        y = lerp(360, nivel - 30, fase)
        if pa > 0:
            lz.circulo(620 + math.sin(fase * 6 + k) * 18, y, 13 + k % 2 * 4, 4, C['gris'], relleno=C['blanco'])
        else:
            lz.k += 1
    lz.etiqueta('entra\naire', (850, 420), (660, 440), aparece(t, 3.2, .7), 40, curva=.25)
    # mini lapicero boca arriba
    pm = aparece(t, 4.8, .6)
    lz.etiqueta('boca arriba\nfalla', (840, 860), None, pm, 32)
    lapicero(lz, 840, 1060, 0.26, math.pi, pm, capuchon=False)


def d_rueda(lz, t):
    papel_y = 1000
    avance = aparece(t, .8, 5.2)
    bx = lerp(380, 820, avance)
    r = 90
    by = papel_y - r - 4
    # papel
    lz.rect(300, papel_y, 1000, papel_y + 70, 5, p=aparece(t, .1, .5), relleno=C['blanco'], radio=6)
    # rastro de tinta
    if bx > 330 and t > .8:
        lz.linea([(330, papel_y - 2), (bx, papel_y - 2)], 14, C['azul'], wob=1.2)
    else:
        lz.k += 1
    punta_zoom(lz, bx, by, t, aparece(t, .2, .7), giro=(bx - 380) / r, r=r, tinta_alto=380)
    lz.flecha((bx - 60, 470), (bx + 120, 470), 0, 8, C['rojo'], aparece(t, 1.2, .5), 28)
    lz.texto('mueves la mano', bx + 30, 420, 36, C['rojo'], p=aparece(t, 1.2, .5))
    lz.etiqueta('la tinta queda\nen el papel', (560, 1150), (420, papel_y + 4), aparece(t, 3.2, .7), 36, curva=-.2)


def d_seca(lz, t):
    # hoja con escritura
    lz.rect(360, 390, 980, 640, 6, p=aparece(t, .1, .5), relleno=C['blanco'], radio=10, sombra=True)
    pe = aparece(t, .5, 2.0)
    pts = []
    for i in range(160):
        u = i / 159
        x = 420 + u * 380
        y = 520 + math.sin(u * 30) * 34 * (0.7 + 0.3 * math.sin(u * 7)) - abs(math.sin(u * 15)) * 18
        pts.append((x, y))
    lz.linea(pts, 7, C['azul'], p=pe, wob=1.5)
    pc = aparece(t, 2.4, .5)
    lz.linea([(850, 515), (880, 550), (935, 470)], 11, C['verde'], p=pc)
    lz.texto('¡seca en segundos!', 670, 600, 34, C['verde'], p=aparece(t, 2.6, .6))
    # punta sellada
    cx, cy = 640, 930
    pp = aparece(t, 3.0, .6)
    lz.poligono([(cx - 120, 700), (cx + 120, 700), (cx + 45, cy - 10), (cx - 45, cy - 10)], 6, p=pp,
                relleno=C['metal'])
    lz.circulo(cx, cy + 10, 48, 7, p=pp, relleno=C['gris'])
    lz.etiqueta('tapón', (870, 900), (cx + 52, cy + 10), aparece(t, 3.6, .6), 42, curva=-.2)
    # gota tachada
    pg = aparece(t, 4.2, .5)
    gx, gy = cx, cy + 120
    lz.poligono([(gx, gy - 38), (gx + 26, gy + 4), (gx + 20, gy + 26), (gx, gy + 34), (gx - 20, gy + 26),
                 (gx - 26, gy + 4)], 5, C['azul'], p=pg, relleno=C['azul_claro'])
    px = aparece(t, 4.6, .4)
    lz.linea([(gx - 50, gy - 50), (gx + 50, gy + 50)], 10, C['rojo'], p=px)
    lz.linea([(gx + 50, gy - 50), (gx - 50, gy + 50)], 10, C['rojo'], p=aparece(t, 4.8, .3))


def d_dato(lz, t):
    # periódico
    pp = aparece(t, .2, .7)
    hoja = rotar([(-250, -190), (250, -190), (250, 190), (-250, 190)], -0.06, 590, 620)
    lz.poligono(hoja, 6, p=pp, relleno=C['blanco'], sombra=True)
    lz.texto('DIARIO', 580, 490, 58, p=aparece(t, .7, .4))
    for k in range(5):
        y = 560 + k * 42
        w = 360 if k % 3 else 300
        a = rotar([(-w / 2, 0), (w / 2, 0)], -0.06, 590, y + 10)
        lz.linea(a, 8, C['gris'], p=aparece(t, .9 + k * .12, .3))
    # bombillo
    pb = rebote(aparece(t, 1.8, .6))
    bx, by = 890, 480
    if pb > 0:
        lz.circulo(bx, by, 52 * pb, 6, relleno=C['amarillo'])
        lz.rect(bx - 24 * pb, by + 46 * pb, bx + 24 * pb, by + 80 * pb, 5, relleno=C['gris_claro'], radio=6)
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.55
            lz.linea([(bx + 70 * math.cos(a), by + 70 * math.sin(a)),
                      (bx + 98 * math.cos(a), by + 98 * math.sin(a))], 6, C['naranja'])
    else:
        lz.k += 7
    # sello 1938
    ps = rebote(aparece(t, 3.2, .5))
    if ps > 0:
        lz.circulo(620, 960, 110 * ps, 8, C['rojo'], relleno=C['papel'])
        lz.texto('1938', 620, 960, 70 * ps, C['rojo'])
    else:
        lz.k += 2


def d_cierre(lz, t):
    # cafetera moka
    p1 = aparece(t, .4, .8)
    cx, cy = 470, 640
    lz.poligono([(cx - 70, cy - 120), (cx + 70, cy - 120), (cx + 40, cy), (cx - 40, cy)], 6, p=p1,
                relleno=C['metal'])
    lz.poligono([(cx - 40, cy), (cx + 40, cy), (cx + 75, cy + 130), (cx - 75, cy + 130)], 6, p=p1,
                relleno=C['metal'])
    lz.linea([(cx + 70, cy - 100), (cx + 115, cy - 90), (cx + 110, cy - 10), (cx + 55, cy + 10)], 7, p=p1)
    lz.poligono([(cx - 20, cy - 145), (cx + 20, cy - 145), (cx + 10, cy - 120), (cx - 10, cy - 120)], 5,
                p=p1, relleno=C['tinta'])
    for k in range(3):
        lz.linea([(cx - 30 + k * 30, cy - 175 - j * 12 + math.sin(t * 4 + k + j) * 6) for j in range(6)],
                 4, C['gris'], p=aparece(t, 1.0 + k * .15, .5))
    # avión
    p2 = aparece(t, 1.0, .8)
    ax, ay = 780 + math.sin(t * 1.4) * 10, 560 + math.sin(t * 2) * 8
    lz.poligono([(ax - 150, ay), (ax + 130, ay - 8), (ax + 160, ay + 10), (ax + 120, ay + 26), (ax - 150, ay + 26)],
                6, p=p2, relleno=C['blanco'])
    lz.poligono([(ax - 10, ay + 10), (ax + 40, ay + 10), (ax - 50, ay + 110), (ax - 80, ay + 110)], 6, p=p2,
                relleno=C['celeste'])
    lz.poligono([(ax - 130, ay), (ax - 100, ay), (ax - 150, ay - 70), (ax - 170, ay - 70)], 6, p=p2,
                relleno=C['celeste'])
    lz.circulo(ax - 30, ay + 62, 22, 5, p=p2, relleno=C['gris'])
    # signos de pregunta
    for i, (x, y) in enumerate([(620, 400), (330, 880), (900, 830)]):
        q = rebote(aparece(t, 1.8 + i * .3, .4))
        lz.texto('?', x, y + math.sin(t * 3 + i) * 8, 90 * max(q, .01), C['azul'], p=float(q > 0))
    lz.texto('¿Y AHORA?', 640, 1000, 64, C['rojo'], p=aparece(t, 2.6, .6))


ESCENAS = [
    dict(tipo='portada', dur=4.5, dibujo=d_portada,
         texto='Lo usas todos los días… pero ¿sabes qué pasa *por dentro*?',
         monigote=dict(apunta=(560, 900)), sonidos=[(0.7, 'pop'), (1.9, 'pop')]),
    dict(tipo='piezas', titulo='4 piezas clave', dur=7.0, dibujo=d_piezas,
         texto='Tiene 4 piezas: *capuchón*, *cuerpo*, *carga de tinta* y una *punta con bolita*.',
         monigote=dict(apunta=(520, 640)),
         sonidos=[(1.5, 'pop'), (2.0, 'pop'), (2.6, 'pop'), (3.3, 'pop')]),
    dict(tipo='paso', titulo='La bolita', dur=6.5, dibujo=d_bolita,
         texto='En la punta hay una *bolita de metal* de 1 mm o menos. Puede *girar*, pero no salirse.',
         monigote=dict(apunta=(480, 800), expresion='sorpresa'), sonidos=[(2.6, 'pop'), (3.6, 'pop')]),
    dict(tipo='paso', titulo='La tinta baja', dur=7.0, dibujo=d_tinta,
         texto='La tinta es espesa: la *gravedad* la lleva hacia la bolita y por arriba *entra aire* para que siga bajando.',
         monigote=dict(apunta=(440, 760)), sonidos=[(1.3, 'pop'), (3.2, 'pop'), (4.8, 'pop')]),
    dict(tipo='paso', titulo='Rueda y pinta', dur=7.0, dibujo=d_rueda,
         texto='Al escribir, la bolita *rueda*: se moja de tinta por dentro y la deja en el papel. ¡Como un *roll-on*!',
         monigote=dict(apunta=(420, 960)), sonidos=[(1.2, 'pop'), (3.2, 'pop')]),
    dict(tipo='paso', titulo='Seca y se sella', dur=6.5, dibujo=d_seca,
         texto='La tinta *seca rapidísimo* y, cuando paras, la bolita *tapa la salida* para que no se derrame.',
         monigote=dict(apunta=(560, 900), expresion='guiño'),
         sonidos=[(2.4, 'ding'), (3.6, 'pop'), (4.6, 'pop')]),
    dict(tipo='dato', titulo='Nació en un periódico', dur=7.0, dibujo=d_dato,
         texto='Lo patentó *László Bíró*, periodista húngaro, en *1938*, inspirado en la tinta de periódico.',
         monigote=dict(expresion='sorpresa', mira=(600, 560)), sonidos=[(1.8, 'ding'), (3.2, 'pop')]),
    dict(tipo='cierre', titulo='¿Qué explico ahora?', dur=6.0, dibujo=d_cierre,
         texto='¿La *cafetera*? ¿Un *motor de avión*? ¡Déjalo en los comentarios y lo dibujo!',
         monigote=dict(saluda=True), sonidos=[(1.8, 'pop'), (2.1, 'pop'), (2.4, 'pop')]),
]
