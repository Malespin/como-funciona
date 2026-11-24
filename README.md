# CÓMO FUNCIONA — plantilla de videos verticales estilo monigote

## Flujo en la nube (sin instalar nada)
1. **Guion:** en `guiones/<episodio>.md` está el texto que debes leer.
2. **Graba** con el celular. Puedes grabar un solo audio dejando **2 segundos de silencio** entre escena y escena, o un audio por escena llamado `1`, `2`, `3`…
3. **Sube** la grabación a `voz/<episodio>/` desde GitHub (Add file → Upload files) y pulsa *Commit*.
4. GitHub fabrica el video solo (pestaña **Actions**, tarda unos 3–5 min) y lo guarda en `videos/<episodio>.mp4`.
   Cada escena dura lo que dura tu voz, la boca del monigote sigue tu volumen y el subtítulo avanza al ritmo de tu lectura.
5. **Para YouTube:** en `publicacion/<episodio>.md` están el título, la descripción y las etiquetas, listos para copiar. En `miniaturas/<episodio>.png` está la miniatura (1080×1920). Para definirlos tú, agrega `YOUTUBE = dict(titulo=..., descripcion=..., etiquetas=[...])` y `MINIATURA_EXTRA` en el episodio.
6. Para rehacer un video sin cambiar nada: Actions → *Hacer video* → *Run workflow* → escribe el nombre del episodio.

Si subes un episodio nuevo sin voz, sale `videos/<episodio>_sin_voz.mp4` con un ritmo pausado (`RITMO = 1.35`).

Genera Shorts de 1080×1920 a 30 fps, con estilo de cuaderno: trazos que tiemblan como si estuvieran hechos a mano, un monigote presentador con bufanda naranja, subtítulos con palabras resaltadas y efectos de sonido.

## Requisitos
- Python 3.9 o superior, con `pip install pillow numpy`
- `ffmpeg` en el PATH
- La fuente Comic Relief viene incluida en `fuentes/`

## Uso
```bash
python3 comofunciona.py episodios/lapicero.py                 # → lapicero.mp4
python3 comofunciona.py episodios/lapicero.py --fotos 3:4.0   # PNG de la escena 3 en el segundo 4
python3 comofunciona.py episodios/lapicero.py --escenas 2,3   # re-renderiza solo esas escenas y vuelve a unir
python3 comofunciona.py episodios/lapicero.py --voz grabacion.m4a   # con tu voz
python3 comofunciona.py episodios/lapicero.py --guion   # escribe el guion para grabar
```

## Nuevo episodio
1. Copia `episodios/_plantilla.py` → `episodios/cafetera.py`.
2. Cambia `TITULO` y dibuja tu objeto con las herramientas del lienzo.
3. Escribe las `ESCENAS`. Usa `--fotos` para revisar escenas sueltas y luego renderiza el video completo.

### Estructura recomendada (unos 45–55 s)
| tipo | chip automático | para qué sirve |
|---|---|---|
| `portada` | (título grande) | gancho: «¿CÓMO FUNCIONA …?» |
| `piezas` | LAS PIEZAS | presentar las partes con etiquetas |
| `paso` ×3–5 | PASO n/N | el proceso, un concepto por escena |
| `dato` | ¿SABÍAS QUE…? | curiosidad o historia |
| `cierre` | — | pedir el próximo tema en comentarios |

### Campos de cada escena
- `dur`: segundos de la escena
- `dibujo`: función `(lz, t)` que dibuja la ilustración
- `titulo`: título grande de la escena
- `texto`: subtítulo; las `*palabras clave*` van entre asteriscos y salen resaltadas
- `vel`: velocidad de escritura del subtítulo en letras por segundo (26 por defecto)
- `monigote`: `apunta=(x,y)`, `expresion='feliz'|'sorpresa'|'duda'|'guiño'`, `saluda=True`, `mira=(x,y)`, `x`, `pies`, `ocultar=True`
- `sonidos`: lista `[(segundo, 'pop'|'ding'|'whoosh')]`. El whoosh entre escenas y el pop del subtítulo se ponen solos.
- `chip`: texto propio para la etiqueta de la esquina, en lugar del automático

### Herramientas de dibujo (`lz`)
Todas aceptan `p` de 0 a 1, que indica cuánto del trazo está dibujado. Combínalas con `aparece(t, inicio, duración)`.
- `linea(pts, ancho, color, p)`: trazo libre
- `poligono(pts, relleno=…)`, `rect(x0,y0,x1,y1)`, `circulo(cx,cy,r)`, `arco(...)`. Con `sombra=True` llevan sombra de cómic.
- `flecha(p0, p1, curva)`, `etiqueta('texto', pos, objetivo, p)`, `burbuja('texto', x, y, cola)`
- `texto('hola', x, y, tam, color, p=…)`: se escribe letra por letra
- `mancha(pts, color)`: relleno sin borde, útil para líquidos y partículas
- Colores en `C`: `tinta, azul, rojo, amarillo, verde, naranja, gris, metal, celeste, rosa, blanco…`

### Zona segura
Mantén los dibujos entre y=330 y y=1250, y a la izquierda de x≈980 de y=900 hacia abajo. La interfaz de Shorts tapa la parte de abajo y la franja derecha. El monigote ocupa la esquina inferior izquierda (x<300, y>900).

## Voz y música
Con `--voz`, cada escena se alarga para que quepa tu voz, con 0,5 s antes y 1 s después. Las animaciones se estiran en la misma proporción y los efectos bajan de volumen. La música agrégala en YouTube o CapCut.
