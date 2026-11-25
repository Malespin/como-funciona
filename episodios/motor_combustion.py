"""Episodio: ¿Cómo funciona un motor de combustión? (motor de carro, 4 tiempos, gasolina)"""
import math
from comofunciona import C, aparece, rebote, rotar, lerp, suave, insignia

TITULO = 'UN MOTOR DE\nCOMBUSTIÓN'
SERIE = 'CÓMO FUNCIONA'
MINIATURA_EXTRA = '¡A PURA EXPLOSIÓN!'
MINIATURA_T = 21.73   # momento de la chispa

YOUTUBE = dict(
    titulo='¿Cómo funciona el motor de un carro? Los 4 tiempos en 1 minuto 🚗💥 #shorts',
    descripcion=(
        'El motor de tu carro funciona a base de pequeñas explosiones. Así es un ciclo de 4 tiempos, '
        'explicado con monigotes:\n\n'
        '1. Admisión: el pistón baja y aspira aire con gasolina.\n'
        '2. Compresión: las válvulas se cierran y el pistón aprieta la mezcla.\n'
        '3. Explosión: la bujía lanza una chispa y la mezcla empuja el pistón hacia abajo.\n'
        '4. Escape: el pistón sube y saca los gases quemados.\n'
        '5. La biela y el cigüeñal convierten ese sube y baja en giro para las ruedas.\n\n'
        '💡 Dato: a 3,000 rpm cada cilindro repite el ciclo 25 veces por segundo. '
        'Se llama ciclo Otto, por Nikolaus Otto, que construyó este motor en 1876.\n\n'
        '💬 ¿Qué explico ahora: el motor de avión o el carro eléctrico? Déjalo en los comentarios.\n\n'
        '#Shorts #CómoFunciona #Motor #Mecánica #Carros #Ciencia'),
    etiquetas=['cómo funciona un motor', 'motor de combustión', 'motor de 4 tiempos', 'cómo funciona el motor de un carro',
               'ciclo Otto', 'pistón', 'cigüeñal', 'bujía', 'mecánica automotriz', 'mecánica básica',
               'motor explicado', 'carros', 'explicado fácil', 'shorts educativos', 'ciencia'],
)

# ------------------------------------------------------------- geometría (coordenadas locales)
CX, REF_Y = 600, 700          # punto de referencia para escalar
HEAD_Y = 470                  # techo del cilindro
CRANK = (600, 1050)
R_CIG, L_BIELA = 110, 380
ALTO_PISTON = 110
LEVA = 34                     # cuánto bajan las válvulas al abrir

MEZCLA = (196, 232, 196)
MEZCLA_FUERTE = (120, 200, 140)
HUMO = (178, 178, 186)
FUEGO = (255, 170, 50)


def pos_piston(ang):
    """Ángulo del cigüeñal (grados, 0 = arriba) → (y del techo del pistón, punto del muñón)."""
    a = math.radians(ang)
    px, py = CRANK[0] + R_CIG * math.sin(a), CRANK[1] - R_CIG * math.cos(a)
    pin_y = py - math.sqrt(L_BIELA ** 2 - (px - CRANK[0]) ** 2)
    return pin_y - 60, (px, py), pin_y


def valvulas(ang):
    a = ang % 720

    def lift(x0, x1):
        if not (x0 < a < x1):
            return 0.0
        u = (a - x0) / (x1 - x0)
        return math.sin(u * math.pi) ** 0.6
    return lift(0, 180), lift(540, 720)


