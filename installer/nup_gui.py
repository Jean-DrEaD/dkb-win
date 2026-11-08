"""DKB Setup: installs from a .nup or from extracted folders (base / update / DLC). tkinter only."""
import json, os, queue, signal, subprocess, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT / 'tools', ROOT / 'installer'):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
WORK = ROOT / 'build' / 'nup-extract'
MSYS = Path(r'C:\msys64\clang64')

LANGS = [('pt-BR', 'Português (Brasil)'), ('en', 'English'), ('fr', 'Français'),
         ('es', 'Español'), ('ru', 'Русский'), ('it', 'Italiano')]
GAME_LANG = {'pt-BR': 'pt-BR', 'en': 'en-US', 'fr': 'fr', 'es': 'es', 'ru': 'ru', 'it': 'it'}
T = {
 'pt-BR': dict(title='DKB Setup', lang='Idioma', mode='Origem do jogo', nup='Arquivo .NUP', folders='Pastas extraídas',
   nupf='Arquivo .nup:', base='Pasta base (exefs/romfs):', upd='Pasta do update (opcional):', dlc='Pasta da DLC (opcional):',
   dest='Pasta de instalação:', browse='Procurar...', install='Instalar', cancel='Cancelar',
   need='Escolha a origem do jogo e a pasta de instalação.', noexefs='Pasta exefs não encontrada em: ', nogame='O .nup não tem pacote base nem update.',
   extract='Extraindo', build='Compilando o jogo (pode levar 20-40 min)...', dlcdep='Instalando a DLC...', done='Instalação concluída!', fail='Falhou (código {}). Veja o log.'),
 'en': dict(title='DKB Setup', lang='Language', mode='Game source', nup='.NUP file', folders='Extracted folders',
   nupf='.nup file:', base='Base folder (exefs/romfs):', upd='Update folder (optional):', dlc='DLC folder (optional):',
   dest='Install folder:', browse='Browse...', install='Install', cancel='Cancel',
   need='Choose the game source and the install folder.', noexefs='exefs folder not found in: ', nogame='The .nup has no base or update package.',
   extract='Extracting', build='Building the game (may take 20-40 min)...', dlcdep='Installing the DLC...', done='Installation complete!', fail='Failed (code {}). See the log.'),
 'fr': dict(title='DKB Setup', lang='Langue', mode='Source du jeu', nup='Fichier .NUP', folders='Dossiers extraits',
   nupf='Fichier .nup :', base='Dossier de base (exefs/romfs) :', upd='Dossier de mise à jour (optionnel) :', dlc='Dossier du DLC (optionnel) :',
   dest="Dossier d'installation :", browse='Parcourir...', install='Installer', cancel='Annuler',
   need="Choisissez la source du jeu et le dossier d'installation.", noexefs='Dossier exefs introuvable dans : ', nogame="Le .nup n'a ni paquet de base ni mise à jour.",
   extract='Extraction', build='Compilation du jeu (20-40 min)...', dlcdep='Installation du DLC...', done='Installation terminée !', fail='Échec (code {}). Voir le journal.'),
 'es': dict(title='DKB Setup', lang='Idioma', mode='Origen del juego', nup='Archivo .NUP', folders='Carpetas extraídas',
   nupf='Archivo .nup:', base='Carpeta base (exefs/romfs):', upd='Carpeta de actualización (opcional):', dlc='Carpeta del DLC (opcional):',
   dest='Carpeta de instalación:', browse='Examinar...', install='Instalar', cancel='Cancelar',
   need='Elige el origen del juego y la carpeta de instalación.', noexefs='No se encontró la carpeta exefs en: ', nogame='El .nup no tiene paquete base ni actualización.',
   extract='Extrayendo', build='Compilando el juego (20-40 min)...', dlcdep='Instalando el DLC...', done='¡Instalación completada!', fail='Falló (código {}). Mira el registro.'),
 'ru': dict(title='DKB Setup', lang='Язык', mode='Источник игры', nup='Файл .NUP', folders='Распакованные папки',
   nupf='Файл .nup:', base='Базовая папка (exefs/romfs):', upd='Папка обновления (необязательно):', dlc='Папка DLC (необязательно):',
   dest='Папка установки:', browse='Обзор...', install='Установить', cancel='Отмена',
   need='Выберите источник игры и папку установки.', noexefs='Папка exefs не найдена в: ', nogame='В .nup нет базового пакета или обновления.',
   extract='Распаковка', build='Сборка игры (20-40 мин)...', dlcdep='Установка DLC...', done='Установка завершена!', fail='Ошибка (код {}). См. журнал.'),
 'it': dict(title='DKB Setup', lang='Lingua', mode='Origine del gioco', nup='File .NUP', folders='Cartelle estratte',
   nupf='File .nup:', base='Cartella base (exefs/romfs):', upd='Cartella aggiornamento (facoltativa):', dlc='Cartella DLC (facoltativa):',
   dest='Cartella di installazione:', browse='Sfoglia...', install='Installa', cancel='Annulla',
   need="Scegli l'origine del gioco e la cartella di installazione.", noexefs='Cartella exefs non trovata in: ', nogame='Il .nup non ha pacchetto base né aggiornamento.',
   extract='Estrazione', build='Compilazione del gioco (20-40 min)...', dlcdep='Installazione del DLC...', done='Installazione completata!', fail='Errore (codice {}). Vedi il registro.'),
}

