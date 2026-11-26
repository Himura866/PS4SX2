# New Eden 04.89 — diagnóstico do indicador de firmware vermelho (confirmado no eboot.bin)

Usuário relatou 26/11/2026 que na aba `Games & Keys` o item Firmware permanece vermelho, enquanto os outros estão verdes, apesar de copiar os arquivos para uma pasta. Relatou tela `Select a Mii` sem itens em vídeo. Este é **um problema da versão New Eden 04.89 ORIGINAL**, anterior a qualquer modificação da V15.

## Evidência real do executável original
`eboot.bin` de 78.376.440 bytes, SHA-256 `5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381`, contém:

- `Launcher::FindKeysAndFirmware(...)`
- `Launcher::FindFirmware(...)`
- `Launcher::FindFirmwareZip(...)`
- `Launcher::InstallFirmwareZip(...)`
- Mensagem: `Copy keys and firmware to the PS4`.
- Ajuda detalhada embutida: `prod.keys` e `title.keys` no topo do pendrive ou na pasta `switch`, e firmware como pasta de `.nca` ou ZIP; **Quadrado em Games and Keys copia para o PS4**. Também lê arquivos de `/data/eden-ps4/import` (para ser preenchido com gerenciador de arquivos).
- Erros textuais: `No firmware found (a folder of .nca files).`, `the zip can't be read`, `it's a ZIP64 zip it can't read`, `it's compressed in a way this can't read`, `the zip is damaged`, `the zip ends early`.
- Progresso: `Copying the firmware: {} of {} files...`.
- Mensagem de falha de cópia mantendo firmware anterior: `(the firmware that was there is left as it was)`.

## Procedimento de teste sem modificar a instalação

1. Usar arquivos de firmware obtidos legalmente do próprio console Switch do usuário. Nunca solicitar envio de `prod.keys`, `title.keys` ou firmware proprietário ao chat.
2. Por pendrive conectado ao PS4, usar o firmware em **ZIP normal (não ZIP64)** ou uma pasta com os arquivos `.nca` (não zip dentro de outro zip).
3. Em `Games & Keys`, pressionar **Quadrado** e aguardar progresso de cópia. Também pode colocar os arquivos na pasta `/data/eden-ps4/import/` e importar com Quadrado.
4. Se não reconhecer, observar mensagem exata: arquivo não encontrado, ZIP64, compressão, ZIP danificado, falha de armazenamento, keys/versão incompatíveis.
5. Verificar indicador após importação; se continuar vermelho, obter foto do erro em vez de renomear, apagar ou mover os dados a esmo.
6. A tela `Select a Mii` vazia **pode** estar relacionada à ausência de dados do firmware, mas ainda não há evidência causal. Não prometer correção do Mii antes de confirmar firmware instalado.

**Importante:** o indicador vermelho não prova que o ZIP está incorreto nem que todos os jogos deixarão de iniciar. O usuário relatou conseguir iniciar Hollow Knight: Silksong anteriormente.

**Status:** função de instalação verificada ESTATICAMENTE no executável; ainda não testada importação no console, nem modificação da V15.
