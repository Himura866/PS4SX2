# HIMURA SWITCH PS4 — modificar **o PKG New Eden 04.89 original**, não um emulador substituto

Esta branch é o ponto de trabalho para **o binário fornecido pelo usuário**: `NewEden-04.89.pkg`, SHA-256 `06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd`, `TITLE_ID=EDNP00001`, `APP_VER=04.89`.

**Não usar** os scripts `ci/himura-switch-build.sh`, `ci/r14-adapt-orbis.py` ou builds do Orbis-EDEN como se fossem reconstruções desse PKG. O código-fonte dessa revisão **não está identificado**. O job experimental `compilar_neweden_ui_r01` de outra branch foi criado antes da correção de escopo do usuário e não prova nada sobre o 04.89.

## Estado da análise técnica real

- PKG de 69.337.088 bytes, `PFS_IMAGE_OFFSET=0x80000` e `PFS_IMAGE_SIZE=0x41a0000`. Metadados `sce_sys/param.sfo` e `icon0.png` foram extraídos.
- O programa principal `eboot.bin` e a árvore interna `app0` **ainda não foram extraídos**. Sem esse material não é possível localizar as telas, temas, configurações e recursos editáveis dessa versão ou recompilar o mesmo aplicativo.
- O usuário confirma que esta versão funciona no PS4, mas não há teste independente de jogos nesta sessão.
- Não modificar os campos `TITLE_ID`, `CONTENT_ID`, caminhos críticos, executáveis, módulos ou saves apenas por renomeação. Preservar compatibilidade e rollback.

## Obter os arquivos do **mesmo aplicativo** sem computador

1. No PS4 desbloqueado, mantenha o New Eden 04.89 instalado e inicie-o.
2. Pelo PS4 Explorer 2.0/GoldHEN FTP, procure o diretório montado da aplicação `/mnt/sandbox/pfsmnt/EDNP00001-app0/`. O caminho exato pode variar conforme o sistema e o ambiente; este é um candidato comum, **não um caminho confirmado**.
3. Copie, se acessível, a pasta de arquivos montada `app0` — principalmente `eboot.bin`, `sce_sys/param.sfo`, as pastas de menu, temas e imagens. Copiar, **não alterar nem apagar** arquivos na instalação.
4. Transfira a cópia pelo Wi-Fi para o celular e compacte em ZIP; não inclua saves pessoais, chaves de jogo ou conteúdo de outros aplicativos.
5. Envie o ZIP para análise. `ci/check-neweden-app0.py` recusa uma versão diferente ou exportação incompleta.

## Depois que a extração for confirmada

1. Catalogar arte, menus, opções e binários **desta revisão**.
2. Aplicar o ícone/capa externa HIMURA e papel de parede samurai, retirando botões impressos. Manter **controles reais no topo**.
3. Melhorar carrossel/biblioteca, traduzir tudo para pt-BR e oferecer temas/configurações reais, créditos e licença correta, sem quebrar compatibilidade.
4. Montar novo PKG com mesmas dependências e ferramentas compatíveis; instalar primeiro como teste controlado, comparando boot, listagem de jogos, áudio e retorno ao menu no PS4 Pro.
5. Usar **somente CircleCI** para compilação quando existir uma receita verificada para este código/binário. Não disparar job de Orbis-EDEN chamando-o de New Eden 04.89.
6. Salvar logs, inventários, versões e resultados na pasta privada `HIMURA SWITCH PS4 - CHECKPOINTS E BACKUPS` no Drive.

**Estado atual:** inspeção e preparação do importador, **nenhum PKG alterado ou recompilado, nenhum jogo testado**.
