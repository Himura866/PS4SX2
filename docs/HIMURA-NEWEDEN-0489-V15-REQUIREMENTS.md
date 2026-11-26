# HIMURA SWITCH PS4 V15 — especificação consolidada

**Base obrigatória:** New Eden 04.89 instalado no PS4 Pro do usuário; `EDNP00001`, executável `eboot.bin` SHA-256 `5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381`. A etiqueta **V15** é a versão **visual/personalizada do HIMURA**, não é prova de alteração do APP_VER técnico 04.89.

## Interface aprovada

- O menu **Sobre / About** deverá exibir **HIMURA SWITCH PS4 — V15**, autores da base comprovados, créditos da personalização e licença aplicável. Preservar identificação técnica `Base New Eden 04.89` onde for adequado para suporte.
- Retirar completamente o item **News/Notícias** do **menu principal**, inclusive o destino e a possibilidade de foco/navegação.
- Retirar completamente o item **Temas** das **Configurações**, inclusive a seleção, navegação, telas de temas e dica de controle associada. Não remover recursos usados internamente por outros componentes sem análise.
- Toda a **interface interna em pt-BR**: textos, títulos, submenus, configurações, caixas de confirmação, mensagens de erro e seção Sobre. Pedido de interface "dublada": confirmar com o usuário se inclui **narração por voz**, em vez de presumir que legendas em pt-BR são dublagem.
- Botões de navegação **reais no topo**, não desenhados no papel de parede; fundo samurai interno sem a faixa inferior de botões fictícios.
- Capa externa `icon0.png` **somente na tela de aplicativos do PS4**, nunca sobrepondo o menu interno.
- Carrossel/grade de jogos sem painel preto invasivo, capas legíveis e seleção destacada; preservação de seleção, retorno, inicialização de jogos e áudio.
- Configurações de otimização **reais e funcionais**, não botões fictícios. Não afirmar que remover Temas por si só melhora FPS.

## Segurança técnica

- NÃO confundir código compilado experimental de Orbis-EDEN com o executável exato New Eden 04.89, mesmo que tenham ancestralidade comum.
- O executável binário embute as rotinas `Ui::HomeMenu::DrawHome`, `DrawSettings`, `Navigate`, `DrawBottomBar`, `DrawHeader` e `SettingItems`; alteração de texto **não remove ação nem item da navegação**.
- Os literais `News`, `Themes`, `About` e `New Eden 04.89` foram observados no binário, mas ainda **não se identificou de forma comprovada** a referência de todos os locais para substituição funcional da UI.
- **Nenhuma dessas remoções foi implementada** no executável original até este checkpoint. Documentação e auditoria de leitura não equivalem a PKG funcional.
- Alterações seguras: verificação prévia de SHA-256, cópia separada, manifesto de bytes alterados, revalidação de ELF, geração de pacote por procedimento compatível e testes no PS4 antes de marcar V15 como pronta.
- Não modificar código de emulação/JIT/GPU/áudio/saves; não renomear paths críticos nem TITLE_ID sem comprovação de compatibilidade.
- Compilar **somente pelo CircleCI** quando existir receita verificada para a **mesma versão 04.89** e não pelo GitHub Actions. Guardar todos os checkpoints na pasta Drive HIMURA SWITCH PS4 - CHECKPOINTS E BACKUPS.

## Gate de homologação V15

1. Sobre mostra V15 + créditos corretos, toda a UI em português.
2. News/Notícias e Temas **não aparecem nem podem ser selecionados**.
3. Menu usa controles reais no topo, arte interna samurai independente da capa externa e carrossel legível.
4. Teste no PS4 Pro confirma boot, jogos, áudio, saves, retorno e ausência de regressões, com resultados registrados.
5. PKG modificado com hash e logs salvo no Drive. Até lá, status **não compilado/não testado**.