NOTOOLS = {'pt-BR': 'Ferramentas de compilacao ausentes (MSYS2 clang64 / .NET 10). Rode o Instalar.bat do dkb-win primeiro.',
 'en': 'Build tools missing (MSYS2 clang64 / .NET 10). Run Instalar.bat from dkb-win first.',
 'fr': 'Outils de compilation absents (MSYS2 clang64 / .NET 10). Lancez d\'abord Instalar.bat (dkb-win).',
 'es': 'Faltan herramientas de compilacion (MSYS2 clang64 / .NET 10). Ejecuta primero Instalar.bat de dkb-win.',
 'ru': 'Нет инструментов сборки (MSYS2 clang64 / .NET 10). Сначала запустите Instalar.bat из dkb-win.',
 'it': 'Strumenti di compilazione mancanti (MSYS2 clang64 / .NET 10). Esegui prima Instalar.bat di dkb-win.'}
for _k, _v in NOTOOLS.items():
    T[_k]['notools'] = _v

TXT_DARK = dict(bg='#1e1e1e', fg='#cfcfcf', insertbackground='#e6e6e6', relief='flat',
                highlightthickness=0, font=('Consolas', 9))


def windows_dark():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
        return winreg.QueryValueEx(k, 'AppsUseLightTheme')[0] == 0
    except Exception:
        return False


def apply_theme(root):
    if not windows_dark():
        return False
    BG, CARD, FG, DIM, ACC = '#121212', '#1e1e1e', '#e6e6e6', '#9e9e9e', '#66bb6a'
    s = ttk.Style(root); s.theme_use('clam')
    s.configure('.', background=BG, foreground=FG, fieldbackground=CARD, bordercolor='#2c2c2c',
                lightcolor=BG, darkcolor=BG, troughcolor=CARD, font=('Segoe UI', 10))
    s.configure('TButton', background='#2a2a2a', padding=(12, 6), relief='flat')
    s.map('TButton', background=[('active', '#383838'), ('disabled', '#1a1a1a')], foreground=[('disabled', DIM)])
    s.configure('Accent.TButton', background=ACC, foreground='#0d1f0e')
    s.map('Accent.TButton', background=[('active', '#81c784'), ('disabled', '#2e4a30')])
    s.configure('TEntry', fieldbackground=CARD, foreground=FG, insertcolor=FG, padding=6)
    s.configure('TCombobox', fieldbackground=CARD, background='#2a2a2a', foreground=FG, arrowcolor=FG)
    s.map('TCombobox', fieldbackground=[('readonly', CARD)], foreground=[('readonly', FG)],
          selectbackground=[('readonly', CARD)], selectforeground=[('readonly', FG)])
    root.option_add('*TCombobox*Listbox.background', CARD)
    root.option_add('*TCombobox*Listbox.foreground', FG)
    root.option_add('*TCombobox*Listbox.selectBackground', ACC)
    s.configure('TRadiobutton', background=BG, foreground=FG, indicatorcolor=CARD)
    s.map('TRadiobutton', indicatorcolor=[('selected', ACC)], background=[('active', BG)])
    s.configure('Horizontal.TProgressbar', background=ACC, troughcolor=CARD, bordercolor=CARD,
                lightcolor=ACC, darkcolor=ACC)
    root.configure(bg=BG)
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        v = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
    except Exception:
        pass
    return True

