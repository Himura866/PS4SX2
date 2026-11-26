# HIMURA SWITCH PS4 — comparativo real R13 × Orbis Eden (26/11/2026)

## Referências conferidas no GitHub
- R13 testada: branch `himura-switch-r13-user-tests-staging`; receita `ci/build-r11-samurai-library.sh`; base **xatyy/Eden4** `fab246cbac93c7995aaf451dca83ae93ba0bd234`.
- Orbis Eden: [MrKitsune9/Orbis-EDEN](https://github.com/MrKitsune9/Orbis-EDEN), release de 25/11, commit **`f004df1c7a812cc65703d8f937d0bd12a6d06a58`**.
- Núcleo do Orbis Eden: [eden-emulator/mirror](https://github.com/eden-emulator/mirror) `5f142c7926d0c7fcbbd0ce30794d72f638a43b2a` + **46 patches próprios PS4** `patches/eden/0001-0046`.
- O nome **"New Eden 0.4.89"** dos vídeos não foi vinculado, com prova de origem, a um repositório específico. O Orbis Eden é uma referência pública verificada para PS4, mas **não afirmar que é a mesma build informalmente chamada New Eden**.

## Mudança EXATA do Orbis Eden entre os commits de 15/11 e 25/11
Comparativo GitHub `c9a26c80...f004df1c`: **1 commit, 3 arquivos**:
1. `frontend/main.cpp`: 113 linhas adicionadas, 7 removidas (interface/funcionalidades de frontend).
2. `tools/analyze-boot.py`: 84 linhas, novo analisador de logs de inicialização.
3. `LEIA-ME.txt`: instruções atualizadas.
**Nenhum dos 46 patches do núcleo foi alterado nesse último commit.** Portanto, é incorreto atribuir à atualização de 25/11 uma nova correção de JIT/Vulkan/CPU sem outra fonte.

## Comparação técnica, sintomas e decisão

| Área | R13 Eden4 | Orbis Eden verificado | Caminho seguro |
|---|---|---|---|
| Núcleo | Eden4 `fab246c`, modificações locais R08–R13 aplicadas por Python | Eden `5f142c79` com 46 patches PS4 testados em conjunto | Usar Orbis como **linha experimental separada**; não aplicar patches diretamente a revisão incompatível do Eden4 |
| CPU/JIT | Silksong para na transição para gameplay; causa não determinada | Patches `0003`, `0005`, `0007`, `0008`; cache JIT e ajustes de pilhas/fibers; compilação `btver2` | Comparar rastros CPU e bloqueios antes de ajustar cache/fastmem |
| Vulkan/GPU | Tela preta/0 FPS e carga longa nos testes | Patch `0009` evita recursos RADV GFX7 que travam, `0015` faz submissões menores; texturas/caches `0017–0026` | Migrar em conjunto com driver/SDK correspondente e medir frames/apresentação |
| Memória PS4 | Sem prova da causa dos freezes | `0027`: reserva lazy do guest no topo; layout ~4,4 GiB; arena GPU e cache dimensionados | Registrar maior bloco livre, total direto, arena/cache e última etapa antes de travar |
| Mii/Mario Kart | Mario Kart 8 Deluxe não sai da tela de título | `0031`: Miis padrão quando base está vazia | Patch Mii é candidato para MK8, não prova conserto da tela inicial; backport já preparado em outra branch R13 |
| Runtime | Build R13 usa LLVM21/stack de Eden4 | LLVM18; libc++18; `frontend/libc_wide_fixes.cpp` corrige busca `wmemchr` do SDK que corrompia cache de texturas | Não misturar bibliotecas entre os dois pipelines |
| Inicialização | Exportação de logs R13 | `boot.log`, `mesa.log`, profiler opcional e `tools/analyze-boot.py` | Comparar tempos de fases, chamadas de firmware e memória; não aumentar timeout aleatoriamente |
| Interface | Arte samurai e português; faixa inferior fictícia corrigida no staging da R13 | Menu próprio, idioma e USB; atualização 25/11 no frontend | Portar o tema e controles reais **depois** que o novo núcleo abrir jogos; arte ainda não integrada ao frontend Orbis |

## O que os testes realmente sustentam
- No **PS4 Pro do usuário**, Silksong entra no menu e na introdução, depois fica com 0 FPS e acaba fechando; BMX City Run não passa de `Loading`; MK8 Deluxe não sai da tela de nome/título. Isso **não** permite concluir qual thread/etapa é responsável sem `boot.log`/`crash.log`.
- Orbis Eden documenta **Mario Kart 8 Deluxe em corridas a 13–16 FPS** e **menus a 40–60 FPS**; Cuphead chega ao menu a ~30 FPS. Não interpretar 60 FPS de menu como 60 FPS de corrida. O próprio projeto documenta memória quase esgotada em corridas e outros travamentos.
- `experimental-fastmem` não é candidato imediato: o upstream relata aumento do uso de memória e incapacidade de voltar a carregar corridas.

## Progresso real nesta branch R14
1. Atualizada `ci/himura-switch-build.sh` para **fixar** o commit Orbis de 25/11 e fazer checkout determinístico pelo SHA, em vez de depender da ponta móvel da branch `main`.
2. O build agora verifica o commit Eden do Orbis, quantidade de 46 patches e componentes essenciais de memória/JIT, Vulkan, Mii, runtime e analisador de boot **antes** da instalação pesada de dependências.
3. Criado `ci/audit-r14-orbis-base.sh` e job `auditar_r14_orbis_core` no CircleCI, exclusivo desta branch. **O job somente audita fontes, não gera PKG**.
4. Não foi alterada a branch R13 principal nem o projeto de PS2.
5. **Pendente:** compilar Orbis atualizado, adaptar o tema samurai ao frontend novo, testar no PS4 Pro e medir gameplay. Nenhuma melhoria de FPS ou solução de crash foi comprovada nesta branch.

## Ordem técnica (sem PKGs cegos)
- Validar auditoria de fonte e pin.
- Verificar compilação/link do Orbis e logs do CI, separadamente de empacotamento.
- Testar boot, CPU/JIT e Vulkan com programa de teste simples; coletar logs de travamento.
- Testar MK8D, Silksong e BMX City Run individualmente, anotando tempos e FPS **durante o jogo**.
- Só depois migrar e validar capa samurai, botões funcionais, menu em português, FPS e empacotar um PKG candidato.
