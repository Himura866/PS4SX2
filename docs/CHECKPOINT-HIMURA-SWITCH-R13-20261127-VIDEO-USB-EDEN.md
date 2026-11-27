# HIMURA SWITCH — CHECKPOINT DE CONTINUIDADE (27/11/2026)

**Estado:** salvo para retomar em outra conversa, sem depender do contexto do chat. Documento de estado verificável. **Não declara correções ainda não implementadas.**
**Regra:** não alterar `main`, não sobrescrever R13 funcional nem New Eden 04.89; somente CircleCI (não GitHub Actions). Não armazenar ROMs, DLCs, prod.keys, title.keys nem firmware no repositório/Drive compartilhado.

## Identificação e fonte verdadeira
- Projeto: **HIMURA SWITCH** para PS4 Pro GoldHEN.
- Base em avaliação: R13, title ID **HIMU00011**, versão instalada/manifesto **01.13**. Não chamar V15/R15 de versão estável antes de boot+gameplay comprovados.
- Referência externa funcional no console relatada pelo proprietário: **New Eden 04.89**, `EDNP00001`, `IV0000-EDNP00001_00-EDENPS4000000000`. No console do usuário abriu e foi possível jogar **Hollow Knight: Silksong** e **Pokémon Legends: Arceus** (com restrições de resolução); isso é evidência sobre New Eden, NÃO sobre a R13.
- R13 utiliza checkout fixado `xatyy/Eden4` commit `fab246cbac93c7995aaf451dca83ae93ba0bd234`, empacotado pelo OpenOrbis/Mesa.
- R13 última base comprovada por teste antigo do usuário: `himura-switch-r13-stability-staging` @ `08c93c95904bbf56d1677d5d8ebd203cae1e5e7e`; menu abre, porém jogos falham antes do gameplay.
- Nova linha de implementação de navegação USB: `himura-switch-r13-usb-browser-safe-20261127` @ `f79fa30612a7352c5c9cdeae4da0fad2ddcbea56`. **CircleCI validou e compilou**, mas a revisão de USB NÃO foi testada fisicamente no PS4.
- Cópia da ramificação para checkpoints (este arquivo): `himura-switch-r13-checkpoint-20261127`. Ramificação `himura-switch-r13-ps4-gpu-submit-20261127` foi criada a partir da mesma base sem implementação GPU confirmada; não afirmar que otimizações foram portadas.
- Documento anterior de ponte do motor: `himura-switch-r13-ui-neweden-0489-bridge` / `docs/R13-UI-NEWEDEN-0489-BRIDGE-20261126.md`: projeto arquitetural, não implementação do motor New Eden.

## Status CI auditável (em 27/11)
- R13 USB commit `f79fa30612a7352c5c9cdeae4da0fad2ddcbea56`
  - `ci/circleci: validar_r11_antes_do_pkg`: **success**
    https://app.circleci.com/workflow/577fe473-1414-4632-a347-a57824fc839d/job/5185e430-f4c7-4253-bdd1-7e47350bc35b
  - `ci/circleci: compilar_eden4_pkg_r11`: **success**
    https://app.circleci.com/workflow/577fe473-1414-4632-a347-a57824fc839d/job/e4318482-46a0-4029-8a74-fecd8d4657ac
- R13 anterior `08c93c9...`: validação+PKG também success, mas isso NÃO implica gameplay nem ausência de crash.
- V15 experimental baseada em repack New Eden apresentou erro de aplicativo/dados corrompidos no hardware; não recomendar instalação. Original 04.89 guardado pelo usuário.

## Revisão do VÍDEO REAL enviado em 27/11/2026
- Arquivo original na conversa: `20261127_132602.mp4`, ~40 s, vídeo do PS4/TV. **O anexo da conversa não é link durável entre chats**; pedir reenvio se não houver acesso ao original.
- Revisão quadro a quadro: menu com samurai e cenário de lua/paisagem vermelho-escura. Usuário aprovou o MENU PRINCIPAL funcional nesta versão. Defeitos visuais identificados:
  1. cinco placas/retângulos azul/preto no local de capas mesmo sem jogos, parecendo capas falsas;
  2. **bases** azul-escuras sob as capas e tracinhos/dots/números/indicadores impressos embaixo do carrossel;
  3. seta azul lateral falsa; não substitui navegação do controle;
  4. faixa preta cobrindo a paisagem avermelhada no rodapé e linha separadora;
  5. usuário quer a MESMA paisagem prolongada até `y=1080`, inclusive abaixo dos botões X/User Page, sem esticar/desfigurar o samurai;
  6. remover badge visual `R13` ao lado de `SWITCH PS4` na tela principal; versão pode existir na tela Sobre e metadados.