LOGTXT = {'pt-BR': ('Abrir log', 'Abrir pasta'), 'en': ('Open log', 'Open folder'), 'fr': ('Ouvrir le journal', 'Ouvrir le dossier'),
          'es': ('Abrir log', 'Abrir carpeta'), 'ru': ('Открыть лог', 'Открыть папку'), 'it': ('Apri log', 'Apri cartella')}


def _logfile(app):
    d = Path(app.v['dest'].get() or '.') / 'logs'; d.mkdir(parents=True, exist_ok=True)
    f = d / 'dkb-setup.log'; f.write_text(app.txt.get('1.0', 'end'), encoding='utf-8'); return f


def _log_btns(self):
    try:
        _log_btns_real(self)
    except Exception:
        import traceback; traceback.print_exc()


def _log_btns_real(self):
    import os
    _l = getattr(self, 'lang', None); _l = _l.get() if hasattr(_l, 'get') else (_l or 'pt-BR')
    if _l not in LOGTXT:
        _m = {'portu': 'pt-BR', 'engl': 'en', 'fran': 'fr', 'espa': 'es', 'русс': 'ru', 'ital': 'it'}
        _l = next((v for k, v in _m.items() if str(_l).lower().startswith(k)), 'en')
    lg = LOGTXT[_l]
    fr = self.b_inst.master
    b1 = ttk.Button(fr, text=lg[0], command=lambda: os.startfile(str(_logfile(self))))
    b2 = ttk.Button(fr, text=lg[1], command=lambda: os.startfile(str(_logfile(self).parent)))
    if self.b_inst.winfo_manager() == 'grid':
        c = max([w.grid_info().get('column', 0) for w in fr.grid_slaves()] + [0])
        b1.grid(row=0, column=c + 1, padx=4); b2.grid(row=0, column=c + 2, padx=4)
    else:
        b1.pack(side='left', padx=4); b2.pack(side='left', padx=4)


def default_lang():
    try:
        import locale
        loc = (locale.getlocale()[0] or '').lower()
    except Exception:
        loc = ''
    if loc.startswith('pt') or 'portug' in loc:
        return 'pt-BR'
    for code, key in (('fr', 'fr'), ('es', 'es'), ('ru', 'ru'), ('it', 'it'), ('french', 'fr'), ('spanish', 'es'), ('russian', 'ru'), ('italian', 'it')):
        if loc.startswith(code):
            return key
    return 'en'


PORTABLE_DN = ROOT / '.portable' / 'dotnet10'
_DN = []


def _sdk10(exe):
    try:
        out = subprocess.run([str(exe), '--list-sdks'], capture_output=True, text=True, timeout=60).stdout
        return any(l.startswith('10.') for l in out.splitlines())
    except Exception:
        return False


def find_dotnet():
    if _DN:
        return _DN[0]
    from shutil import which
    for c in (PORTABLE_DN / 'dotnet.exe', Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'dotnet' / 'dotnet.exe',
              Path(r'C:\Program Files\dotnet\dotnet.exe'), which('dotnet')):
        if c and Path(c).is_file() and _sdk10(c):
            _DN.append(str(c))
            return str(c)
    return None


