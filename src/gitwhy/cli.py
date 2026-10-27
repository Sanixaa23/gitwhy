"""gitwhy komut satiri arayuzu.

    gitwhy                           son basarisiz git komutunu acikla
    gitwhy explain --stderr DOSYA    verilen hata ciktisini acikla (- = stdin)
    gitwhy capture -- git push       komutu kosar, basarisizsa kaydeder
    gitwhy doctor                    depo sagligi
    gitwhy shell-init [bash|zsh]     sarmalayici shell kodunu yazdirir

Hicbir alt komut depoyu degistirmez. `capture` kullanicinin verdigi komutu
oldugu gibi kosar; kendiliginden komut uretmez.
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

from . import __version__, capture, context, explain, rules

SARMALAYICI = {
    "bash": """# gitwhy sarmalayicisi - ~/.bashrc'ye ekle
git() {
  command git "$@"
  local kod=$?
  if [ $kod -ne 0 ]; then
    command gitwhy capture-exit "$kod" "git $*" >/dev/null 2>&1
    command gitwhy
  fi
  return $kod
}
""",
    "zsh": """# gitwhy sarmalayicisi - ~/.zshrc'ye ekle
git() {
  command git "$@"
  local kod=$?
  if [ $kod -ne 0 ]; then
    command gitwhy capture-exit "$kod" "git $*" >/dev/null 2>&1
    command gitwhy
  fi
  return $kod
}
""",
}


def _cikti(metin: str) -> None:
    """Windows konsolunda cp1254 hatasi vermeden yazdirir."""
    try:
        sys.stdout.write(metin + "\n")
    except UnicodeEncodeError:
        kodlama = sys.stdout.encoding or "utf-8"
        sys.stdout.write(metin.encode(kodlama, "replace").decode(kodlama) + "\n")


def _acikla(depo: str, hata_metni: str) -> int:
    ctx = context.topla(depo)
    senaryo = rules.esle(ctx, hata_metni)
    _cikti(explain.anlat(senaryo, ctx))
    return 0 if senaryo else 1


def komut_son_hata(arg) -> int:
    kayit = capture.oku()
    if kayit is None:
        _cikti(
            "Kayitli bir hata yok. Deponun su anki durumuna bakiliyor.\n"
            "Belirli bir hatayi aciklamak icin:  gitwhy explain --stderr -\n"
        )
    return _acikla(arg.depo, capture.hata_metni(kayit))


def komut_explain(arg) -> int:
    if arg.stderr == "-":
        metin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace").read()
    else:
        with open(arg.stderr, encoding="utf-8", errors="replace") as f:
            metin = f.read()
    return _acikla(arg.depo, metin)


def komut_capture(arg) -> int:
    """Verilen komutu kosar; basarisiz olursa kaydeder ve aciklar."""
    if not arg.komut:
        _cikti("Kullanim: gitwhy capture -- git push")
        return 2
    p = subprocess.run(arg.komut, capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    sys.stdout.write(out)
    sys.stderr.write(err)
    if p.returncode == 0:
        return 0
    capture.yaz(" ".join(arg.komut), p.returncode, out, err, arg.depo)
    _cikti("")
    _acikla(arg.depo, err + "\n" + out)
    return p.returncode


def komut_capture_exit(arg) -> int:
    """Shell sarmalayicisi icin: cikti zaten ekranda, sadece exit kodunu kaydet."""
    capture.yaz(arg.komut_metni, arg.kod, "", "", arg.depo)
    return 0


def komut_doctor(arg) -> int:
    ctx = context.topla(arg.depo)
    if not ctx.gecerli_depo:
        _cikti("Burasi bir git deposu degil: %s" % ctx.depo)
        return 1
    satir = ["# gitwhy doctor — %s" % ctx.depo, ""]
    satir.append("branch            : %s" % (ctx.branch or "(detached)"))
    satir.append("upstream          : %s" % (ctx.upstream or "yok"))
    satir.append("ileri / geri      : +%d / -%d" % (ctx.ileri, ctx.geri))
    satir.append("remote            : %s" % (", ".join(ctx.remoteler) or "yok"))
    satir.append("surmekte islem    : %s" % (", ".join(ctx.surmekte) or "yok"))
    satir.append("cakisan dosya     : %d" % len(ctx.cakisan))
    satir.append("user.email        : %s" % (ctx.user_email or "TANIMLI DEGIL"))
    gitignore = os.path.exists(os.path.join(ctx.depo, ".gitignore"))
    satir.append(".gitignore        : %s" % ("var" if gitignore else "YOK"))
    riskli = [y for y in ctx.sahnelenen if _riskli_yol(y)]
    satir.append("sahnelenmis sir   : %s" % (", ".join(riskli) or "yok"))
    _cikti("\n".join(satir))
    return 0


_RISKLI = (".env", "id_rsa", "credentials.json", ".pem", ".p12", ".keystore")


def _riskli_yol(yol: str) -> bool:
    ad = yol.replace("\\", "/").split("/")[-1].lower()
    return any(ad == r or ad.endswith(r) for r in _RISKLI)


def komut_shell_init(arg) -> int:
    kod = SARMALAYICI.get(arg.kabuk)
    if kod is None:
        _cikti("Desteklenen kabuklar: bash, zsh. PowerShell kapsam disi.")
        return 2
    sys.stdout.write(kod)
    return 0


def main(argv=None) -> int:
    ayristirici = argparse.ArgumentParser(
        prog="gitwhy",
        description="Git hatalarini deponun durumunu okuyarak aciklar.",
    )
    ayristirici.add_argument("--version", action="version", version="gitwhy " + __version__)
    ayristirici.add_argument("--depo", default=".", help="incelenecek depo (varsayilan: .)")
    alt = ayristirici.add_subparsers(dest="alt_komut")

    p = alt.add_parser("explain", help="verilen hata ciktisini acikla")
    p.add_argument("--stderr", required=True, help="hata ciktisi dosyasi, - = stdin")
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_explain)

    p = alt.add_parser("capture", help="komutu kosar, basarisizsa aciklar")
    p.add_argument("komut", nargs=argparse.REMAINDER)
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_capture)

    p = alt.add_parser("capture-exit", help="shell sarmalayicisi icin kayit")
    p.add_argument("kod", type=int)
    p.add_argument("komut_metni")
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_capture_exit)

    p = alt.add_parser("doctor", help="depo sagligi")
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_doctor)

    p = alt.add_parser("shell-init", help="sarmalayici shell kodunu yazdirir")
    p.add_argument("kabuk", nargs="?", default="bash", choices=["bash", "zsh"])
    p.set_defaults(islev=komut_shell_init)

    arg = ayristirici.parse_args(argv)
    islev = getattr(arg, "islev", komut_son_hata)
    return islev(arg)


if __name__ == "__main__":
    sys.exit(main())
