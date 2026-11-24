#!/usr/bin/env python3
"""Lo usa GitHub Actions: decide qué episodios renderizar según lo que cambió."""
import os, subprocess, sys

AUDIO = ('.m4a', '.mp3', '.wav', '.ogg', '.opus', '.aac', '.flac', '.webm', '.mp4', '.mov', '.3gp')


def cambiados():
    pedido = os.environ.get('EPISODIO', '').strip()
    if pedido:
        return {pedido.replace('.py', '')}
    r = subprocess.run(['git', 'diff', '--name-only', 'HEAD^', 'HEAD'], capture_output=True, text=True)
    if r.returncode != 0:  # primer commit: todos
        return {f[:-3] for f in os.listdir('episodios') if f.endswith('.py')}
    eps = set()
    for ruta in r.stdout.split():
        partes = ruta.split('/')
        if partes[0] == 'episodios' and ruta.endswith('.py'):
            eps.add(partes[1][:-3])
        elif partes[0] == 'voz' and len(partes) > 2:
            eps.add(partes[1])
    return eps


def main():
    os.makedirs('videos', exist_ok=True)
    os.makedirs('guiones', exist_ok=True)
    fallos = []
    for ep in sorted(cambiados()):
        if ep.startswith('_') or not os.path.exists(f'episodios/{ep}.py'):
            continue
        print(f'\n=== {ep} ===', flush=True)
        subprocess.run([sys.executable, 'comofunciona.py', f'episodios/{ep}.py', '--guion'], check=True)
        os.replace(f'guion_{ep}.md', f'guiones/{ep}.md')
        carpeta = f'voz/{ep}'
        audios = [f for f in os.listdir(carpeta)] if os.path.isdir(carpeta) else []
        audios = [f for f in audios if f.lower().endswith(AUDIO)]
        cmd = [sys.executable, 'comofunciona.py', f'episodios/{ep}.py']
        if audios:
            cmd += ['--voz', carpeta, '--salida', f'videos/{ep}.mp4']
        else:
            cmd += ['--salida', f'videos/{ep}_sin_voz.mp4']
        if subprocess.run(cmd).returncode != 0:
            fallos.append(ep)
    if fallos:
        sys.exit('Fallaron: ' + ', '.join(fallos))


if __name__ == '__main__':
    main()
