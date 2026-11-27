# HIMURA SWITCH V13 — ÚLTIMO CHECKPOINT

## REVISÃO MAIS RECENTE — V13 | GPU GFX7 / CRASH (27/11/2026)

**Trabalho código realizado:** branch isolada `himura-switch-v13-ps4-gpu-batch-20261127` @ `f8525d932bebea1178c4719c0e6a00ec3195d7d5`. Adaptado do patch público Orbis-EDEN 0015 para a fonte Eden4 com macro real **`__OPENORBIS__`**, sem modificar o New Eden original: reduz batches de 4096 para 256 desenhos na GPU PS4 e faz flush a partir de 96 uploads; reseta contador por novo contexto Vulkan. Cinco arquivos adaptados com teste preflight. Android e PC seguem com suas políticas anteriores. **HIPÓTESE DE CRASH, NÃO SOLUÇÃO HOMOLOGADA.**
- Patch: https://github.com/Himura866/PS4SX2/blob/himura-switch-v13-ps4-gpu-batch-20261127/ci/patch-v13-gpu-batch.py
- Documentação técnica de diagnóstico e testes: https://github.com/Himura866/PS4SX2/blob/himura-switch-v13-ps4-gpu-batch-20261127/docs/V13-GPU-CRASH-TESTE-20261127.md
- CircleCI desta revisão: **pré-validação SUCCESS** https://app.circleci.com/workflow/f2aa990f-ba64-408d-8e89-e8a7f2827426/job/afc7a13d-7334-43d2-9925-a9a85bfc6b61 ; **compilação PKG PENDING** https://app.circleci.com/workflow/f2aa990f-ba64-408d-8e89-e8a7f2827426/job/f71f2f5e-629f-484e-8e9a-ca863cd90103 ; sem teste físico PS4.
- Meta de teste no PS4: Silksong e Pokémon Legends: Arceus abrirem e executarem gameplay; medir FPS/áudio, verificar retorno ao menu e USB. Se crashar, exportar `/data/EdenPS4/HIMURA_R13_GAME_STATUS.txt`, `eden.log`, `boot-trace.log`, `crash.log`. Não enviar keys/firmware/ROMs.
- Outras tarefas V13 continuam pendentes e preservadas: imagem do samurai sem botões/capas falsos, fundo até rodapé, carrossel sem placas/tracinhos, importação real de updates/DLC/keys/firmware, português total, splash duplicado, USB detectado no hardware. Compilar apenas CircleCI; manter base funcional inalterada.

**Regra de retomada agora:** conferir PRIMEIRO esta branch de GPU e seu CI, NUNCA compilar a branch de documentação `himura-switch-r13-checkpoint-20261127` como se tivesse código novo. O New Eden 04.89 já funcionou no PS4 do usuário; não se pode atribuir automaticamente a ele patches de outro projeto sem seu código-fonte correspondente.

**NOME CANÔNICO PARA PESQUISA: `HIMURA SWITCH V13 — ÚLTIMO CHECKPOINT`**  
**ATALHOS DE BUSCA:** `CHECKPOINT V13`, `HIMURA SWITCH V13`, `V01.13`, `R13`.  
**PROJETO EXATO:** emulador **HIMURA SWITCH para PS4 Pro / GoldHEN**, não HIMURA FIVE (PS5), HIMURA PS2, V15 experimental, nem outros projetos.

> **Instrução de retomada para novos chats:** Primeiro pesquisar pelo documento do Google Drive **HIMURA SWITCH V13 - ULTIMO CHECKPOINT** e por este arquivo **CHECKPOINT_V13.md**. Só depois consultar a ramificação de trabalho indicada abaixo. Não selecionar automaticamente o checkpoint V15/R14 ou um checkpoint antigo só por data. Quando houver revisão posterior da mesma V13, atualizar este documento e o Google Doc mantendo esse título.

## Onde está o trabalho verdadeiro

- **Ramificação de implementação em andamento (código):** `Himura866/PS4SX2` — **`himura-switch-v13-ps4-gpu-batch-20261127`** (com a base PT-BR/USB preservada em `himura-switch-r13-ptbr-usb-20261127`).
- **Último commit de código confirmado ao registrar:** **`f8525d932bebea1178c4719c0e6a00ec3195d7d5`**. Aguardar CI e teste real.
- **Versão do aplicativo/PKG:** `01.13`; título `HIMU00011`. "V13" é o **apelido fácil do checkpoint**, não um novo número técnico inventado.
- **Branch onde fica este arquivo:** `himura-switch-r13-checkpoint-20261127` (**somente checkpoint**, NÃO compilá-la como se fosse a ramificação mais atual).
- **Base anterior preservada:** `himura-switch-r13-usb-browser-safe-20261127` @ `f79fa30612a7352c5c9cdeae4da0fad2ddcbea56`.
- Código: https://github.com/Himura866/PS4SX2/tree/himura-switch-v13-ps4-gpu-batch-20261127
- Base PT-BR/USB preservada: https://github.com/Himura866/PS4SX2/tree/himura-switch-r13-ptbr-usb-20261127
- Checkpoint detalhado da implementação: https://github.com/Himura866/PS4SX2/blob/himura-switch-r13-ptbr-usb-20261127/docs/CHECKPOINT-HIMURA-SWITCH-R13-20261127-PTBR-USB-IMPLEMENTATION.md
- Checkpoint visual e vídeo original: https://github.com/Himura866/PS4SX2/blob/himura-switch-r13-checkpoint-20261127/docs/CHECKPOINT-HIMURA-SWITCH-R13-20261127-VIDEO-USB-EDEN.md
- **Google Drive — este checkpoint canônico, mesmo documento que já continha as melhorias da R13:** https://docs.google.com/document/d/1u-Yn2PMxjPPF9n2w0x7iWG_a-TMw90LXeOiLvX0A-ac/edit?usp=drivesdk