def motor(lz, ang, t, ox=600, oy=760, e=0.9, p=1.0, etapas=None, gas=True, chispa=False, flujo=True):
    """Corte de un cilindro. Todo se mueve según 'ang' (0-720°, un ciclo completo)."""
    def T(pts):
        return [(ox + (x - CX) * e, oy + (y - REF_Y) * e) for x, y in pts]

    def P(x, y):
        return T([(x, y)])[0]

    if etapas is None:
        etapas = (aparece(p, 0, .35), aparece(p, .2, .35), aparece(p, .4, .35), aparece(p, .6, .4))
    p_bloque, p_piston, p_cig, p_cabeza = etapas
    a = ang % 720
    yp, pin, pin_y = pos_piston(a)
    adm, esc = valvulas(a)

    # --- gas en la cámara
    if gas and p_piston > 0.6:
        if a < 180:
            col = MEZCLA
        elif a < 360:
            col = tuple(int(lerp(m, f, (a - 180) / 180)) for m, f in zip(MEZCLA, MEZCLA_FUERTE))
        elif a < 540:
            u = (a - 360) / 180
            col = tuple(int(lerp(f, h, suave(u))) for f, h in zip(FUEGO, (236, 196, 160)))
        else:
            u = (a - 540) / 180
            col = tuple(int(lerp(h, c, u * 0.7)) for h, c in zip(HUMO, C['papel']))
        lz.mancha(T([(472, HEAD_Y), (728, HEAD_Y), (728, yp + 2), (472, yp + 2)]), col)
        # llamas
        if 360 <= a < 470:
            fuerza = 1 - (a - 360) / 110
            pts = []
            for k in range(13):
                x = 480 + k * 20
                alto = (yp - HEAD_Y) * (0.35 + 0.6 * fuerza * (0.5 + 0.5 * math.sin(k * 2.1 + t * 20)))
                pts.append((x, yp - alto if k % 2 else yp - alto * 0.5))
            lz.mancha(T([(476, yp)] + pts + [(724, yp)]), C['amarillo'])
        else:
            lz.k += 1
    else:
        lz.k += 2

    # --- cigüeñal y biela
    cx, cy = CRANK
    lz.circulo(*P(cx, cy), 140 * e, 6, p=p_cig, relleno=C['gris_claro'])
    lz.circulo(*P(cx, cy), 22 * e, 5, p=p_cig, relleno=C['gris'])
    if p_cig > 0.5:
        a1 = P(pin[0], pin[1])
        a2 = P(CX, pin_y)
        lz.linea([a1, a2], 34 * e, C['tinta'], wob=0.8)
        lz.linea([a1, a2], 20 * e, C['metal'], wob=0.8)
        lz.circulo(*a1, 20 * e, 5, relleno=C['gris'], wob=0.5)
        # brazo del cigüeñal
        lz.linea([P(cx, cy), a1], 10 * e, C['tinta'], wob=0.5)
    else:
        lz.k += 4

    # --- pistón
    lz.rect(*P(476, yp), *P(724, yp + ALTO_PISTON), 6, p=p_piston, relleno=C['metal'], radio=8)
    if p_piston > 0.7:
        for dy in (20, 36):
            lz.linea(T([(480, yp + dy), (720, yp + dy)]), 4, C['tinta'], wob=0.6)
        lz.circulo(*P(CX, pin_y), 16 * e, 5, relleno=C['gris'], wob=0.4)
    else:
        lz.k += 3

    # --- paredes del cilindro
    for x0, x1 in ((420, 472), (728, 780)):
        lz.poligono(T([(x0, HEAD_Y), (x1, HEAD_Y), (x1, 900), (x0, 900)]), 6, p=p_bloque,
                    relleno=(186, 192, 204))

    # --- culata (cabeza) con conductos
    for x0, x1 in ((420, 495), (565, 635), (705, 780)):
        lz.poligono(T([(x0, 400), (x1, 400), (x1, HEAD_Y), (x0, HEAD_Y)]), 6, p=p_cabeza,
                    relleno=(186, 192, 204))
    for x0, x1, dx in ((495, 565, -40), (635, 705, 40)):
        lz.linea(T([(x0, 400), (x0 + dx, 300)]), 6, p=p_cabeza)
        lz.linea(T([(x1, 400), (x1 + dx, 300)]), 6, p=p_cabeza)

    # --- flujo: mezcla entrando / humo saliendo
    if flujo and p_cabeza > 0.8:
        if adm > 0.05:
            for k in range(9):
                u = (t * 0.9 + k / 9) % 1
                x = lerp(490, 520 + (k % 3) * 12, u) + math.sin(k * 3 + u * 6) * 10
                y = lerp(300, HEAD_Y + 30 + (yp - HEAD_Y) * 0.6 * u, u)
                lz.circulo(*P(x, y), 9 * e, 3, (70, 150, 90), relleno=MEZCLA, wob=0.3)
        else:
            lz.k += 9
        if esc > 0.05:
            for k in range(6):
                u = (t * 0.8 + k / 6) % 1
                x = lerp(670, 720, u) + math.sin(k * 2 + u * 5) * 12
                y = lerp(HEAD_Y + 10, 290, u)
                lz.circulo(*P(x, y), (12 + 10 * u) * e, 3, C['gris'], relleno=HUMO, wob=0.6)
        else:
            lz.k += 6
    else:
        lz.k += 15

    # --- válvulas
    for xc, lift in ((530, adm), (670, esc)):
        d = lift * LEVA
        lz.linea(T([(xc, 280), (xc, 462 + d)]), 7, p=p_cabeza, wob=0.4)
        lz.linea(T([(xc - 14, 280), (xc + 14, 280)]), 7, p=p_cabeza, wob=0.4)
        lz.poligono(T([(xc - 42, 462 + d), (xc + 42, 462 + d), (xc + 34, 474 + d), (xc - 34, 474 + d)]),
                    5, p=p_cabeza, relleno=C['metal'], wob=0.5)

    # --- bujía
    lz.rect(*P(586, 290), *P(614, 385), 5, p=p_cabeza, relleno=C['blanco'], radio=6)
    lz.rect(*P(578, 380), *P(622, 410), 5, p=p_cabeza, relleno=C['gris'], radio=3)
    lz.linea(T([(600, 410), (600, 484)]), 5, p=p_cabeza, wob=0.3)
    if chispa:
        sx, sy = P(600, 492)
        lz.circulo(sx, sy, 46 * e, 0.1, C['amarillo'], relleno=C['amarillo'], wob=3)
        for k in range(6):
            ang_r = k * math.pi / 3 + t * 3
            lz.linea([(sx + 20 * e * math.cos(ang_r), sy + 20 * e * math.sin(ang_r)),
                      (sx + 34 * e * math.cos(ang_r + .3), sy + 34 * e * math.sin(ang_r + .3)),
                      (sx + 62 * e * math.cos(ang_r), sy + 62 * e * math.sin(ang_r))], 5, C['naranja'], wob=1)
    else:
        lz.k += 7

    return dict(
        adm=P(530, 300), esc=P(670, 300), valvula_adm=P(530, 470), bujia=P(614, 330),
        camara=P(600, (HEAD_Y + yp) / 2), piston=P(724, yp + 50), biela=P((pin[0] + CX) / 2, (pin[1] + pin_y) / 2),
        cig=P(cx + 110, cy + 60), cilindro=P(420, 700), centro_cig=P(cx, cy),
        flecha_x=ox + 230 * e, yp=oy + (yp - REF_Y) * e,
    )


