# HIMURA SWITCH PS4 — Contrato da interface do New Eden 04.89

**Requisito obrigatório e fixo confirmado pelo usuário em 26/11/2026.**

## Navegação do menu
- **Botões interativos de navegação no TOPO**, seguindo o estilo das versões HIMURA anteriores. A navegação é pelo DualShock 4, com foco, seleção e retorno reais; não basta desenhar controles estáticos na arte.
- O fundo interno usa a arte samurai de menu aprovada, sem a faixa inferior de botões fictícios; separar a arte dos elementos de interface programados.
- Carrossel/biblioteca de jogos deve manter seleção visível, boa leitura e evitar o painel preto cobrindo todo o fundo. Botões/topo não podem esconder títulos nem impedir a navegação.
- **Capa externa** `sce_sys/icon0.png` aparece somente no mosaico de aplicativos do PS4; ela **não** deve ser reutilizada como fundo do menu interno.
- Textos do menu, configurações, temas e créditos em português brasileiro; créditos da base e licença preservados.

## Segurança e integridade do binário
- A base alvo é o **New Eden 04.89** enviado pelo usuário, `EDNP00001`; não confundir com a árvore Orbis-EDEN de outra revisão.
- **ATENÇÃO:** os botões do topo e o carrossel **ainda não foram integrados ao executável** nesta etapa de documentação. O `eboot.bin` tem lógica de UI compilada; a aplicação exige modificação comprovadamente segura ou fontes correspondentes.
- Não editar as rotinas de boot de jogos, JIT, áudio, Vulkan, gerenciamento de memória ou saves para implementar a interface. Exigir verificação estrutural e teste PS4 antes de marcar funcional.
- Em qualquer teste: controlar hash da entrada, gerar saída separada, registrar alterações, preservar identificadores importantes e garantir capacidade de reversão.

## Critérios de aprovação antes de publicar PKG
1. Comandos ativos visivelmente no topo, acessíveis pelo controle; nenhuma barra de botões fictícios no fundo.
2. Capa externa não aparece dentro do menu.
3. Seleção de jogos, abertura, retorno, áudio e configurações sem regressões confirmadas no PS4 Pro.
4. Temas e opções de otimização com funções reais, créditos e textos em pt-BR.
5. Cada arte, binário, relatório e PKG comprovado guardado na pasta privada de checkpoints no Drive.
