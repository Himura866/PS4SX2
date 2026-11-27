# HIMURA SWITCH — checkpoint de implementacao R13 PT-BR / USB (27/11/2026)

> **Estado verificavel:** codigo commitado; validacao CircleCI iniciada. Nao equivale a PKG pronto nem a teste no PS4.
> Nunca sobrescrever `main`, a R13 funcional anterior nem o New Eden 04.89. Sem jogos, DLCs, keys ou firmware nos repositorios e backups.

## Bases
- Fonte preservada R13 com navegador USB: `himura-switch-r13-usb-browser-safe-20261127` @ `f79fa30612a7352c5c9cdeae4da0fad2ddcbea56`.
- Branch desta revisao: `himura-switch-r13-ptbr-usb-20261127`, iniciado da base acima.
- Primeiro HEAD com CI ativado: `0231b02a98b065197df64d24fdce7b664890ddb7`.
- HEAD atual ate esta anotacao: `235808948042ae7b824d7427c8f48861dce460ac`.
- Script novo: `ci/patch-r13-usb-ptbr.py`, aplicado por ultimo depois da sequencia de patches R13.
- Receita: `ci/build-r11-samurai-library.sh`; validacao em `ci/r11-preflight.sh` e `.circleci/config.yml`.

## Mudancas implementadas no codigo (ainda sem validacao no hardware)
1. `USB 0` corresponde a `/mnt/usb0`, `USB 1` a `/mnt/usb1`; ambos sao mostrados mesmo ausentes, os adicionais apenas se encontrados. Nao confundir indice do caminho com porta fisica do PS4.
2. Verificacao de disponibilidade usa `opendir` para saber se uma pasta realmente pode ser navegada; tela de Arquivos de jogos mostra o caminho inacessivel quando ha falha.
3. Traducao PT-BR incremental para partes da biblioteca, Arquivos de jogos, Sobre, creditos/licencas, informacoes e opcoes do sistema, preservando identificadores de configuracao e logica interna de "On/Off".
4. Verificacao automatica de indices USB, texto traduzido e patch do build. Build CircleCI habilitado para a nova ramificacao.
5. Nenhum novo dado de jogos, saves ou instalacao NAND e alterado por este patch; apenas apresenta a lista de pastas e indexa jogos como antes.

## Status CI da revisao
- Apos o commit `2358089480`, GitHub reportou `ci/circleci: validar_r11_antes_do_pkg` **pending**, sem conclusao de compilacao PKG nesse momento:
  https://app.circleci.com/workflow/b167db28-059e-4be4-8e5d-52c9330aba5a/job/8b5d5b52-3337-4a2d-a99a-2c7be117953f
- Preflight -> compilacao PKG -> SHA/artefato -> teste fisico devem ser reportados separadamente.

## Exatamente o que permanece pendente
1. **Arte:** remover realmente as capas falsas, setas, tracos e botoes impressos no bitmap original e prolongar a paisagem do samurai ao rodape; retirar mascaras opacas, badge R13 e base azulada do carrossel apenas depois de existir uma arte limpa aprovada; manter capas de jogos reais e neon. `ci/generate-r11-branding.py`, `ci/patch-r11-approved-menu.py` e `ci/r11-preflight.sh` ainda exigem antigas mascaras. Nao apagar as mascaras sem primeiro limpar a arte.
2. **USB:** ler USB0 e USB1 no PS4 Pro com HD conectado e confirmar quais mounts realmente existem e possuem permissoes; se falhar, exportar logs sem vazar dados pessoais.
3. **PT-BR:** revisar todo o menu e demais textos que continuem em ingles no console; checar largura das frases e acentuacao/fontes.
4. **Imports:** keys, firmware, updates e DLCs exigem fluxos proprios, selecao, confirmacao e backup, nao foram implementados aqui. Scanner de pasta nao equivale a instalar.
5. **Desempenho/compatibilidade:** portar melhorias New Eden somente depois da comparacao ABI/GPU/JIT/Mesa e testes A/B, especialmente Silksong e Pokemon Legends Arceus.
6. **Splash externo:** verificar sequencia Orbis e exibir menu interno diretamente quando permitido, sem bloquear o controle.
7. **Final PKG:** conferir CI, tamanho e hash de artefato, instalar/testar no PS4 Pro, registrar game boot/FPS/audio/USB/saves e voltar ao menu; somente entao declarar release utilizavel.

## Links permanentes
- Codigo desta revisao: https://github.com/Himura866/PS4SX2/tree/himura-switch-r13-ptbr-usb-20261127
- Base funcional de UI: https://github.com/Himura866/PS4SX2/tree/himura-switch-r13-usb-browser-safe-20261127
- Checkpoint anterior detalhado do video/arte: https://github.com/Himura866/PS4SX2/blob/himura-switch-r13-checkpoint-20261127/docs/CHECKPOINT-HIMURA-SWITCH-R13-20261127-VIDEO-USB-EDEN.md
- Video original enviado nesta conversa: `20261127_132602.mp4` (nao depender deste anexo em outra conversa).

**Proxima acao:** conferir resultado do job CI, resolver eventual erro de patch; depois criar arte limpa sem mascaras e integrar fluxos de importacao, com checkpoints a cada revisao importante.