def ensure_dotnet(log):
    if find_dotnet():
        log('.NET 10 SDK: ' + find_dotnet()); return
    log('Baixando .NET 10 SDK portatil (~300 MB, uma vez so)...')
    import tempfile, urllib.request
    ps1 = Path(tempfile.gettempdir()) / 'dotnet-install.ps1'
    urllib.request.urlretrieve('https://dot.net/v1/dotnet-install.ps1', str(ps1))
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(ps1),
                        '-Channel', '10.0', '-InstallDir', str(PORTABLE_DN), '-NoPath'], capture_output=True, text=True)
    log((r.stdout + r.stderr).strip()[-1500:])
    if not find_dotnet():
        raise RuntimeError('.NET 10 SDK: o download falhou (veja o log).')
    log('.NET 10 SDK: ' + find_dotnet())


def romfs_of(d):
    d = Path(d)
    return d / 'romfs' if (d / 'romfs').is_dir() else d


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.dark = apply_theme(self)
        self.after(0, self._log_btns)
        self.geometry('820x620')
        self.lang = tk.StringVar(value=default_lang())
        self.mode = tk.StringVar(value='nup')
        self.v = {k: tk.StringVar() for k in ('nup', 'base', 'upd', 'dlc')}
        self.v['dest'] = tk.StringVar(value=r'C:\NS2\DKB-GUI-teste')
        self.lines, self.q, self.proc, self.busy = [], queue.Queue(), None, False
        self.frame = None
        self.ui()
        self.after(100, self.pump)

    def t(self, k):
        return T[self.lang.get()].get(k, T['en'][k])

    def ui(self, *_):
        if self.frame:
            self.frame.destroy()
        self.title(self.t('title'))
        f = self.frame = ttk.Frame(self, padding=12)
        f.pack(fill='both', expand=True)
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text=self.t('lang')).grid(row=0, column=0, sticky='w')
        cb = ttk.Combobox(f, state='readonly', values=[n for _, n in LANGS])
        cb.current([c for c, _ in LANGS].index(self.lang.get()))
        cb.grid(row=0, column=1, sticky='w', pady=4)
        cb.bind('<<ComboboxSelected>>', lambda e: (self.lang.set(LANGS[cb.current()][0]), self.ui()))
        ttk.Label(f, text=self.t('mode')).grid(row=1, column=0, sticky='w')
        m = ttk.Frame(f); m.grid(row=1, column=1, sticky='w')
        for val, key in (('nup', 'nup'), ('dir', 'folders')):
            ttk.Radiobutton(m, text=self.t(key), value=val, variable=self.mode, command=self.ui).pack(side='left', padx=4)
        rows = [('nupf', 'nup', True)] if self.mode.get() == 'nup' else [('base', 'base', False), ('upd', 'upd', False), ('dlc', 'dlc', False)]
        rows.append(('dest', 'dest', False))
        r = 2
        for lab, key, isfile in rows:
            ttk.Label(f, text=self.t(lab)).grid(row=r, column=0, sticky='w', pady=3)
            ttk.Entry(f, textvariable=self.v[key]).grid(row=r, column=1, sticky='ew', padx=4)
            ttk.Button(f, text=self.t('browse'), command=lambda k=key, fi=isfile: self.pick(k, fi)).grid(row=r, column=2)
            r += 1
        b = ttk.Frame(f); b.grid(row=r, column=0, columnspan=3, pady=8, sticky='w')
        self.b_inst = ttk.Button(b, text=self.t('install'), style='Accent.TButton', command=self.start, state='disabled' if self.busy else 'normal')
        self.b_inst.pack(side='left', padx=4)
        ttk.Button(b, text=self.t('cancel'), command=self.cancel).pack(side='left', padx=4)
        self.pb = ttk.Progressbar(f, mode='determinate', value=0)
        self.pb.grid(row=r + 1, column=0, columnspan=3, sticky='ew')
        if self.busy:
            self.pb.configure(mode='indeterminate'); self.pb.start(15)
        self.txt = tk.Text(f, height=18, wrap='none', **(TXT_DARK if self.dark else {}))
        self.txt.grid(row=r + 2, column=0, columnspan=3, sticky='nsew', pady=6)
        f.rowconfigure(r + 2, weight=1)
        self.txt.insert('end', '\n'.join(self.lines[-500:]) + ('\n' if self.lines else ''))

    def pick(self, key, isfile):
        p = filedialog.askopenfilename(filetypes=[('NUP', '*.nup'), ('*', '*.*')]) if isfile else filedialog.askdirectory()
        if p:
            self.v[key].set(os.path.normpath(p))

    def log(self, m):
        self.q.put(m)

    def pump(self):
        while not self.q.empty():
            m = self.q.get()
            if isinstance(m, dict):
                self.pb.stop(); self.pb.configure(mode='determinate', maximum=max(m['t'], 1), value=m['d'])
                continue
            if isinstance(m, tuple):
                self.busy = False
                self.pb.stop(); self.pb.configure(mode='determinate', value=100 if m[0] else 0); self.b_inst.configure(state='normal')
                (messagebox.showinfo if m[0] else messagebox.showerror)(self.t('title'), m[1])
                continue
            self.lines.append(m)
            self.txt.insert('end', m + '\n'); self.txt.see('end')
        self.after(100, self.pump)

    def start(self):
        src = self.v['nup'].get() if self.mode.get() == 'nup' else self.v['base'].get() or self.v['upd'].get()
        if not src or not self.v['dest'].get():
            messagebox.showwarning(self.t('title'), self.t('need')); return
        self.busy = True
        self.b_inst.configure(state='disabled'); self.pb.configure(mode='indeterminate'); self.pb.start(15)
        threading.Thread(target=self.work, daemon=True).start()

    def cancel(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            except Exception:
                self.proc.terminate()

    def work(self):
        try:
            ensure_dotnet(self.log)
            if not (MSYS / 'bin' / 'clang.exe').is_file() or not find_dotnet():
                raise RuntimeError(self.t('notools'))
            _dn = Path(str(find_dotnet())); _dd = _dn.parent if _dn.suffix.lower() == '.exe' else _dn
            import os as _os; _os.environ['PATH'] = str(_dd) + _os.pathsep + _os.environ.get('PATH', ''); _os.environ['DOTNET_ROOT'] = str(_dd)
            dest = Path(self.v['dest'].get())
            dlc = None
            if self.mode.get() == 'nup':
                from extract_nup import Nup, Zstd, extract_tree
                nup, z = Nup(Path(self.v['nup'].get())), Zstd()
                upd = [p for p in nup.packages if p.kind_name == 'update']
                base = [p for p in nup.packages if p.kind_name == 'base']
                addon = [p for p in nup.packages if p.kind_name == 'addon']
                game = max(upd, key=lambda p: p.version) if upd else (base[0] if base else None)
                if not game:
                    raise RuntimeError(self.t('nogame'))
                for which in ('exefs', 'romfs'):
                    self.log(f'{self.t("extract")} [{game.index}] {game.kind_name} {which}...')
                    n, tot, sk = extract_tree(nup, z, game, which, WORK / 'game' / which, True, True)
                    self.log(f'  {which}: {n} ({tot / 1e9:.2f} GB, {sk} ok)')
                exefs, romfs = WORK / 'game' / 'exefs', WORK / 'game' / 'romfs'
                if addon:
                    self.log(f'{self.t("extract")} [{addon[0].index}] addon romfs...')
                    extract_tree(nup, z, addon[0], 'romfs', WORK / 'dlc' / 'romfs', True, True)
                    dlc = WORK / 'dlc' / 'romfs'
            else:
                b, u = self.v['base'].get(), self.v['upd'].get()
                top = Path(u or b)
                exefs = top / 'exefs'
                if not exefs.is_dir():
                    raise RuntimeError(self.t('noexefs') + str(top))
                romfs = top / 'romfs' if (top / 'romfs').is_dir() else Path(b) / 'romfs'
                if self.v['dlc'].get():
                    dlc = romfs_of(self.v['dlc'].get())
            cmd = [sys.executable, '-m', 'installer', '--exefs', str(exefs), '--romfs', str(romfs),
                   '--dest', str(dest), '--lang', GAME_LANG[self.lang.get()]]
            if MSYS.is_dir():
                cmd += ['--toolchain', str(MSYS), '--deps', str(MSYS), '--ninja', str(MSYS / 'bin' / 'ninja.exe'),
                        '--dll-dir', str(MSYS / 'bin')]
            dn = find_dotnet()
            if dn:
                cmd += ['--dotnet', dn]
            self.log(self.t('build'))
            self.proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                         encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            for line in self.proc.stdout:
                line = line.rstrip()
                try:
                    e = json.loads(line)
                    if e.get('total'):
                        self.q.put({'d': float(e.get('done') or 0), 't': float(e['total'])})
                    if e.get('type') == 'progress':
                        continue
                    line = ' '.join(f'{k}={v}' for k, v in e.items() if k not in ('steps',))[:220]
                except Exception:
                    pass
                self.log(line)
            rc = self.proc.wait()
            if rc != 0:
                self.q.put((False, self.t('fail').format(rc))); return
            if dlc and dlc.is_dir():
                self.log(self.t('dlcdep'))
                r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'deploy_dlc.py'), '--src', str(dlc), '--dest', str(dest)],
                                   capture_output=True, text=True)
                self.log((r.stdout + r.stderr).strip())
            self.q.put((True, self.t('done') + '\n' + str(dest)))
        except Exception as ex:
            self.log(f'[!] {ex}')
            self.q.put((False, str(ex)))


