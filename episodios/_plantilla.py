"""PLANTILLA EN BLANCO — copia este archivo, renómbralo (ej. cafetera.py) y rellénalo.

Render:   python3 comofunciona.py episodios/cafetera.py
Revisar:  python3 comofunciona.py episodios/cafetera.py --fotos 2:3.5   (escena 2, segundo 3.5)
"""
import math
from comofunciona import C, aparece, rebote, rotar, lerp, suave

TITULO = 'LA CAFETERA'          # sale en la portada: ¿CÓMO FUNCIONA LA CAFETERA?
SERIE = 'CÓMO FUNCIONA'


# Dibuja tu objeto UNA vez como función, y reutilízala en varias escenas.
def objeto(lz, cx, cy, p=1):
    lz.rect(cx - 120, cy - 160, cx + 120, cy + 160, 6, p=p, relleno=C['metal'], sombra=True)


# Cada escena = una función dibujo(lz, t). t = segundos dentro de la escena.
# Usa aparece(t, inicio, duración) para que las cosas se dibujen solas.
def d_portada(lz, t):
    objeto(lz, 600, 860, aparece(t, 0.6, 1.2))


def d_paso1(lz, t):
    objeto(lz, 600, 760, aparece(t, 0.2, 0.8))
    lz.etiqueta('agua', (860, 520), (640, 700), aparece(t, 1.5, .7))
    lz.flecha((420, 600), (420, 900), 0, 8, C['rojo'], aparece(t, 2.2, .6))


def d_cierre(lz, t):
    lz.texto('¿Y AHORA?', 620, 800, 72, C['rojo'], p=aparece(t, 1.0, .6))


ESCENAS = [
    dict(tipo='portada', dur=4.5, dibujo=d_portada,
         texto='La usas cada mañana… ¿pero sabes qué pasa *por dentro*?',
         monigote=dict(apunta=(560, 860))),
    dict(tipo='paso', titulo='Título del paso', dur=6.5, dibujo=d_paso1,
         texto='Aquí va lo que dices en voz alta. Las *palabras clave* van entre asteriscos.',
         monigote=dict(apunta=(520, 760)), sonidos=[(1.5, 'pop'), (2.2, 'pop')]),
    # tipo='piezas' (chip LAS PIEZAS), tipo='dato' (chip ¿SABÍAS QUE…?) y más tipo='paso'
    dict(tipo='cierre', titulo='¿Qué explico ahora?', dur=6.0, dibujo=d_cierre,
         texto='¡Déjalo en los *comentarios*!', monigote=dict(saluda=True)),
]