- Manter exatamente o ícone externo samurai aprovado e arte interna aprovada, controles REAIS e clicáveis, letras PT-BR, capas quadradas de jogos reais com ampliação + neon na selecionada. Sem jogo real: nenhuma capa fictícia.
- Causa localizada diretamente no código, não conjectura:
  - `ci/patch-r11-approved-menu.py` usa `c.DrawImage(picture,0,0)` de uma IMAGEM com mockups, e depois ***8+ máscaras*** `c.FillRoundRect(... {0x090e1b})` nas 5 posições das capas, setas e indicador e `c.FillRect(0,970,Canvas::Width,110,{0x070911},1.0f)` + `c.HLine(...,969,...)` no rodapé. Também injeta `c.Text("R13",...)`.
  - `ci/patch-r11-approved-menu.py` ainda injeta outro fundo opaco atrás de **cada jogo** após a âncora `const bool focused = ...`.
  - `ci/generate-r11-branding.py` substitui pixels 992–1079 por **cor lisa** `(7,9,17)` e não recupera a paisagem.
  - `ci/r11-preflight.sh` ATUALMENTE exige explicitamente máscaras/faixa opaca/pixels lisos, isto está **em conflito com o objetivo final**. Modificar preflight juntamente com o asset real, não apenas deletar máscaras.
- Assets originais protegidos em `assets/r11-approved-icon.webp` sha256 `ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778`; `assets/r11-approved-menu.webp` sha256 `b36c6a9eb5af0ee280c52845c91ca2f3a04b68e79d4f85b620bba9c25705b058`. Não editar arquivo original nem trocar arte sem aprovação. Criar **novo** asset derivado `r13-menu-clean.*`, documentar SHA, renderizar preview lado a lado e somente depois integrar.

## USB, jogos, DLCs, updates, keys e firmware
- Teste real informado: em **Game Files → Add Folder**, `USB 1` aparece **disconnected**, mesmo com HD externo conectado no console. O usuário também quer opções USB 0 e USB 1 (conforme nomenclatura solicitada) e todas as unidades montadas; detecção deve ser por caminho real montado, não confundir rótulo/porta física.
- `xatyy/Eden4` tem `SourceDefs()` em `eden/src/yuzu_ps4/main.cpp`: enumera `/mnt/usb0` como `USB 1` (índice+1) e mostra os demais apenas se `IsDirectory(path)`. Exatamente por isso a tela pode mostrar `USB 1` desconectado sem listar a unidade real; também se o HD não estiver montado em `/mnt/usbN` o navegador não encontra. É necessário diagnosticar **mount real** e permissões, não só adicionar labels fictícios.
- `ci/patch-r13-usb-browser.py` implementa modal `FolderPicker` com controle e `AddSource(path)`, substituindo teclado; limite de varredura 4096 diretórios, profundidade 4. Foi integrado em `ci/build-r11-samurai-library.sh` e pré-validação, mas a detecção USB física **ainda não foi corrigida nem verificada**. Observação para revisão: no Python `patch_launcher` altera `ui_launcher.cpp`; se ocorrer erro de ancoragem, CI deve falhar. Rever a condição `if (!source.removable && ...)` e separação entre origens fixas e custom.
- Requisito final: menu em PT-BR em todas as telas, incluindo Game Files, Settings e **Sobre** (créditos/atribuições mantidos). Interface de instalação como New Eden: escolher pasta por DS4 sem teclado, identificar NSP/XCI/NRO/NSO e updates/DLCs (respeitando formato/compatibilidade), oferecer seleção de keys e firmware local **com prévia e confirmação**, importar para destinos corretos de modo **não destrutivo**, preservar dados/saves existentes e opção para indexar jogos direto do HD sem copiar gigabytes. Não expor arquivos de keys em logs/CI.
- As funções de importar firmware/keys/DLCs/updates ainda **NÃO foram implementadas** na R13; não confundir scan de jogos com instalador de conteúdos e NAND.
- O código `main.cpp` original mantém estado em `/data/EdenPS4/ui-state.ini` e opções em `/data/EdenPS4/ps4.ini`; preservar ambos em upgrades.

