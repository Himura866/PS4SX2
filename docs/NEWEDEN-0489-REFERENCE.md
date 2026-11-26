# New Eden 04.89 — base de referência (não confundir com fonte extraído)

O usuário forneceu o arquivo `NewEden-04.89.pkg`. A inspeção local dos seus metadados confirmou:

- Formato: PlayStation 4 PKG, assinatura hex `7f434e54`.
- Nome `param.sfo`: `New Eden`.
- Versão `APP_VER` / `VERSION`: `04.89`.
- `TITLE_ID`: `EDNP00001`.
- `CONTENT_ID`: `IV0000-EDNP00001_00-EDENPS4000000000`.
- Tamanho: 69.337.088 bytes (66,1 MiB).
- SHA-256: `06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd`.
- Cabeçalho contém 14 entradas, incluindo `param.sfo` e `icon0.png` recuperados sem modificar o PKG.
- `PUBTOOLINFO` contém `c_date=20261107` (metadado, não data de publicação validada).

**Não presumir que este binário corresponda à fonte Orbis-EDEN já presente no repositório.** O identificador do Orbis-EDEN usado anteriormente é `EDPS00001`, distinto do `EDNP00001` deste PKG. Até o momento, o sistema de arquivos do pacote, o ELF e o código-fonte **não foram extraídos**, e nenhum jogo foi testado no PS4 neste checkpoint. O diretório herdado nesta branch serve só como ponto de trabalho, **não é um rebuild comprovado do New Eden 04.89**.

## Desenvolvimento após obtenção do código correspondente

1. Conservar PKG original e confrontar integridade pelo hash acima.
2. Localizar o código-fonte exato ou extrair o PFS/ELF com ferramentas adequadas; identificar a proveniência e compatibilidade com PS4 Pro.
3. Preservar funcionamento: menu, biblioteca, controle, áudio, configurações e inicialização de jogos; criar teste de regressão.
4. Traduzir interface inteira para pt-BR sem textos misturados ou menu oculto.
5. Substituir capa/ícone e criar o menu samurai real, 1080p, com navegação e botões de controle funcionais; não usar uma imagem fixa como interface.
6. Implementar configurações de otimização suportadas de verdade, medir resultados e reverter cada ajuste inseguro.
7. Compilar unicamente pelo CircleCI, inspecionar PKG/ELF produzido e solicitar validação no PS4 Pro antes de marcar funcional.

Não alterar as branches R13/R14 atuais enquanto a equivalência da base não for comprovada. Não subir o arquivo PKG enviado ao repositório sem necessidade e autorização específica.
