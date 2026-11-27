# HIMURA SWITCH — checkpoint R13 de diagnóstico `std::bad_alloc` (27/11/2026)

**Base preservada:** `himura-switch-r13-next-pkg-integration-20261127`, commit `95a863987a93742c069aac751ba9f65f527af67b` (CircleCI compilação `compilar_eden4_pkg_r11`: **success**, 8/8 testes pré-build concluídos; isso NÃO significa gameplay testado nem arquivo PKG auditado). Nova branch exclusivamente de instrumentação: `himura-switch-r13-oom-probe-20261127`.

## Evidência real

O usuário enviou `switch.zip` contendo `crash.log`, `eden.log` e `HIMURA_R13_GAME_STATUS.txt` após reproduzir o problema no Hollow Knight: Silksong. O crash.log acumula 8 relatos de `uncaught exception std::bad_alloc`, sem marcação que permita associar cada um especificamente à última tentativa. O log do jogo mostrou 6.017 frames compostos/flips e 10.194 buffers de áudio ao final, além de um maior bloco livre de memória direta de 199 MiB; houve progresso do jogo antes do fechamento. Em torno de 250,8 segundos, o jogo não tinha encerrado normalmente. O cache JIT relata 480 mil blocos compilados e cinco limpezas. O perfil por amostragem estava **ligado**. Nenhum destes dados, sozinho, aponta para o alocador exato ou comprova vazamento permanente.

## Implementação real nesta branch

- `ci/r13_memory_failure_probe.h`: grava um registro curto via `open`/`write`/`fsync`/`close`, sem alocação de `std::string`, no caminho legado `/data/EdenPS4/HIMURA_R13_OOM.txt`. Campos incluem origem, fase, bytes solicitados se conhecidos, código de erro, contagem de quadros, flips e MiB da reserva extra.
- `ci/patch-r13-memory-oom-probe.py` integra a instrumentação no checkout **fixado** `fab246cbac93c7995aaf451dca83ae93ba0bd234` durante o build: instala `std::set_new_handler` após criar a pasta de dados, registra a primeira falha de `operator new` por processo, e mantém o comportamento de lançar `std::bad_alloc`. 
- Instrumenta `HostMemory::Impl` na plataforma `__OPENORBIS__` para registrar tamanho e código de falha de `sceKernelAllocateDirectMemory` ou `sceKernelMapDirectMemory` antes de lançar `bad_alloc`.
- Acrescenta o arquivo `HIMURA_R13_OOM.txt` ao exportador de relatórios (Arquivos de jogos > Triângulo > USB), sem incluir chaves, firmware ou saves.
- `ci/test-r13-memory-oom-probe.sh` compila o registrador C++ no CircleCI, gera duas falhas artificiais e verifica os eventos persistidos em arquivo temporário.
- `ci/r11-preflight.sh` valida a aplicação do patch após os patches R13 anteriores, com base fixada, e exige a evidência do arquivo. `.circleci/config.yml` ativa as validações **apenas nessa branch**; **sem PKG extra automático**.

**Limitação relevante:** `std::new_handler` só registra falhas de `operator new` que invocarem o handler, não necessariamente todos os caminhos de `malloc`, biblioteca Vulkan, exceções `bad_alloc` lançadas manualmente ou falhas de heap proprietárias. Esse código **não elimina o crash**; coleta o ponto de falha com impacto mínimo para a próxima correção.

## Próximo passo

1. Só após preflight verde e compilação PS4 comprovada, instalar uma **variante de diagnóstico** sem substituir uma versão estável; manter New Eden 04.89 e saves intocados.
2. Reproduzir Silksong e exportar `HIMURA_R13_OOM.txt`, `HIMURA_R13_GAME_STATUS.txt`, `crash.log`, `eden.log`.
3. Cruzar origem `operator_new` ou `guest_RAM_direct_alloc` com runtime, maior bloco direto, estágio Vulkan e JIT. **Não aumentar/diminuir arbitrariamente** a reserva de GPU, nem desligar funcionalidades sem A/B.
4. Após identificar a função/allocador, implementar mitigação verdadeira (redução de pressão, reutilização, flush/cache adequado ou recuperação controlada), executar testes no PS4 até gameplay por ≥10 min.
5. Identidade pública do app/pastas = HIMURA SWITCH, com migração protegida das pastas legadas; manter créditos e licenças de terceiros. **Pasta /data/EdenPS4 não foi renomeada** aqui para evitar perda de dados.

Regra de entrega: nunca dizer que o próximo PKG ou gameplay estão prontos apenas porque o CI ou o teste nativo passou.
