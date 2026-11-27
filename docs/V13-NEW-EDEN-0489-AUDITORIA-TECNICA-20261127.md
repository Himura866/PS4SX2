# HIMURA SWITCH V13 × New Eden 04.89 — auditoria técnica inicial (27/11/2026)

**Estado desta revisão:** comparação baseada em checkpoints reais do HIMURA, fontes públicas e inventário do `app0` do New Eden 04.89. **Nenhum motor foi substituído, nenhum PKG foi compilado e nenhuma correção de gameplay foi comprovada aqui.** Esta branch isola apenas documentação; não altera a branch R13 de testes.

## Evidências distintas — não confundir as bases

- **HIMURA R13**: código derivado de `xatyy/Eden4`, commit fixado `fab246cbac93c7995aaf451dca83ae93ba0bd234`. A branch GPU experimental adiciona limite de 256 draws/96 uploads sob `__OPENORBIS__`, ainda sem prova de correção no console.
- **New Eden 04.89 do usuário**: cópia do `app0` com `eboot.bin` e símbolos; eboot de 78.376.440 bytes, código de menu compilado, opções de renderer, shader cache, shaders assíncronos, CPU/threads, frame pacing, precisão GPU e FPS observadas no inventário. **Não há código-fonte demonstravelmente correspondente a este binário 04.89.** Sem isso, não é possível transplantar com segurança seu núcleo de JIT/GPU/ABI pela cópia de arquivos.
- **Orbis-EDEN público**: projeto relacionado, mas *não é comprovadamente* o mesmo binário New Eden 04.89. Fontes e patches públicos permitem comparar ideias e portar alterações uma por uma, após verificação do código/ABI.
- **Conclusão**: adotar o executável New Eden 04.89 como referência de comportamento; nunca alegar que uma compilação Eden4 reproduz seus recursos sem teste A/B. Preservar a instalação funcional e todos os dados.

## Matriz de migração — em ordem de segurança e benefício

| Área | Situação observada / código conhecido | Ação verificável | Restrição |
| --- | --- | --- | --- |
| Início de jogo | Arceus na R13 atual fecha com CE-34878-0 antes da seleção de idioma; revisão anterior avançava mais; jogos iniciam lentamente | Cronometrar da seleção ao primeiro quadro e comparar última etapa do log com uma rodada New Eden | Código CE-34878-0 sozinho não indica causa; priorizar regressão |
| JIT CPU | Eden4 já documenta janelas pequenas de proteção de cache, tabela de páginas e otimizações Dynarmic | Medir tempo de tradução inicial e propor porta somente do que for demonstravelmente ausente/compatível | Não habilitar fastmem ou nova alocação de memória sem prova em hardware |
| GPU / Vulkan | R13 possui mitigação RADV e proposta experimental de lotes 256 draws/96 uploads; Orbis-EDEN público traz patch 0015 semelhante | Comparar inicialização GPU, primeiro frame, driver, memória e travamentos por branch isolada | Menos draws pode piorar FPS; nenhuma equivalência com 04.89 demonstrada |
| Shaders e cache | Inventário do New Eden 04.89 indica shader cache e shaders assíncronos; Eden4 possui cache próprio | Auditar persistência, invalidação/versionamento e tempo de warm/cold start | Não compartilhar cache binário entre motores/versões |
| Memória | PS4 Pro tem limites estreitos; Eden4 usa pools diretos/flexíveis, reserva GPU e reciclagem | Logar pico de consumo e falha de alocação junto de etapa de boot e crash | Não copiar allocator de uma base para outra sem testar APIs |
| Armazenamento | USB0/USB1 mostrados na R13, mas leitura real falha; updates aparecem como jogos | Enumerar mounts reais, distinguir app/update/DLC, importar ZIP do firmware para destino válido só após confirmação e validação | Não apagar ou migrar keys, games, saves, firmware sem backup |
| Interface | R13 apresenta máscaras pretas, R13 no cabeçalho e spinner inerte | Corrigir arte aprovada sem botões falsos; barra horizontal animada com progresso real quando houver eventos | Nunca exibir porcentagem fictícia; manter DualShock e navegação |
| Build | CI preflight ≠ PKG e PKG ≠ jogo funcional | Validar patches pequenos, build CircleCI, hash+extração do PKG, só depois teste real no PS4 Pro | Não sobrescrever New Eden nem a R13 anterior |

## Protocolo de diagnóstico comparável

1. **Preservar** a R13 anterior, a R13 Experimental atual e o New Eden 04.89; registrar hashes/versões.
2. Para **Silksong** e **Pokémon Legends: Arceus**: registrar segundos de `X` até início de `system.Load`, fim do carregador, `GPU.Start`, primeiro frame na TV, idioma/menu e gameplay; fazer teste de partida fria e repetição com cache. Uma transição sem evento de progresso deve usar animação indeterminada.
3. Registrar, em arquivo de log sem dados privados: renderer, modo portátil/TV, número de threads, estado do shader cache, memória disponível, status dos arquivos, status do mount e último checkpoint; código da exceção com stack/log PS4 quando houver.
4. Exportar **somente** `HIMURA_R13_GAME_STATUS.txt`, `eden.log`, `boot-trace.log`, `crash.log` e logs equivalentes do New Eden. Nunca exportar keys, ROMs, firmware ou saves.
5. Classificar cada falha por etapa: `pre-load`, `loader`, `GPU`, `JIT/CPU`, `primeiro frame`, `gameplay`, `shutdown`. Na falta de log, marcar `inconclusivo`, não adivinhar.
6. Validar melhorias uma por vez com *A/B* entre builds. Critério de sucesso: mesmo jogo avança mais do que antes, gameplay estável, FPS e tempo de boot medidos, áudio sem regressão, retorno ao menu e saves preservados.

## Decisão de arquitetura

**Opção preferencial se a prioridade número 1 é estabilidade do New Eden:** manter o *motor funcional 04.89* inalterado e produzir uma personalização visual segura apenas quando houver método confiável de modificar/reconstruir o frontend compilado e gerar PKG validável. **Opção paralela de desenvolvimento:** portar patches de fonte pública ao Eden4 R13 isoladamente, com ABI, dependências, GPU e inicialização conferidas. Nunca substituir `eboot.bin` isoladamente.

## Fontes de consulta

- Fonte Eden4: https://github.com/xatyy/Eden4
- Fonte Orbis-EDEN: https://github.com/MrKitsune9/Orbis-EDEN
- Patch público 0015 de GPU: https://github.com/alechurri/nx-on-orbis/blob/main/patches/eden/0015-PS4-submit-smaller-command-buffers-the-driver-flatte.patch
- Checkpoint R13: https://github.com/Himura866/PS4SX2/blob/himura-switch-r13-checkpoint-20261127/CHECKPOINT_V13.md
- Patch GPU isolado R13: https://github.com/Himura866/PS4SX2/blob/himura-switch-v13-ps4-gpu-batch-20261127/ci/patch-v13-gpu-batch.py

**Próximo gate executável:** não iniciar nova compilação de 50 minutos para testes cegos. Primeiro obter stack/etapa final da R13 e tempo de boot comparativo com New Eden. Só aplicar otimização ao componente identificado e preservar as outras branches.
