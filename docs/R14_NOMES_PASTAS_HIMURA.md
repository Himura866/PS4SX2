# HIMURA SWITCH PS4 R14 — nomenclatura e isolamento de diretórios

## Identidade visível da versão HIMURA
A R14 usa um frontend próprio com título de aplicativo `HIMURA SWITCH PS4`, `TITLE_ID=HIMU00014` e versão `01.14`. Esses valores são substituídos no script `ci/r14-adapt-orbis.py` dentro do checkout fixado do Orbis Eden; a R13 não é modificada.

| Elemento | Orbis Eden antes da adaptação | HIMURA SWITCH R14 |
| --- | --- | --- |
| Título no menu do PS4 | NX on Orbis | HIMURA SWITCH PS4 |
| TITLE_ID | EDPS00001 | HIMU00014 |
| Diretório próprio da interface | `/data/edenps4` | `/data/himura-switch-r14` |
| ROMs | `/data/edenps4/roms` | `/data/himura-switch-r14/roms` |
| Updates/DLCs | `/data/edenps4/updates` | `/data/himura-switch-r14/updates` |
| Chaves extraídas legalmente pelo usuário | `/data/edenps4/keys` | `/data/himura-switch-r14/keys` |
| Firmware próprio do usuário | `/data/edenps4/firmware` | `/data/himura-switch-r14/firmware` |
| Configurações | `/data/edenps4/settings.txt` | `/data/himura-switch-r14/settings.txt` |
| Logs da interface | `/data/edenps4/boot.log` | `/data/himura-switch-r14/boot.log` |

**Atenção:** a simples alteração de `Ps4::DataDir` não comprova que TODAS as pastas do núcleo Eden (cache, NAND, config, logs internos) foram migradas. O núcleo usa funções `Common::FS::GetEdenPath` e pode construir diretórios próprios. Mapear e testar esses caminhos antes de substituí-los; não fazer alteração global cega de nomes de símbolos, bibliotecas, paths de build `deps/eden`, `build-eden`, binário `eden-ps4` e dependências do CMake.

## Compatibilidade e migração
- Não apagar, renomear ou mover dados da R13/Orbis Eden automaticamente. Instalação paralela e importação explícita, com consentimento do usuário e backup dos saves.
- Se futuramente for desejado ocultar `eden` de caminhos exibidos ao usuário, fazer mapeamento na camada de frontend e cópias seguras para caminhos editáveis, mantendo nomes ABI/namespace internos quando necessários.
- Não remover copyright, LICENSE, NOTICE e créditos dos autores originais. Rebranding visual é compatível com o devido cumprimento da GPL; não alegar autoria exclusiva do motor original.
- Validar nome de pastas e arquivos efetivamente criados em Fat, Slim e Pro, junto aos logs e aos jogos, antes de declarar suporte público.
- Não incluir firmware, jogos ou chaves de terceiros no PKG.
