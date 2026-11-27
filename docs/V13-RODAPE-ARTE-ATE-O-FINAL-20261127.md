# HIMURA SWITCH — rodapé integrado à arte do menu (27/11/2026)

**Pedido confirmado pelo usuário após o vídeo `20261127_145526.mp4`:** a imagem/paisagem da tela principal deve continuar visualmente até o limite INFERIOR da TV, inclusive por trás da faixa que hoje é preta e contém nomes, informações e comandos. NÃO se trata de apenas aumentar o tamanho das capas dos jogos. Retirar a sensação de uma lista/faixa preta separada do restante da arte.

## Critérios de aceitação visuais
1. Expandir/continuar a paisagem original de fundo até y=1080 (1920×1080), preservando proporções e a composição (sem simplesmente esticar ou deformar a arte).
2. Remover a faixa opaca preta da área inferior. Controles reais, dicas de botão, nomes de jogos e informações ficam por cima da imagem. Para legibilidade, permitir somente sombra localizada ou gradiente translúcido suave, nunca painel preto opaco.
3. Manter a capa dos jogos com foco/neon real e eliminar blocos pretos que cobrem a paisagem atrás das capas.
4. Tirar o selo R13 impresso/reescrito no cabeçalho; manter o nome HIMURA SWITCH.
5. Preservar a navegação funcional por DualShock, a barra superior com ações reais, textos PT-BR e o posicionamento legível dos indicadores inferiores.
6. Verificar captura real da TV (1080p) em HOME, biblioteca com e sem jogos, seleção de capa, página de configurações e retorno ao menu. Sem elementos falsos embutidos no bitmap.

## Evidência de código conhecida
Em `ci/patch-r11-approved-menu.py`, a rotina `R11_SKIN_SOURCE` desenha a arte e em seguida aplica diversas máscaras escuras. A máscara inferior atual é:

```cpp
c.FillRect(0, 970, Canvas::Width, 110, {0x070911}, 1.0f);
c.HLine(0, Canvas::Width, 969, 3, {0xd52236}, 0.85f);
```

Remover SOMENTE essas linhas não basta se o próprio bitmap `branding/himura-r11-menu.png` já tiver rodapé escuro ou botões impressos. A solução correta exige **arte limpa recomposta até a borda inferior**, seguida de patch do launcher para não pintar máscara opaca sobre a arte. Rever também as máscaras quadradas sobre exemplos de capas e o selo `c.Text("R13",...)`; substituir os exemplos fictícios no bitmap, não apagar cegamente máscaras que os ocultam.

## Regra de entrega
**Este documento é especificação, não correção implementada.** Não promover a PKG sem screenshot verificável do resultado, testes de controle e validação do menu no PS4 Pro. Não alterar o New Eden 04.89 nem remover jogos, saves, keys, updates ou firmware.
