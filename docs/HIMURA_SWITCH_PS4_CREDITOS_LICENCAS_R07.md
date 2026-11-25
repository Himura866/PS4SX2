# HIMURA SWITCH PS4 — Area "Creditos e licencas" (requisito R07)

Solicitacao confirmada: no PKG final, incluir menu navegavel com controle PS4:
`Configuracoes > Sobre > Creditos e licencas`.

## Conteudo visivel
- Titulo da tela: "Creditos e licencas"
- Identidade: "HIMURA SWITCH PS4 — projeto independente"
- Mensagem: "Desenvolvido com base em projetos de codigo aberto. Obrigado aos desenvolvedores e colaboradores."
- Lista rolavel dos projetos cujo codigo realmente compuser o PKG: nome, contribuicao, link do codigo-fonte, licenca aplicavel.
- Acoes: `Voltar` (Circle), navegar (D-pad/analogico), `Ver licenca` e `Codigo-fonte` (Cross).
- Creditos nao devem ocupar tela inicial nem aparecer em cada jogo; porem devem permanecer acessiveis no menu e junto aos arquivos distribuidos.

## Creditos que precisarao ser preservados conforme a base final

### R06 (base atualmente usada)
- Eden e equipe de contribuidores — emulacao Switch, derivada de yuzu.
- yuzu e seus contribuidores — trabalhos anteriores.
- Orbis Eden — port de Eden para PS4, continuacao por Mr.Kitsune9 e colaboradores, originado de NX on Orbis de alechurri.
- OpenOrbis, orbis-ports, Mesa RADV, LLVM e outras dependencias incorporadas, respeitando os avisos/licencas existentes.
- Componentes e fontes citados em `MrKitsune9/Orbis-EDEN/NOTICE.md`.

### R07 (base experimental em avaliacao)
- Eden4 por xatyy e contribuidores — somente caso codigo Eden4 seja usado no PKG.
- DolphinPS4 por ShiroKlein e colaboradores — caso o runtime Eden4 seja utilizado.
- Incluir os autores, fontes, licencas, fontes tipograficas e componentes listados no `xatyy/Eden4/CREDITS.md`.
- ps4-switch-emu — atualmente referencia para tecnicas de teste e diagnostico, sem declarar uso de codigo ainda.

## Regras antes de publicar PKG
1. Gerar lista final de bibliotecas realmente usadas e manter arquivos originais de licenca/autoria no pacote (diretorio `licenses/`).
2. Preservar avisos GPL e licencas adicionais. Disponibilizar codigo-fonte correspondente, patches e instrucoes de construcao de distribuicoes GPL.
3. Conferir atribuicoes de imagens, icones, sons e fontes independentes do codigo.
4. Exibir link de codigo-fonte/release e avisos de que o projeto nao e afiliado a Nintendo/Sony/Eden.
5. Fazer um teste com DualShock 4 no PS4: Configuracoes > Sobre > Creditos e licencas; confirmar rolagem, acesso a licencas e botao voltar.
6. Nao afirmar que a tela esta funcional so porque o manifesto textual foi criado.

## Status
R07: especificacao e texto base registrados; a interface nao foi integrada e nenhum PKG final foi compilado/testado.

Referencias:
- https://github.com/MrKitsune9/Orbis-EDEN/blob/main/NOTICE.md
- https://github.com/xatyy/Eden4/blob/main/CREDITS.md
- https://github.com/xatyy/Eden4/blob/main/LICENSE