def flecha_piston(lz, k, sube, p):
    """Flecha roja junto al cilindro: sube o baja."""
    x = k['flecha_x'] + 20
    y0, y1 = (760, 540) if sube else (540, 760)
    lz.flecha((x, y0), (x, y1), 0, 9, C['rojo'], p, 28)


def chip_tiempo(lz, n, nombre, t):
    lz.k += 2  # (reservado: el título de la escena ya nombra el tiempo)


# ------------------------------------------------------------- escenas
def d_portada(lz, t):
    p = aparece(t, 0.5, 1.4)
    ang = (t * 150) % 720
    k = motor(lz, ang, t, ox=640, oy=990, e=0.6, p=p, chispa=p >= 1 and 360 <= ang < 385)
    if p >= 1 and 360 <= ang < 470:
        x, y = 900, 760
        q = rebote(aparece(ang, 360, 30))
        pts = []
        for i in range(16):
            rr = (70 if i % 2 else 36) * q
            a = i * math.pi / 8
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        lz.poligono(pts, 5, relleno=C['amarillo'])
        lz.texto('¡PUM!', x, y, 34 * q, C['rojo'])
    else:
        lz.k += 2


def d_piezas(lz, t):
    et = (aparece(t, .1, .6), aparece(t, .5, .6), aparece(t, .8, .6), aparece(t, 1.1, .6))
    k = motor(lz, 90, t, etapas=et, gas=False, flujo=False)
    lz.etiqueta('cilindro', (300, 690), k['cilindro'], aparece(t, 1.6, .6), 38, curva=.2)
    lz.etiqueta('pistón', (880, 600), k['piston'], aparece(t, 2.1, .6), 38, curva=-.2)
    lz.etiqueta('bujía', (860, 330), k['bujia'], aparece(t, 2.6, .6), 38, curva=-.25)
    lz.etiqueta('válvulas', (300, 360), k['valvula_adm'], aparece(t, 3.1, .6), 38, curva=.25)
    lz.etiqueta('biela', (880, 860), k['biela'], aparece(t, 3.6, .6), 38, curva=-.2)
    lz.etiqueta('cigüeñal', (860, 1150), k['cig'], aparece(t, 4.1, .6), 38, curva=.2)


