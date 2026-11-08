r"""Monta <dest>\dlc\romfs a partir da romfs da DLC.
Mesmo disco = hardlink (sem espaco extra); outro disco = copia. Nunca junction/symlink
(o jogo nao reconhece a DLC por junction - teste B)."""
import argparse, os, shutil, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='pasta romfs da DLC')
    ap.add_argument('--dest', required=True, help='pasta do dkb.exe')
    a = ap.parse_args()
    src = Path(a.src); dst = Path(a.dest) / 'dlc' / 'romfs'
    if not src.is_dir():
        print(f'deploy_dlc: origem nao existe: {src}'); return 1
    if dst.is_symlink() or (hasattr(dst, 'is_junction') and dst.is_junction()):
        os.rmdir(dst) if dst.is_junction() else dst.unlink()
        print('deploy_dlc: junction/symlink antiga removida')
    same = os.path.splitdrive(src.resolve())[0].lower() == os.path.splitdrive(Path(a.dest).resolve())[0].lower()
    n_link = n_copy = n_skip = 0
    for f in src.rglob('*'):
        if not f.is_file(): continue
        t = dst / f.relative_to(src)
        if t.exists() and t.stat().st_size == f.stat().st_size:
            n_skip += 1; continue
        t.parent.mkdir(parents=True, exist_ok=True)
        if t.exists(): t.unlink()
        if same:
            try: os.link(f, t); n_link += 1; continue
            except OSError: pass
        shutil.copy2(f, t); n_copy += 1
    print(f'deploy_dlc: {dst} -> hardlinks {n_link}, copias {n_copy}, ja existiam {n_skip}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
