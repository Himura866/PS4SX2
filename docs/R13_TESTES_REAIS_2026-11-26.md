# HIMURA SWITCH PS4 R13 — testes reais do usuário (26/11/2026)

## Ambiente
- PS4 Pro desbloqueado com GoldHEN.
- Emulador HIMURA SWITCH PS4 R13 instalado para teste.
- Este relatório registra sintomas relatados e observáveis; ainda não estabelece causa-raiz.

## Casos observados
| Jogo | Resultado | Confirmação |
| --- | --- | --- |
| Hollow Knight: Silksong | Menu e introdução aparecem. Na transição para gameplay: tela preta, ~0 FPS por longo período; depois o aplicativo fecha. | Relato direto do testador. |
| BMX City Run | Fica em "Loading" por pelo menos 36 s no vídeo; não chegou a abrir mesmo após gravação. | Vídeo e confirmação posterior do testador. |
| Mario Kart 8 Deluxe | Permanece na tela de título com o nome do jogo sem seguir para os menus ou corridas. | Relato direto do testador. |
| Terceira gravação 20261126_123041.mp4 | Aproximadamente 31,55 s, TV sem gameplay visível; indicador FPS 0,0 em diversos momentos. | Revisão de frames do vídeo. Jogo exato não identificável na gravação. |

## Hipóteses a verificar, NÃO correções confirmadas
1. Guest CPU/JIT ou um serviço do sistema esperando permanentemente numa fase de boot.
2. Renderização/VideoOut ou fila Vulkan travada após troca de cena.
3. Erro no carregamento de recursos, jogo/update/DLC/firmware ou configurações.
4. Pressão de memória direta do PS4 Pro durante compilação de shaders ou transição para gameplay.
5. Referências úteis: Orbis Eden usa outra revisão do núcleo do Eden e documenta Mario Kart 8 Deluxe chegando às corridas com ~13–16 FPS, porém ainda com demora de carregamento e uso alto de RAM; essas métricas não são comparáveis diretamente à nossa R13. Código-fonte: https://github.com/MrKitsune9/Orbis-EDEN

## Diagnóstico requerido antes de alterar núcleo
- Reproduzir em apenas um jogo por vez e exportar logs via opção do emulador.
- Arquivos úteis: `/data/EdenPS4/HIMURA_R13_GAME_STATUS.txt`, `eden.log`, `crash.log`, `samples.log`, `boot-trace.log`.
- Não compartilhar arquivos de chaves `prod.keys` ou `title.keys`.
- Comparar contadores a cada 10 s: `quadros_compostos`, `video`, `audio`, `memoria_extra_mib`.
- Se composições avançam mas VideoOut não, investigar apresentação. Se tudo estaciona, investigar guest CPU, deadlock, erro/timeout de serviço ou carregamento.
- Confirmar em qual commit e PKG o problema foi reproduzido e registrar versão do jogo, atualizações e se NSP ou XCI.
- Comparar a solução com código upstream pontualmente; evitar substituição em bloco sem testes.

## Estado das correções
- A correção dos controles fictícios no papel de parede foi **preparada** na branch `himura-switch-r13-user-tests-staging` e **ainda não comprovada em PKG**.
- Uma adaptação Mii para alguns jogos, inclusive Mario Kart, existe em outra ramificação `himura-switch-r13-mii-compat-staging`; **não comprova solução da tela de título**, que ocorre antes da seleção Mii.
- Nenhuma correção dos congelamentos foi comprovada ainda em execução real no console.

## Comparativo confirmado em 26/11: lançamento Orbis Eden de 25/11
- Fonte oficial: https://github.com/MrKitsune9/Orbis-EDEN, commit `f004df1c7a812cc65703d8f937d0bd12a6d06a58` de 25/11/2026.
- Base Orbis Eden: Eden `5f142c79` + 46 patches PS4, OpenOrbis/Mesa RADV, difere da base Eden4 `fab246cbac93c7995aaf451dca83ae93ba0bd234` usada pela R13. **Não presumir compatibilidade binária dos patches.**
- A release Orbis Eden v2026-11-25 relata primeira imagem de Mario Kart 8 Deluxe em ~45 s e 30 FPS por volta de ~55 s. Página: https://store.brewology.com/ps4/orbis-eden/ . Sem gravação pareada e logs do mesmo console, não equiparar esses valores aos da R13.
- A documentação do código base ainda descreve menus a 40–60 FPS e corridas de MK8D a 13–16 FPS nos testes anteriores. **60 FPS de menu não equivale a 60 FPS de gameplay.**
- Recursos da release 25/11: configurações por jogo; cópias de segurança de saves; medição do tempo de carregamento `boot.log`/`tools/analyze-boot.py`; melhorias de configuração; suporte USB em teste.
- Ainda não foi possível vincular, com prova oficial, o nome informal "New Eden v0.4.89" a esse commit ou a um pacote específico. Solicitar link exato se for necessário validar essa revisão.
- Próxima fase técnica: isolar diferença em serviços Mii, CPU accuracy, inicialização de conteúdos/firmware, memória do processo e transição JIT->Vulkan, usando logs reais antes de mexer no core. Não declarar que importar patches elimina congelamentos.
- Em 26/11, o estado GitHub do commit de CI R13 `08c93c95904bbf56d1677d5d8ebd203cae1e5e7e` tinha os dois checks CircleCI em `success`; isso comprova validação e compilação, **não compatibilidade de jogos**.
