# dkb-win

Recompilacao estatica de **Donkey Kong Bananza** para Windows (Vulkan).

> Este repositorio **nao contem nenhum arquivo do jogo**. Use seu proprio dump legal (ExeFS e RomFS da versao base 1.0.0). O dkb.exe e gerado na sua maquina.

## Como compilar
De dois cliques em **Instalar.bat**. Ele baixa e instala sozinho o MSYS2 clang64 (clang, lld, sdl3, opus, zstd, ninja), o Python 3.12 e o .NET SDK 8. Depois e so escolher as pastas ExeFS e RomFS do seu dump e clicar em Compilar (cerca de 25 min). O jogo fica na pasta jogo\.
## totk.ini recomendado

    native_gs = 1
    fix_c0 = 1
    fix_vs_fault = 0
    astc_bc = 0

## Creditos
- Projeto base do recompilador: https://github.com/sagaopc/dkb-pc-recomp.git
- **STS78721/dkb-BANANAS**: native GS do terreno, correcao de crash em cutscene, DLSS, launcher e overlay.
- **Eden** e o fork **PokeDinner**: referencia para texturas esparsas/ASTC.
- VMA (AMD), SDL3, Opus, Zstandard, libvpx, NVIDIA NGX/DLSS, MSYS2/LLVM-Clang.
- Integracao, testes e correcoes deste fork: Jean-DrEaD.

Donkey Kong Bananza e marca da Nintendo. Projeto de fas, sem afiliacao com a Nintendo.