## Compatibilidade, desempenho e boot
- Prioridade: tirar o crash/carregamento que impede gameplay na R13. No console do usuário, New Eden inicia Silksong e Arceus; não prometer igual desempenho só copiando patches. Portas de GPU/JIT requerem comparação real de versões/dependências/ABI e testes A/B no hardware.
- Estudar `MrKitsune9/Orbis-EDEN` e upstream `xatyy/Eden4`; em particular RADV GFX7 (indirect draw), comandos GPU menores, memória/cache e JIT; **não aplicar patches cegamente**.
- Usuário quer abertura rápida **direto no menu biblioteca**, sem mostrar de novo a capa EXTERNA após clicar no app. Examinar splash do sistema vs splash interno; não prometer eliminar tela de sistema que dependa do Orbis.
- O objetivo de próximo pacote é um teste incremental com logs de boot+USB+render+game. Não alterar ID de app sem garantir integridade; não sobrescrever instalação funcionando; nunca declarar compatibilidade 100%.

## Próxima sessão — ordem exata para retomar
1. Abrir ESTA documentação e obter estado atual dos branches/CI; verificar e anotar SHA do HEAD. Perguntar qual build o vídeo mostra apenas se crucial para comparar (o vídeo por si demonstra o defeito).
2. Preservar o menu aprovado. Criar/validar **asset limpo** com o MESMO samurai e paisagem até o pé da tela (sem botões, capas fictícias, setas, traços). Revisar imagem visualmente. Adaptar script de branding e eliminar as máscaras do backdrop + filler debaixo das capas; atualizar preflight com teste de SHA/qualidade dos assets limpos.
3. Corrigir nomenclatura e sondagem do USB real no PS4, listar USB0/USB1 e detectados dinamicamente, mostrar erro diagnóstico de montagem/permissões ao invés de `disconnected` falso; preservar USB ao desconectar.
4. Traduzir todos os textos visíveis (especialmente Sobre e Game Files), remover apenas badge `R13` do cabeçalho (manter versão em metadados/Sobre).
5. Implementar com testes isolados importação opt-in de firmware, keys, DLCs/updates; evidenciar o que foi instalado em NAND e reversão/backup.
6. Validar e adaptar melhorias específicas New Eden, com comparação de fontes e A/B: desempenho/compatibilidade/PS4 GPU sem regressões.
7. CI: preflight -> compilação PKG com caches -> conferir SHA e composição/assets -> teste hardware: boot, entrar no menu, detectar USB, adicionar jogo, Silksong gameplay, Arceus gameplay, áudio/controles/retorno ao menu, logs de falha. Relatar PASS/FAIL para cada gate.
8. Salvar **NOVO checkpoint** deste template e link do artefato/commit/teste na pasta de continuidade Google Drive; não sobrescrever um checkpoint anterior, se necessário criar versão datada.

## Links permanentes
- Branch do código com seletor USB compilado: https://github.com/Himura866/PS4SX2/tree/himura-switch-r13-usb-browser-safe-20261127
- Pipeline da compilação R13 USB: https://app.circleci.com/workflow/577fe473-1414-4632-a347-a57824fc839d
- Branch do código anterior: https://github.com/Himura866/PS4SX2/tree/himura-switch-r13-stability-staging
- Documento de critérios de UI/USB: `docs/R13-SAMURAI-USB-IMPORT-ACCEPTANCE-20261127.md`
- Pasta privada histórica do projeto no Google Drive: https://drive.google.com/drive/folders/1bussrRWAonydkoVcvRHXvfVkcn5G982C
- Documento mestre de continuidade anterior no Google Docs: https://docs.google.com/document/d/1BpN2J8mFHHsz8K_dEZsuKiQgYO3_WFFGGzlQQCs3uhk/edit

**Notação de status:** fonte salvo em GitHub ✓; CI compilação ✓; defeito visual diagnosticado ✓; correção de asset de produção ✗; USB detectado no PS4 ✗; importação keys/firmware/DLC/updates ✗; Silksong jogável na R13 ✗; PKG final para teste ✗.