def d_admision(lz, t):
    u = aparece(t, 0.8, 3.6)
    k = motor(lz, lerp(0, 179, u), t)
    chip_tiempo(lz, 1, 'ADMISIÓN', t)
    flecha_piston(lz, k, False, aparece(t, 1.0, .6))
    lz.etiqueta('aire +\ngasolina', (300, 560), (k['adm'][0] - 30, k['adm'][1] + 20), aparece(t, 1.8, .7), 38,
                curva=.25)


def d_compresion(lz, t):
    u = aparece(t, 0.8, 3.6)
    k = motor(lz, lerp(181, 359, u), t)
    chip_tiempo(lz, 2, 'COMPRESIÓN', t)
    flecha_piston(lz, k, True, aparece(t, 1.0, .6))
    lz.etiqueta('válvulas\ncerradas', (300, 560), (k['valvula_adm'][0] - 10, k['valvula_adm'][1] + 6),
                aparece(t, 1.4, .7), 36, curva=.2)
    pa = aparece(t, 3.6, .6)
    lz.etiqueta('¡apretada!', (880, 380), k['camara'], pa, 38, C['rojo'], curva=-.3)


def d_explosion(lz, t):
    u = aparece(t, 1.6, 1.4)
    ang = 360 + 179 * suave(u) ** 0.7 if t >= 1.2 else 360
    chispa = 1.2 <= t < 1.9
    k = motor(lz, ang, t, chispa=chispa)
    chip_tiempo(lz, 3, 'EXPLOSIÓN', t)
    lz.etiqueta('chispa', (860, 340), k['bujia'], aparece(t, 0.7, .6), 38, curva=-.25)
    if t >= 1.2:
        q = rebote(aparece(t, 1.2, .3)) * (1 - aparece(t, 2.6, .4))
        x, y = 880, 560
        pts = []
        for i in range(16):
            rr = (100 if i % 2 else 52) * q
            a = i * math.pi / 8 + 0.2
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        if q > 0.02:
            lz.poligono(pts, 6, relleno=C['amarillo'])
            lz.texto('¡PUM!', x, y, 46 * q, C['rojo'])
        else:
            lz.k += 2
    else:
        lz.k += 2
    flecha_piston(lz, k, False, aparece(t, 1.7, .4))
    lz.texto('¡empuja!', k['flecha_x'] + 40, 820, 38, C['rojo'], p=aparece(t, 2.0, .5))


def d_escape(lz, t):
    u = aparece(t, 0.8, 3.6)
    k = motor(lz, lerp(541, 719, u), t)
    chip_tiempo(lz, 4, 'ESCAPE', t)
    flecha_piston(lz, k, True, aparece(t, 1.0, .6))
    lz.etiqueta('gases\nquemados', (880, 380), (k['esc'][0] + 30, k['esc'][1] - 10), aparece(t, 2.0, .7), 38,
                curva=-.25)


def d_giro(lz, t):
    vel = 260 * aparece(t, 0.3, 1.2)
    ang = (t * vel) % 720 if t > 0.3 else 0
    k = motor(lz, (130 * t + 0.5 * vel * t) % 720, t, ox=520, oy=720, e=0.78,
              chispa=False)
    cx, cy = k['centro_cig']
    # flecha de giro alrededor del cigüeñal
    pa = aparece(t, 1.5, .8)
    if pa > 0:
        pts = [(cx + 135 * math.cos(a), cy + 135 * math.sin(a))
               for a in [math.radians(-150 + i * 9 * pa) for i in range(21)]]
        lz.linea(pts, 7, C['rojo'])
        ex, ey = pts[-1]
        a = math.atan2(ey - pts[-3][1], ex - pts[-3][0])
        for s in (2.5, -2.5):
            lz.linea([(ex, ey), (ex + 24 * math.cos(a + s), ey + 24 * math.sin(a + s))], 7, C['rojo'])
    else:
        lz.k += 3
    # eje y rueda
    pr = aparece(t, 2.6, .8)
    rx, ry = 860, cy
    lz.linea([(cx + 20, cy), (rx - 90, ry)], 10, p=pr)
    lz.circulo(rx, ry, 95, 9, p=pr, relleno=C['tinta'])
    lz.circulo(rx, ry, 55, 5, p=pr, relleno=C['metal'])
    if pr > .6:
        g = t * 4
        for j in range(5):
            a = g + j * 2 * math.pi / 5
            lz.linea([(rx, ry), (rx + 50 * math.cos(a), ry + 50 * math.sin(a))], 5, wob=0.4)
    else:
        lz.k += 5
    lz.texto('a las ruedas', rx, ry + 140, 36, C['rojo'], p=aparece(t, 3.2, .5))


