# Teste real New Eden 04.89 — Mario Kart 8 Deluxe — falha de cabeçalho NCA

Data: 2026-11-26. Evidência: vídeo de 11,398 segundos enviado pelo usuário `20261126_173312.mp4`, filmando diretamente a tela do PS4 Pro. Backup na pasta privada do Drive: https://drive.google.com/file/d/1mxeySHO3EQ7WlU86Eeok2Cko8OPVFVZo/view

## Observação direta

- Tela inicial do New Eden 04.89 mostra capa do Mario Kart 8 Deluxe selecionada, junto de outros jogos.
- Janela modal: **"Mario Kart 8 Deluxe ROMSNS.COM didn't start. The file looks damaged: copy or dump it again (The NCA file has a bad header.)"**
- O modal continua exibido durante os ~11 segundos do vídeo; não há gameplay do Mario Kart.
- O indicador inferior esquerdo mostra `FPS: 0.00` enquanto o erro está aberto; NÃO é leitura de FPS em gameplay.
- O nome do título inclui `ROMSNS.COM`, mas isso não é prova de proveniência nem integridade.

## Diagnóstico

A mensagem indica que **o leitor NCA rejeitou um cabeçalho**. Não atribuir inicialmente a queda de FPS, Vulkan ou desempenho do PS4. Causas que precisam ser separadas por testes: pacote incompleto/corrompido, erro na transferência do NSP/XCI, arquivo alterado/reempacotado, conteúdo NCA inválido, ou eventual incompatibilidade/bug do parser/chaves. A mensagem de cabeçalho ruim NÃO prova qual causa.

Primeiras ações SEGURAS antes de modificar a V15:
1. Conferir extensão original do arquivo (NSP ou XCI), tamanho completo e hash do arquivo no celular/pendrive e no PS4 após cópia.
2. Comparar com dump legítimo da mesma cópia de jogo, íntegro; transferir novamente em binário, sem conversão ZIP/renomeação, caso hashes difiram.
3. Confirmar que a base executa Silksong como o usuário relatou; NÃO alterar CPU/JIT, Vulkan e parser do núcleo apenas para ignorar erro de cabeçalho NCA.
4. Se arquivo íntegro e chaves/firmware obtidos do próprio Switch estiverem corretos e o erro persistir, coletar boot.log, mensagens do carregador NCA, versão do jogo e resultado ao remover updates/DLC para comparação.

**Importante:** o vídeo não mostra um teste completo de NSP e XCI, nem jogo rodando ou FPS real. A compatibilidade da V15 continua não verificada. O objetivo V15 é preservar funcionamento existente e aumentar compatibilidade só após diagnóstico comprovado.
