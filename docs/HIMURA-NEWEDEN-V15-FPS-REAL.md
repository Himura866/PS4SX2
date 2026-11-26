# HIMURA SWITCH PS4 V15 — contador de FPS real

**Requisito obrigatório confirmado em 26/11/2026.** O usuário quer monitorar o FPS real dos jogos na tela, especialmente Hollow Knight: Silksong, que relatou conseguir abrir no New Eden 04.89 original.

## Descoberta confirmada no binário 04.89

O executável `eboot.bin` exportado da instalação real tem SHA-256 `5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381` (78.376.440 bytes). Uma análise estática, **somente leitura**, confirmou:

- Texto de opção `FPS Counter` no offset `0x1f2758b`.
- Nome de configuração `show_fps_overlay` no offset `0x1e37b0e`.
- Marcador `fps=on` no offset `0x1e32b47`.
- Texto de configuração persistente `fps=%s` no offset `0x1ea30a9`.
- Log de velocidade `speed: the game {:.1f} fps` no offset `0x1ee4261`.
- Símbolo de API `Launcher::SetFpsOverlay(bool)` presente em `symbols.zst`.

**Conclusão:** a versão 04.89 já traz um contador/overlay de FPS e uma opção correspondente. O caminho de menor risco é **reaproveitar essa implementação**, evitando injetar outro contador no renderer ou motor de emulação.

## V15 — requisitos e testes

1. No menu Configurações, traduzir `FPS Counter` para **Mostrar FPS** ou **Contador de FPS** em português brasileiro.
2. Preservar o vínculo funcional entre o item do menu, `show_fps_overlay`, o acionamento `Launcher::SetFpsOverlay(bool)` e a persistência. Não bastam rótulos decorativos.
3. Exibir dados reais medidos do jogo; **nunca valores fixos ou estimativas arbitrárias**. Se disponível, distinguir FPS do jogo e porcentagem de velocidade de emulação. A posição do HUD precisa ser legível e não impedir o gameplay.
4. Permitir ligar/desligar sem crash e, se o binário original o fizer, manter a preferência entre reinicializações. Preferir a implementação já presente no 04.89.
5. Comparar gameplay **Silksong** com contador ligado/desligado; anotar FPS mínimo/típico/estabilidade, tempo de carregamento, áudio, retorno ao menu e temperatura do console quando observável.
6. Não modificar JIT/Vulkan/scheduler/execução dos jogos só para implementar ou mudar a aparência do FPS.
7. Este documento NÃO confirma FPS reais medidos ou o funcionamento visual do HUD em um PS4; a medição depende de testes no aparelho.

## Status

✅ Análise estática do recurso original e identificação do símbolo.
⏳ Tradução visual e testes de ativação/medição no PS4 pendentes.
⏳ Compilação de um PKG V15 com as demais melhorias ainda não concluída.

A base New Eden 04.89 é diferente de construções experimentais Orbis-EDEN em outras branches. O original e todos os checkpoints permanecem no Drive privado.