## Situação verificada em 27/11/2026

- **Implementado no código:** pasta/HD via controle com indexação de jogos; melhorias de identificação USB 0/1 (`/mnt/usb0`, `/mnt/usb1`), aviso de pastas inacessíveis e traduções PT-BR em diversas telas; scripts integrados à receita PKG da R13.
- **CircleCI no commit `6146f76`:** `validar_r11_antes_do_pkg` **SUCCESS**; `compilar_eden4_pkg_r11` **PENDING** na última consulta. Acompanhar: https://app.circleci.com/workflow/a160f40a-3b31-4af7-b1bf-34a6ee4a8bce/job/d50af57d-20d9-42cd-8326-c721acfbb64d
- **PKG novo desta revisão:** ainda **não confirmado como compilado e instalável**. Não declarar pronto pelo simples fato de o preflight passar.
- **Teste no PS4 Pro:** ainda não realizado nesta revisão. A R13 anterior abriu o menu; isso **não prova** que a R13 roda Silksong ou Arceus.
- **New Eden PS4 Edition 04.89:** o usuário relatou jogar Hollow Knight: Silksong (e testar Arceus) nele; a execução **não foi portada** para a R13. A ponte R13 visual + motor New Eden é ainda uma investigação técnica, não uma fusão pronta: https://github.com/Himura866/PS4SX2/blob/himura-switch-r13-ui-neweden-0489-bridge/docs/R13-UI-NEWEDEN-0489-BRIDGE-20261126.md

## O que o usuário pediu manter e corrigir

1. **Mesmo samurai, lua vermelha e cenário original aprovado** no menu interno, até o rodapé. **Retirar** capas e botões fictícios pintados na imagem, placas preto-azuladas, seta, indicadores e faixa preta. Ícone/capa externa diferente de wallpaper interno; **não cobrir o menu** com splash.
2. **Capas reais quadradas** dos jogos encontrados, carrossel modernizado, destaque neon ao selecionar, botões de verdade e navegação funcional do controle PS4. Sem capas falsas se biblioteca estiver vazia.
3. **Interface PT-BR**, arquivos e pastas USB/HD com navegação real. Preservar keys/firmware/saves já funcionando, sem limpeza destrutiva. Importação de keys/firmware/updates/DLCs **não concluída**; não confundir achar pasta com instalar.
4. Melhorar tempo de build **sem prometer duração**, carregamento, GPU/CPU/Vulkan, som sem chiado, estabilidade de Silksong após a abertura, voltar ao menu e encerrar sem crash; medir FPS real.
5. Prioridade: **PKG real**, com hash/artefato CircleCI auditável, **e teste no PS4** antes de afirmar compatibilidade. Não sobrescrever a versão New Eden original que funciona.
6. **Somente CircleCI**, não GitHub Actions; evitar builds desnecessárias. Não publicar jogos, keys, DLCs ou firmware em GitHub/Drive.

## Próxima ação para continuar exatamente daqui

1. Consultar o **status CircleCI do commit `6146f76e...`**, corrigir qualquer falha; só então verificar se foi produzido PKG e artefato com hash.
2. Tratar a **arte original R13**: gerar *novo* arquivo limpo derivado da imagem aprovada (preservar original), retirar as máscaras opacas e **atualizar os testes preflight que atualmente exigem as máscaras**.
3. Validar navegador de HD no console; completar PT-BR e funções de importação com segurança.
4. Continuar a integração com **motor New Eden 04.89** somente por fonte compatível/mecanismo validado, nunca copiar `eboot.bin` de um projeto por cima do outro.
5. Teste real de boot, seleção de jogo, Silksong/Arceus, áudio, FPS, retorno ao menu e dados; publicar resultado como **confirmado**, **falhou**, ou **pendente**.

**Regra de memória:** *Quando o usuário disser “prossiga do último checkpoint V13 do Himura Switch”, este é o documento de entrada. O código verdadeiro está em `himura-switch-r13-ptbr-usb-20261127`; o apelido V13 nunca deve redirecionar para V15 ou outros projetos. Conferir sempre se existe commit mais recente na ramificação de código.*
