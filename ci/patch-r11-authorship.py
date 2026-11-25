#!/usr/bin/env python3
"""R11 attribution without removing upstream credits or overriding copyleft licenses.

The credited alias 'POD DO HIMURA' is not an assertion that a legal
registration occurred. Verify personal nickname/legal ownership separately.
"""
from pathlib import Path
import sys

def once(text, old, new, label):
    n=text.count(old)
    if n != 1: raise RuntimeError(f"R11 credits {label}: anchor count {n}")
    return text.replace(old,new,1)

ATTRIBUTION = """HIMURA SWITCH PS4 — R11 SAMURAI EDITION
Identidade da distribuicao: HIMURA.
Apelido exibido nos creditos: POD DO HIMURA.

Personalizacao original do projeto HIMURA: proposta visual, layout do menu,
identidade grafica samurai, carrossel, destaques neon e integracoes especificas
desenvolvidas nesta ramificacao. Reconhecimento de autoria/titularidade das
contribuicoes originais conforme a lei e os fatos; esta nota NAO e um
certificado de registro, cessao, ou declaracao de propriedade sobre os codigos
de terceiros.

BASES DE TERCEIROS
Eden4/xatyy; Eden; yuzu; DolphinPS4/ShiroKlein; Mesa/RADV;
OpenOrbis; LLVM; Nunito; SwitchLauncher (referencia de layout);
e demais bibliotecas: veja CREDITS.md e os textos completos em licenses/.
Preservar atribuicoes, avisos de autoria e licencas aplicaveis.

O emulador inclui codigo GPL-3.0-or-later, GPL-2.0-or-later e componentes
sob outras licencas. O titular do HIMURA nao pode impedir a copia,
modificacao e redistribuicao dos componentes GPL nos termos da GPL.
Nomes, marca e materiais graficos originais podem envolver direitos distintos,
sem alterar as permissoes do codigo GPL.

AUTENTICIDADE DA DISTRIBUICAO
Verifique o SHA-256 do PKG com o manifesto gerado pela compilacao e publicado
no canal oficial. Um hash sozinho identifica os bytes, nao comprova
a identidade do distribuidor, caso terceiros substituam ambos os arquivos.
"""

def main(root):
    launcher = root/"eden/src/yuzu_ps4/ui_launcher.cpp"
    source = launcher.read_text(encoding="utf8")
    source=once(source,
        "constexpr CreditEntry HimuraCredits[] = {",
        'constexpr CreditEntry HimuraCredits[] = {\n'
        '    {"POD DO HIMURA", "Identidade e personalizacoes originais desta R11; nao inclui autoria do Eden4/Eden", '
        '"Contribuicoes originais, direitos reservados conforme aplicavel", "HIMURA SWITCH PS4 R11"},',
        "credit entry")
    source=once(source,
        'HIMURA SWITCH PS4 (R07 experimental)',
        'HIMURA SWITCH PS4 (R11 Samurai Edition)',
        "version label")
    source=once(source,
        '"Codigo aberto e agradecimentos - base experimental Eden4"',
        '"POD DO HIMURA - personalizacao R11; creditos da base Eden4"',
        "credits summary")
    launcher.write_text(source, encoding="utf8")

    build=root/"eden/ps4/build.sh"
    sh=build.read_text(encoding="utf8")
    sh=once(sh,
        'cp "$REPO/CREDITS.md" "$STAGE/licenses/CREDITS.md"',
        'cp "$REPO/CREDITS.md" "$STAGE/licenses/CREDITS.md"\n'
        'cp "$REPO/branding/HIMURA-ATTRIBUTION.txt" "$STAGE/licenses/HIMURA-ATTRIBUTION.txt"',
        "included notice")
    build.write_text(sh,encoding="utf8")
    branding=root/"branding"
    branding.mkdir(parents=True,exist_ok=True)
    (branding/"HIMURA-ATTRIBUTION.txt").write_text(ATTRIBUTION,encoding="utf8")
    print("R11: credited POD DO HIMURA with original upstream credits and licenses")

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r11-authorship.py <Eden4 checkout>")
    main(Path(sys.argv[1]).resolve())