def d_dato(lz, t):
    cx, cy, r = 600, 800, 290
    pd = aparece(t, .2, .8)
    # dial
    lz.arco(cx, cy, r, math.pi, 2 * math.pi, 10, p=pd, wob=1.2)
    for n in range(9):
        a = math.pi + n * math.pi / 8
        q = aparece(t, .5 + n * .06, .2)
        lz.linea([(cx + (r - 10) * math.cos(a), cy + (r - 10) * math.sin(a)),
                  (cx + (r - 45) * math.cos(a), cy + (r - 45) * math.sin(a))], 7, p=q)
        lz.texto(str(n), cx + (r - 85) * math.cos(a), cy + (r - 85) * math.sin(a), 38,
                 C['rojo'] if n >= 7 else C['tinta'], p=q)
    lz.texto('×1000 rpm', cx, cy + 50, 30, C['gris'], p=aparece(t, 1.0, .4))
    # aguja a 3,000 rpm con temblor
    va = aparece(t, 1.3, 1.0)
    rpm = 3 * rebote(va) + (math.sin(t * 30) * 0.04 if va >= 1 else 0)
    a = math.pi + rpm * math.pi / 8
    lz.linea([(cx, cy), (cx + (r - 70) * math.cos(a), cy + (r - 70) * math.sin(a))], 9, C['rojo'], p=float(t > 1.2))
    lz.circulo(cx, cy, 20, 5, p=pd, relleno=C['tinta'])
    # contador de explosiones
    pc = aparece(t, 2.6, .5)
    lz.texto('25 explosiones', cx, cy + 125, 66, C['naranja'], p=pc)
    lz.texto('por segundo · cada cilindro', cx, cy + 198, 38, C['tinta'], p=aparece(t, 3.0, .5))
    if t > 3.0:
        for j in range(4):
            fase = (t * 2.5 + j * 0.25) % 1
            if fase < 0.3:
                x = 330 + j * 180
                y = 470 + (j % 2) * 40
                q = rebote(fase / 0.3)
                pts = [(x + (34 if i % 2 else 16) * q * math.cos(i * math.pi / 6),
                        y + (34 if i % 2 else 16) * q * math.sin(i * math.pi / 6)) for i in range(12)]
                lz.poligono(pts, 4, relleno=C['amarillo'])
            else:
                lz.k += 1
    else:
        lz.k += 4


def d_cierre(lz, t):
    # avión
    p2 = aparece(t, .4, .8)
    ax, ay = 760 + math.sin(t * 1.4) * 10, 520 + math.sin(t * 2) * 8
    lz.poligono([(ax - 150, ay), (ax + 130, ay - 8), (ax + 160, ay + 10), (ax + 120, ay + 26), (ax - 150, ay + 26)],
                6, p=p2, relleno=C['blanco'])
    lz.poligono([(ax - 10, ay + 10), (ax + 40, ay + 10), (ax - 50, ay + 110), (ax - 80, ay + 110)], 6, p=p2,
                relleno=C['celeste'])
    lz.poligono([(ax - 130, ay), (ax - 100, ay), (ax - 150, ay - 70), (ax - 170, ay - 70)], 6, p=p2,
                relleno=C['celeste'])
    lz.circulo(ax - 30, ay + 62, 22, 5, p=p2, relleno=C['gris'])
    # carro eléctrico
    p1 = aparece(t, 1.0, .8)
    cx, cy = 520, 800
    lz.poligono([(cx - 170, cy), (cx - 160, cy - 60), (cx - 80, cy - 70), (cx - 30, cy - 130), (cx + 90, cy - 130),
                 (cx + 140, cy - 70), (cx + 180, cy - 60), (cx + 185, cy)], 6, p=p1, relleno=(150, 220, 170))
    lz.circulo(cx - 95, cy + 5, 38, 6, p=p1, relleno=C['tinta'])
    lz.circulo(cx + 110, cy + 5, 38, 6, p=p1, relleno=C['tinta'])
    lz.poligono([(cx + 10, cy - 115), (cx - 15, cy - 70), (cx + 5, cy - 70), (cx - 10, cy - 30), (cx + 35, cy - 85),
                 (cx + 15, cy - 85), (cx + 30, cy - 115)], 4, p=aparece(t, 1.6, .4), relleno=C['amarillo'])
    for i, (x, y) in enumerate([(430, 420), (840, 760), (360, 1000)]):
        q = rebote(aparece(t, 1.8 + i * .3, .4))
        lz.texto('?', x, y + math.sin(t * 3 + i) * 8, 90 * max(q, .01), C['azul'], p=float(q > 0))
    lz.texto('¿Y AHORA?', 660, 1010, 64, C['rojo'], p=aparece(t, 2.6, .6))