App._log_btns = _log_btns







def _fix_scroll(root):
    st = ttk.Style(root)
    st.layout('Dark.Vertical.TScrollbar', [('Vertical.Scrollbar.trough', {'sticky': 'ns', 'children': [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})]})])
    st.configure('Dark.Vertical.TScrollbar', troughcolor='#1e1e1e', background='#3a3a3a', bordercolor='#1e1e1e', lightcolor='#3a3a3a', darkcolor='#3a3a3a', gripcount=0, width=12)
    st.map('Dark.Vertical.TScrollbar', background=[('active', '#555555')])
    def hide(c):
        m = c.winfo_manager()
        if m == 'grid': c.grid_remove()
        elif m == 'pack': c.pack_forget()
        elif m == 'place': c.place_forget()
    def walk(x):
        for c in list(x.winfo_children()):
            cls = c.winfo_class()
            if cls in ('Scrollbar', 'TScrollbar'):
                if str(c.cget('orient')) == 'horizontal':
                    hide(c)
                elif c.winfo_manager() == 'grid':
                    info = {k: v for k, v in c.grid_info().items() if k != 'in'}
                    new = ttk.Scrollbar(c.master, orient='vertical', command=c.cget('command'), style='Dark.Vertical.TScrollbar')
                    hide(c); new.grid(**info)
                    for t in c.master.winfo_children():
                        if t.winfo_class() == 'Text':
                            t.configure(yscrollcommand=new.set)
                else:
                    c.configure(style='Dark.Vertical.TScrollbar') if cls == 'TScrollbar' else None
            elif cls == 'Text':
                c.configure(wrap='char')
            walk(c)
    walk(root)


_orig_ml = tk.Misc.mainloop
def _ml(self, n=0):
    try:
        _fix_scroll(self)
    except Exception as e:
        print('aviso scroll:', e)
    return _orig_ml(self, n)
tk.Misc.mainloop = _ml

if __name__ == '__main__':
    App().mainloop()

