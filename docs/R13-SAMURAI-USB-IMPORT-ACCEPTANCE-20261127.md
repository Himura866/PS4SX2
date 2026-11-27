# HIMURA SWITCH R13 — critérios para correção da arte e acesso ao USB

Data: 2026-11-27. Documento de requisitos e diagnóstico; **não significa implementação nem PKG validado**.

## Base preservada
- HIMU00011 / app version 01.13 (R13). Proteger icon/arte R13 aprovados.
- New Eden 04.89 é referência de comportamento/compatibilidade, não um substituto de eboot ou prova de que um port tem as mesmas funções.
- V15 experimental apresentou erro de dados corrompidos no PS4 e não deve substituir a base de teste.

## Achado real no código
Em `ci/patch-r11-approved-menu.py`, a arte do samurai de `/app0/skin/himura-r11-menu.png` é desenhada com `c.DrawImage`. A função injeta `c.FillRect(0, 970, Canvas::Width, 110, {0x070911}, 1.0f)` para **cobrir**, não remover, as legendas falsas no rodapé. Existem outras máscaras escuras sobre capas de demonstração embutidas na imagem. Logo, não declarar essa correção visual como concluída.

## Correção visual exigida
1. Partir da **mesma arte aprovada** do samurai com lua vermelha/montanhas. Remover diretamente os seis botões/legendas fictícios *impressos na imagem*, reconstruindo somente o cenário sob eles; evitar faixa opaca preta e arte substituta.
2. Limpar as capas de demonstração, setas e indicador falsos gravados no bitmap antes de usá-lo como fundo. A UI C++ renderiza os elementos reais por cima.
3. Manter a barra de comandos **real**, navegável, na parte superior; manter versão atual, PT-BR, neon e ampliação da capa ativa.
4. Remover o fundo preto **ao redor da capa selecionada**, sem eliminar a capa nem sua ampliação. Verificar possíveis artefatos/letras brancas residuais na base da capa central.
5. Testes devem falhar se o rodapé limpo não estiver presente nos assets de build; não desativar máscaras antes de existir a imagem correta.

## Importar do HD externo — Games > Add Folder
1. Não abrir teclado para digitar caminhos. Exibir seletor navegável com controle PS4: **Armazenamento interno**, **USB 1**, pastas e opção **Selecionar esta pasta**.
2. A seleção inicia varredura recursiva e categorização de jogos/updates, keys e firmware **que o aplicativo e permissões permitem ler**; exibir encontrados, ignorados e erros.
3. Preferir indexar jogos no HD por caminho sem copiar arquivos grandes; para importar keys/firmware, prévia e confirmação, sem sobrescrever existentes. Suportar re-scan, USB desconectado, permissões e falta de espaço.
4. Não confundir localizar arquivos com conseguir executar jogos. Validar carregamento, compatibilidade e desempenho separadamente, com logs.

## Evidência para marcar concluído
- Diff do código da UI, arte original limpa revisável, prévia comparativa e testes de integridade do asset.
- Simulações de navegação em armazenamento interno e USB 1, importação não destrutiva, remoção de USB e diretórios inválidos.
- PKG gerado pelo CI e testado **no PS4 Pro**, incluindo boot, seleção de USB e carregamento real de jogos. Compilação verde sozinha não satisfaz.
