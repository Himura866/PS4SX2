# HIMURA SWITCH V15 — Navegação por pastas e importação pelo USB (pedido de 27/11/2026)

## Pedido do usuário (funcionalidade obrigatória, ainda NÃO implementada)

No menu **Jogos > Armazenamento / Storage** existem as origens **Interno / Internal** e **USB 1**. Hoje, ao acionar **Adicionar pasta / Add Folder**, abre uma entrada de texto exigindo digitar manualmente o caminho. O usuário quer **navegar visualmente nas pastas com o controle e selecionar exatamente a pasta** no HD/USB ou armazenamento interno, SEM digitar caminhos.

### Fluxo esperado no DualShock 4

1. Selecionar **Jogos > Armazenamento > Interno** ou **USB 1**. Mostrar estados de dispositivo detectado/ausente, espaço e erro de leitura sem inventar caminhos.
2. Pressionar **Adicionar pasta**. Abrir **navegador de diretórios real**, iniciando na raiz acessível do dispositivo escolhido; **não abrir teclado/campo de texto**. Mostrar lista de pastas, destaque da seleção e caminho atual.
3. **Direcional** move o foco; **X** entra em uma pasta; **O** volta à pasta anterior; ação **Selecionar esta pasta** confirma a pasta atual. Deixar claro o comando de confirmação na interface. Respeitar o mapeamento real do controle e o retorno ao menu sem travar.
4. Registrar o caminho escolhido de modo persistente e **atualizar a biblioteca** com jogos compatíveis presentes na pasta e em subpastas, evitando duplicados e varreduras travadas. Não criar capas fictícias. Dar indicadores de leitura e falhas por arquivo.
5. Mostrar arquivos reconhecidos em categorias separadas: **Jogos**, **Atualizações/DLC**, **Keys**, **Firmware**. Não tratar keys/firmware como jogos; não importar automaticamente todo ZIP/arquivo desconhecido.
6. **Keys**: detectar somente backups reconhecidos e próprios do usuário; **nunca substituir keys já funcionais sem confirmação**, opção de pular e manter as atuais. Não revelar nem incluir chaves em logs, artefatos ou screenshots.
7. **Firmware**: identificar arquivos/estrutura suportados pelo motor efetivo; informar versão, compatibilidade e ação explícita de instalar/atualizar. **Não sobrescrever firmware existente sem confirmação e backup**. Se não houver instalador funcional, exibir suporte indisponível em vez de declarar sucesso.
8. **Jogos com updates**: reconhecer jogo base e atualizações separadamente; só associar/instalar se formato, title ID e versão forem aceitos pelo motor. Não misturar conteúdo entre títulos.
9. Oferecer **Usar esta pasta** (indexar do USB sem copiar) e **Copiar para armazenamento interno** quando essa operação estiver de fato implementada. Cópia deve verificar espaço livre, integridade/hashes e duplicados, ter progresso e retomada segura; jamais excluir arquivos do HD por padrão.
10. Caso o USB seja desconectado, biblioteca deve mostrar itens indisponíveis sem perder os cadastros. Sem tela preta/crash; oferecer reconexão/revarredura.

## Regras de segurança e compatibilidade

- Não criar caminho fixo imaginário para **USB 1**: resolver dispositivo e ponto de montagem reais que o PS4/GoldHEN expõe na instalação do usuário. **USB 1** é um rótulo de UI, não necessariamente o caminho `/mnt/usb1`.
- Isolar o escopo de leitura à raiz autorizada; impedir travessia por `..`/links para fora da origem e tratar diretórios indisponíveis, permissões e erros.
- Indexação não deve apagar ou sobrescrever saves, chaves nem firmware que já funcionam, nem depender de desinstalar o New Eden.
- A V15 deve preservar capa externa R13, paisagem samurai interna, zoom da capa central sem fundo preto, botões reais no topo e interface pt-BR.
- O pacote experimental de 27/11/2026 falhou no boot do PS4 com aviso de dados corrompidos; **resolver boot antes de declarar este recurso funcional**.
- O projeto inclui scripts de build/teste e um executável New Eden 04.89 pré-compilado; **o código-fonte exato da UI desse executável NÃO está comprovadamente disponível**. Os patches Orbis-EDEN/R11 de outra base não devem ser aplicados cegamente ao executável 04.89.
- Nenhum scanner/importador/browse de diretórios foi implementado no aplicativo apenas por adicionar este documento.

## Testes de aceitação exigidos em hardware

- PS4 Pro sem USB: mensagem útil ao entrar em USB 1; voltar com O.
- PS4 Pro com HD/pendrive: abrir pastas e subpastas pelo DualShock, sem teclado. Confirmar pasta e verificar biblioteca.
- Pasta mista com jogos, updates, keys e firmware: reconhecer categorias, sem substituir keys/firmware sem autorização.
- Pasta vazia ou conteúdo ilegível: resultados seguros, sem falso positivo ou crash.
- Reiniciar emulador, remover/reconectar USB e reler a pasta; testar no modo indexação e modo cópia.
- Registrar logs sem segredos; só publicar PKG após instalar, abrir e validar no próprio console.
