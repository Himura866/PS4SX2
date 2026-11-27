# HIMURA SWITCH — portabilidade de otimizações Android → PS4 Pro (R13, 27/11/2026)

**Estado:** auditoria de fonte e plano de integração. NÃO altera o emulador, não gera PKG, não prova melhoria no PS4 Pro. Criado na branch isolada `himura-switch-v13-neweden-technical-audit-20261127`. Preservar a R13 de teste e o New Eden 04.89 funcional.

## O que a base Eden4 fixada já oferece

Fonte: `xatyy/Eden4` commit `fab246cbac93c7995aaf451dca83ae93ba0bd234`, `eden/src/yuzu_ps4/main.cpp`, antes dos patches gerados da R13:

- `Settings::values.cpu_backend = Dynarmic` e `renderer_backend = Vulkan`: JIT e GPU nativos usados na plataforma PS4.
- `use_disk_shader_cache = false` no arranque; `async_presentation = false`. **Não ativar cegamente**: verificar persistência, permissões, backend PS4, cache de pipelines RADV, comportamento de GPU e integridade do cache.
- A `ps4.ini` em `/data/EdenPS4/` lê/grava escolhas do usuário; existem modo Docked/Handheld, 720p/1080p, perfilador de CPU, quatro opções JIT de diagnóstico e mapeamento de controles. Precisam ser testadas no build final: fonte isolada não comprova execução.
- `Ui::Launcher` exibe categorias, chama `host.SetOption` para salvar/aplicar, portanto há mecanismo real para conectar opções novas a subsistemas, sem criar botões fictícios.

## Quais técnicas Android portar — e quais NÃO portar

| Técnica | Avaliação para PS4 Pro | Evidência / gate |
| --- | --- | --- |
| Cache persistente de shaders e pipelines Vulkan | Candidato concreto de melhoria em segunda execução do jogo; **a base PS4 desativa cache em disco**. Adicionar primeiro teste de escrita/leitura, serialização, versão por emulador e invalidação segura | Comparar primeiro carregamento e carregamento repetido, stutter, uso de RAM, mensagens RADV, retorno ao menu. Nunca compartilhar blobs de cache entre Android/New Eden/R13 |
| Compilação assíncrona de shaders | Portar somente após verificar a thread safety do driver e efeitos em renderização; pode reduzir engasgos, mas introduzir glitches ou travamentos | Medir GPU e qualidade dos primeiros frames em Silksong e Arceus, reverter sob erro |
| JIT Dynarmic mais rápido (otimização de blocos / registro / páginas) | Alta prioridade pelo gargalo de tradução de CPU documentado no Orbis-EDEN. Comparar algoritmos atuais do Eden Android com a versão PS4, sem transplantar memória/ABI | Instrumentar tempo de compilação JIT, páginas e último checkpoint. Uma mudança por branch |
| Limites de buffers e lotes Vulkan | O patch PS4 experimental de 256 draws/96 uploads é específico de RADV/GFX7, não uma otimização Android universal | Verificar quando há perda de dispositivo; comparar FPS, CPU, erro Vulkan, alterações no jogo |
| Reciclagem de memória e controle de cache | Altamente relevante no PS4 com RAM disponível limitada; priorizar medição de pico e alinhamento das estruturas com o driver | Medir alocação de RAM/GPU, falhas de alocação, regressões e desempenho |
| Ajustes por jogo | Oferecer perfis 'Compatibilidade' e 'Desempenho' só quando cada ajuste modificar código real e for testado; opções persistentes, restaurar padrão e indicação de reinício | Verificação da conexão UI → opção gravada → código que efetivamente lê → diferença mensurável |
| Resolução / modo portátil | Já existem na base, testar se os caminhos 720p/1080p e Docked/Handheld modificam corretamente os componentes e efeitos | Perfis associados a jogos, comparação de estabilidade, memória e qualidade |
| NCE Android ARM64 | **Não portável como recurso de execução direta**: PS4 Pro usa processador x86-64, Android NCE depende de CPU hospedeira ARM64 | Manter Dynarmic ou outro tradutor ARM→x86-64 comprovado |
| Drivers Turnip / Adreno / ajustes exclusivos Snapdragon | **Não portáveis**: PS4 usa GPU AMD GCN, Mesa RADV próprio, interface Orbis e Vulkan restrito | Usar capacidades realmente anunciadas pelo driver; não exibir opções sem implementação |
| FSR, VSync, escalonamento e FPS desbloqueado | Não supor compatibilidade ou ganho: só expor controles após comprovação em renderização e frame pacing do PS4 | Nunca prometer 60 FPS onde CPU/GPU não conseguem renderizar em tempo real |

## Sequência executável de integração

1. **Instrumentar antes de otimizar:** fases `launcher`, abertura de jogo, loader, JIT/CPU, GPU.Start, primeiro frame, gameplay; tempos monotônicos, FPS real, pico de memória e código de falha; exportar logs sem chaves, jogos ou saves.
2. **Verificar baseline**: a R13 Experimental atual (Arceus fecha CE-34878-0 antes do idioma) vs R13 anterior (atingia idioma), New Eden 04.89 e um homebrew leve. Reproduzir no PS4 Pro.
3. **Auditar cache de shaders**: por que é desligado na base; provar diretório funcional e integridade; isolar código experimental numa branch. Testar cold/warm-start sem misturar caches. Se quebrar, voltar ao estado desligado.
4. **Investigar gargalo de CPU/JIT**: perfis de tempo; comparar patches Eden Android/Orbis-EDEN por algoritmo e ABI. Evitar `fastmem` sem garantia de mapeamento de memória.
5. **Implementar opções reais**: apenas se cada botão tiver backend, gravação, leitura e teste. Priorizar perfis por jogo, cache (se seguro), diagnóstico de performance e restauração de padrões. Não incluir sliders cosméticos, NCE ou Turnip.
6. **Build e testes**: preflight, CI, PKG com hash e instalação em revisão separada; comparar Silksong e Pokémon Legends: Arceus (boot, idioma, menu, gameplay, crash, FPS, áudio, retorno e saves).
7. **Preservação**: manter New Eden e versões anteriores; nunca apagar keys/firmware/jogos; não incluir conteúdo protegido no GitHub.

## Referências

- Eden4 fixado: https://github.com/xatyy/Eden4/tree/fab246cbac93c7995aaf451dca83ae93ba0bd234
- Eden4 limitações: https://github.com/xatyy/Eden4/blob/main/docs/KNOWN_ISSUES.md
- Orbis-EDEN: https://github.com/MrKitsune9/Orbis-EDEN
- Port RADV, contexto PS4: https://github.com/orbis-ports/ps4-mesa-docs
- Patch PS4 pequenos command buffers: https://github.com/alechurri/nx-on-orbis/blob/main/patches/eden/0015-PS4-submit-smaller-command-buffers-the-driver-flatte.patch
- Documentação de opções de Eden: https://github.com/NimaWoods/Eden-Emulator/blob/master/docs/user/Settings.md

**Próximo marco não concluído:** instrumentação e validação da R13 no hardware. Esta nota não deve ser descrita como otimização já aplicada ou PKG pronto.