ESCENAS = [
    dict(tipo='portada', dur=4.5, dibujo=d_portada,
         texto='Está en casi todos los carros… y funciona a base de pequeñas *explosiones*.',
         monigote=dict(apunta=(520, 900))),
    dict(tipo='piezas', titulo='Las piezas', dur=7.0, dibujo=d_piezas,
         texto='Sus piezas clave: *cilindro*, *pistón*, *bujía*, *válvulas*, *biela* y *cigüeñal*.',
         monigote=dict(apunta=(470, 700)),
         sonidos=[(1.6, 'pop'), (2.1, 'pop'), (2.6, 'pop'), (3.1, 'pop'), (3.6, 'pop'), (4.1, 'pop')]),
    dict(tipo='paso', titulo='Admisión', dur=6.5, dibujo=d_admision,
         texto='Primero, la *admisión*: el pistón baja y aspira una mezcla de *aire y gasolina*.',
         monigote=dict(apunta=(470, 560)), sonidos=[(1.8, 'pop')]),
    dict(tipo='paso', titulo='Compresión', dur=6.5, dibujo=d_compresion,
         texto='Luego, la *compresión*: las válvulas se cierran y el pistón sube *apretando* la mezcla.',
         monigote=dict(apunta=(470, 600)), sonidos=[(1.4, 'pop'), (3.6, 'pop')]),
    dict(tipo='paso', titulo='Explosión', dur=6.5, dibujo=d_explosion,
         texto='Ahora, la *explosión*: la bujía lanza una *chispa*, la mezcla arde y empuja el pistón con fuerza.',
         monigote=dict(expresion='sorpresa', mira=(600, 500)),
         sonidos=[(0.7, 'pop'), (1.2, 'whoosh'), (1.25, 'ding')]),
    dict(tipo='paso', titulo='Escape', dur=6.5, dibujo=d_escape,
         texto='Por último, el *escape*: el pistón sube y saca los *gases quemados*. ¡Y vuelta a empezar!',
         monigote=dict(apunta=(560, 480)), sonidos=[(2.0, 'pop')]),
    dict(tipo='paso', titulo='Del pistón a las ruedas', dur=7.0, dibujo=d_giro,
         texto='La *biela* y el *cigüeñal* convierten ese sube y baja en *giro*, y ese giro mueve las ruedas.',
         monigote=dict(apunta=(420, 900), x=150), sonidos=[(1.5, 'pop'), (2.6, 'pop')]),
    dict(tipo='dato', titulo='¡Rapidísimo!', dur=7.0, dibujo=d_dato,
         texto='A *3,000 rpm*, cada cilindro repite estos 4 tiempos *25 veces por segundo*.',
         monigote=dict(expresion='sorpresa', mira=(600, 700)), sonidos=[(1.3, 'whoosh'), (2.6, 'ding')]),
    dict(tipo='cierre', titulo='¿Qué explico ahora?', dur=6.0, dibujo=d_cierre,
         texto='¿Un *motor de avión*? ¿Un *carro eléctrico*? ¡Déjalo en los comentarios y lo dibujo!',
         monigote=dict(saluda=True), sonidos=[(1.8, 'pop'), (2.1, 'pop'), (2.4, 'pop')]),
]
