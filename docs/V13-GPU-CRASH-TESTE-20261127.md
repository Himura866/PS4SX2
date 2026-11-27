# HIMURA SWITCH V13 — Hipótese de crash da GPU e teste isolado

**Início de retomada:** https://github.com/Himura866/PS4SX2/blob/himura-switch-r13-checkpoint-20261127/CHECKPOINT_V13.md

## O que foi realmente observado

- O usuário relata que a **R13 abre o menu e começa a carregar jogos, mas fecha ou trava antes/depois de entrar no gameplay**. O New Eden 04.89, no mesmo PS4 Pro, já executou Silksong e Pokémon Legends: Arceus. **Não há no material consultado log de crash da R13 correlacionado a um jogo**.
- Em `xatyy/Eden4` commit `fab246c` (fonte fixada pela R13), `vk_rasterizer.cpp` permite até **4096 draws** por lote padrão do Vulkan.
- Em `MrKitsune9/Orbis-EDEN`, patch público **0015** propõe **256 draws** e limite adicional de **96 uploads** para reduzir blocos de comandos à GPU GFX7 do PS4. Isso é uma **hipótese técnica investigável**, não comprovação de que o executável fechado do New Eden 04.89 contém precisamente esse código nem de que ele explica todo crash.
- R13 já possui a mitigação de indirect-count RADV (patch R13) e limites de cache específicos de `__OPENORBIS__`; não copiar patches Orbis-EDEN 0009 ou 0025 pela segunda vez.

## Correção experimental

Branch isolada: `himura-switch-v13-ps4-gpu-batch-20261127`, baseada na `himura-switch-r13-ptbr-usb-20261127` @ `6146f76e07cba9308581e27a98f9f1a7e205b348`. Script `ci/patch-v13-gpu-batch.py` altera cinco arquivos do checkout descartável: `vk_rasterizer.cpp`, `vk_scheduler.h`, `vk_scheduler.cpp`, `vk_buffer_cache.cpp` e `vk_texture_cache.cpp`. Sob `__OPENORBIS__`: descarrega mais cedo após 256 draws ou 96 uploads, conta cópias agrupadas e zera contador ao criar novo contexto. **PC e Android conservam valores anteriores**. Falha se qualquer âncora mudar antes de escrever os cinco arquivos. `ci/test-v13-gpu-batch.py` assegura o escopo PS4 e detecta dupla aplicação.

**Risco conhecido:** envios menores podem reduzir FPS ou alterar a temporização; por isso comparar com a R13 anterior no console, sem sobrescrever um aplicativo funcional sem backup. `HIMU00011` e `APP_VER=01.13` não mudam.

## Como identificar a falha no hardware

1. Exigir preflight, compilação, hash e artefato CircleCI; compilação aprovada **não é** gameplay aprovado.
2. No PS4 Pro: testar menu, controle, HD USB, depois **Silksong** até passar a abertura e jogar, e **Pokémon Legends: Arceus** até entrar no mapa, sem garantir FPS.
3. Se ocorrer crash, coletar `/data/EdenPS4/HIMURA_R13_GAME_STATUS.txt` e `eden.log`, `boot-trace.log`, `crash.log` pela tela de exportar logs ou FTP. Não divulgar keys, firmware nem arquivos de jogos.
4. Comparar últimas etapas do checkpoint: `container load`, `GPU start`, `guest CPU ready`, `first guest frame`, `first game frame submitted`. Se morrer antes da inicialização de GPU, a correção de lotes Vulkan não é suficiente.
5. Verificar FPS, áudio, volta ao menu, saves e ausência de regressões. Sem log/teste físico, manter status como **hipótese**, não solução confirmada.

**Status inicial:** patch novo em código de branch isolada; CI, PKG e teste físico desta revisão pendentes.
