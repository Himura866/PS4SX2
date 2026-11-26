# Checkpoint — exportação app0 verificada (26/11/2026)

**Arquivos reais recebidos**: `EDNP00001-app0.zip`, originado da pasta montada `/mnt/sandbox/pfsmnt/EDNP00001-app0` do PS4.

- ZIP SHA-256: `66e8154774498ce8bd30bde0af36b561cebd6f24ef2d3cdaabafa7ff9a16ec02`
- ZIP integrity: aprovado; 13 arquivos (fora diretórios).
- `eboot.bin`: 78.376.440 bytes, ELF x86-64 FreeBSD PS4 tipo 0xfe10, SHA-256 `5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381`, texto `New Eden 04.89` confirmado.
- `symbols.zst`: 781.039 bytes, Zstandard; mapa descompactado com 79.764 linhas de símbolos.
- `sce_sys` no ZIP traz somente `keystone`. `param.sfo` e `icon0.png` disponíveis no PKG original já recebido, não no ZIP.
- `eboot.bin` inclui a implementação do menu, temas e configurações; não existem fontes `*.cpp` exportadas.
- Temas identificados no executável: Basic Black, Basic White e Retro. O changelog de 04.89 descreve uma correção de crash ao mover rapidamente pela linha do menu Retro.
- Informações de configurações presentes no binário: renderizador, resolução, shader cache, shaders assíncronos, precisão GPU, frame pacing, velocidade do jogo, CPU, threads/cores e overlay FPS.
- `/data/eden-ps4` ocorre em dezenas de caminhos internos, inclusive cache e logs. Nunca renomear em massa sem migração verificada.

## Rotinas compiladas identificadas via símbolos

| Função | Endereço virtual |
|---|---|
| `Ui::HomeMenu::DrawHome` | 0x000956b0 |
| `Ui::HomeMenu::DrawRetroHome` | 0x000943c0 |
| `Ui::HomeMenu::DrawSettings` | 0x00096a90 |
| `Ui::HomeMenu::SettingItems` | 0x0008ecd0 |
| `Ui::HomeMenu::Navigate` | 0x0008d7d0 |
| `Ui::HomeMenu::DrawAllSoftware` | 0x000961a0 |
| `Ui::HomeMenu::DrawBottomBar` | 0x0009cc00 |
| `Ui::HomeMenu::DrawHeader` | 0x0009cdc0 |

**Importante**: estes símbolos permitem orientação da análise, não fornecem o código-fonte original. Não fazer alterações aleatórias no executável nem alegar que a simples tradução de strings implementa novos botões, carrossel ou configurações. Um PKG com assinaturas, metadados e módulos corretos precisa ser gerado e testado após qualquer alteração.

## Backups privados no Google Drive

- Original PKG 04.89: https://drive.google.com/file/d/1IFr36pcJnrBEQuu3-pO19V_-m4PHVi9D/view
- ZIP real exportado do PS4: https://drive.google.com/file/d/1rbzv62oiYAoJizHkHr_i4r7-MC6McWcO/view
- Relatório + auditor: https://drive.google.com/file/d/1WsoJa9o-eT9LlZcWfbDGoRQnSVYb-Jus/view

**Estado**: análise estática concluída, versão do executável reconhecida, nenhum byte alterado, nenhum PKG recompilado, nenhuma compatibilidade de jogos medida nesta sessão.

## Próxima etapa

Localizar as rotinas/recursos editáveis da UI original e obter o método de reempacotamento FSELF/PKG sem quebrar a inicialização. Separar mudanças de ícone/metadados de modificações em `eboot.bin`. Criar checkpoints com logs; validar no PS4 Pro antes de integrar alterações de menu, controles e temas.
