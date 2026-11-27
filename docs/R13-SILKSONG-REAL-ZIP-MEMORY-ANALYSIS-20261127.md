# HIMURA SWITCH R13 — análise real do switch.zip (Silksong, 27/11/2026)

## Evidência fornecida pelo usuário
O arquivo ZIP enviado contém **crash.log**, **eden.log** (12.244 linhas) e **HIMURA_R13_GAME_STATUS.txt** (32 linhas), referentes a uma tentativa de Hollow Knight: Silksong. Este documento resume somente os indicadores necessários e não publica o log integral (que contém caminhos de usuário, nomes de cópias e registros brutos de memória).

## Falha principal
- **`crash.log`: 8 seções com `uncaught exception std::bad_alloc` e `signal 6 (code 65543)`. O relatório não possui timestamps por seção, e pode conter execuções acumuladas: não assumir que as 8 seções são da última tentativa. `std::bad_alloc` significa que uma alocação de memória no processo host falhou; a pilha é de endereços não simbolizados, então o subsistema e a solicitação exata ainda são desconhecidos.**
- **`eden.log` e `HIMURA_R13_GAME_STATUS.txt`:** são explicitamente da inicialização de Silksong. CPU, contêiner e GPU avançam sem falha imediata. O primeiro quadro é composto/apresentado. No último checkpoint, há **6.017 quadros compostos / 6.017 flips, 10.194 buffers de áudio** e **310 MiB de heap extra**. O vídeo estagnou repetidamente durante alguns intervalos (por exemplo, 3.588 quadros mantidos por um intervalo de 10 s), mas voltou a progredir em seguida. **Não confundir quedas temporárias com GPU completamente travada.**
- O `eden.log` termina por volta de **250,8 s** de processo sem mensagem de desligamento normal e sem `std::bad_alloc` nessa execução; a exceção está no arquivo separado de crashes.
- **Memória de GPU/PS4:** ao iniciar o jogo o maior bloco de memória direta livre era **484.976 KiB** e orçamento Vulkan informado **511 MiB**. Durante o jogo, o maior bloco livre desceu progressivamente e estabilizou em **203.968 KiB (~199 MiB)**. O restante não comprova falta de memória total, mas mostra pressão/fragmentação e demanda de alocações.
- **`memory callbacks`** do PS4 chegaram a **76.153.667** antes da saída. Investigar pressão de memória/JIT e o custo dessas chamadas, sem pressupor leak.
- **JIT Dynarmic:** mais de **480.000 blocos** reportados em um pool, com **5 limpezas de cache**. O custo acumulado de emissão estava em ~32,8 s; isso merece profiling seletivo na execução em PS4.
- Opções reais em `eden.log`: **modo portátil** (`docked=0`), saída **720p**, **Vulkan**, `profile=on`, opções de JIT `inline_memory=1`, `direct_table=1`, `page_reuse=1`, `regalloc=on`. O log mostra `PS4 Pro mode: off` embora o usuário tenha PS4 Pro; verificar como o PKG é inicializado e a sinalização Neo do sistema antes de assumir potência Pro disponível.
- Avisos secundários: `No control data found for program` no NSP, `joycon` engine desconhecido, alguns `HW.Memory Unmapped @ 0xffff...` e avisos `Shader (STUBBED)`. Não os classificar como causa direta sem reprodução isolada. Também há uso de versão de firmware codificada em fallback, não comprova que o firmware instalado está completo.

## Prioridades técnicas, com critério de aceite
1. **Não liberar PKG como jogável até o teste real no console.** Antes de novo build, instrumentar alocações que falham: distinguir heap C++, memória direta/GPU, cache de shaders, JIT e processamento de texturas; registrar tamanho solicitado, fase, thread, orçamento/largest free block. Garantir segurança de escrita e pouco overhead.
2. **Conter pressão de memória sem crashes silenciosos**: revisar `ps4_heap_set_overflow_gpu_reserve(256 MiB)` e roteamento de reservas. Não aumentar ou diminuir a reserva arbitrariamente sem medir efeito. Verificar fragmentação da memória direta e estratégias de cache/evicção do Vulkan e JIT.
3. **Desligar o profiler de amostragem em testes de desempenho normais**, preservando-o como modo de diagnóstico (`profile=off`). Em `profile=on`, o `eden.log` é extremamente volumoso (inclui blocos e dumps de memória), o que pode gerar custo adicional. Isso não é uma correção demonstrada do crash.
4. **Comparação controlada**: mesma ROM, mesmas keys, mesmo modo portátil, cache e firmware nas variantes A/B R13 e New Eden 04.89. Primeiro confirmar vídeo introdutório -> controle jogável por pelo menos 10 minutos, depois FPS/áudio/menu/saves.
5. **Entender por que o modo Pro aparece desligado** no log. Não forçar `sceKernelIsNeoMode()` sem validar o que o sistema e o PKG permitem.
6. **Simbolização de endereços do crash**: preservar SHA do eboot.bin/ELF da versão instalada; usar mapa/linker ou ELF com símbolos correspondente para mapear `0x1c61bce`, `0x1ca17e6`, `0x1c6204e` e outros frames. Sem binário compatível, não adivinhar função pelo endereço.

## Conclusão e nível de certeza
**Alta confiança:** crash.log reúne exceções de alocação `std::bad_alloc`, sugerindo falha real de memória na família de builds; Silksong avança além do boot e tem demanda crescente da memória direta. **Média confiança:** pressão de memória/fragmentação está envolvida no fechamento relatado. **Não demonstrado:** qual função aloca, se há vazamento, se esse último teste foi uma das 8 exceções, se extensão RADV é causa, se forçar Pro resolve.

## Estado do desenvolvimento
No último acompanhamento, commit `95a8639` teve pré-validação aprovada e build PKG ainda pendente. Branch de diagnóstico anterior `himura-switch-r13-silksong-crash-and-brand-20261127` tinha falhado preflight; os resultados acima são análise **de arquivos de usuário**, não validação de um patch jogável.

Preservar New Eden original, R13 atual, saves, firmware, keys. Não publicar os logs brutos no repositório.
