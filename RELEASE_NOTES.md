# DK Builder v0.3.7

## Novidades
- **Sincronizado com o upstream** (Lucas-blip-png/dkb-pc-recomp, `48ac0a0..a5796d9`, 67 commits): correções de runtime, renderização e desempenho.
- **Frame generation (experimental)**: nova opção no menu do jogo (**F1** ou **Esc** → Graphics, abaixo do SMAA), com `off` e `2x`. Vem desligado.
- **Overlay completo**: nova linha `Frame gen` mostrando FPS real → exibido e o motivo de descarte (`refresh cap`).
- **Título do jogo** volta a mostrar a versão correta (`3.2.0`) em vez de `Ver. 0.0.0`.
- **Foco da janela**: o jogo abre em primeiro plano e o fullscreen é aplicado corretamente.
- **Ícone**: o instalador usa o `dkb.ico` do projeto.

## Correções de build
- Removido `gfx_present.c`, que causava símbolos duplicados (o upstream dividiu esse arquivo).
- Protótipo de `gfx_window_release_vk` corrigido.

## Frame generation: quando vale a pena
O FG cria 1 quadro intermediário por quadro real, mas **descarta** os quadros gerados quando o dobro do FPS passa do refresh do monitor.

| Monitor | Jogo | Resultado |
|---|---|---|
| 60 Hz | 60 fps | sem efeito (`refresh cap`) |
| 60 Hz | ≤ 30 fps | ~60 exibidos, com mais latência |
| 120/144 Hz | 60 fps | ~120 exibidos |

**Em monitor de 60 Hz, deixe `off`.**

## Lembrete: cache de shaders
- **NVIDIA:** Painel de Controle → *Tamanho do cache de shader* → **Ilimitado** (sem isso, o 1º boot pode travar na cutscene).
- **AMD:** cache de shader **Ativado** (não testado).

## Requisitos
Windows 11 x64, GPU com Vulkan 1.3 e dump próprio do jogo (base + update 3.2.0 + DLC opcional, em `.nup`).

---

## DKB v0.3.0

### New / Novidades
- **DKB Builder** (graphical installer): pick your game files, choose the folder and language, and it builds the game. Accepts .nup or romfs/exefs folders.
- **Update 3.2.0 support** (the installer detects the version automatically).
- **DLC (Emerald Rush)** is detected and mounted.
- Settings moved to `dkb.ini` (old `totk.ini` still read). Log: `logs\dkb.log`.
- The game window now opens in the foreground.
- New DKB icon and banner.

### Known issues / Problemas conhecidos
- 40-50 FPS in big scenes (limited by the CPU when preparing frames). Optimization is the next goal.
- The first launch shows black textures for a while (shader cache is empty). From the second launch on it loads normally.
- The version screen still shows 1.0.0 (only the text is wrong).

### Requirements
- Windows 10/11 x64, ~60 GB free, your own legal dump of the game. No game files are included.