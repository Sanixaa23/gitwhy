"""Salt-okunur git sorgulari ve tek bir Baglam nesnesi.

Bu modul depoyu ASLA degistirmez. Buraya eklenecek her yeni komut salt-okunur
olmak zorunda: bir komut depoyu degistirebiliyorsa bu dosyaya girmez.

Birincil sinyal depo durumu, hata metni degil. Git surumleri hata mesajlarini
degistirir ama --porcelain=v2 cikti bicimi sabit tutulur.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# .git dizininde varligi yarim kalmis bir islemi gosteren yollar.
SURMEKTE_YOLLARI = (
    "MERGE_HEAD",
    "rebase-merge",
    "rebase-apply",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
)


def _git(depo: str, *arg: str) -> Tuple[str, str, int]:
    """git'i `depo` icinde kosar; (stdout, stderr, exit) dondurur.

    LC_ALL=C: kendi sorgularimizin cikti dili sabit kalsin. Kullanicinin
    gordugu hata mesaji bundan etkilenmez, onu biz uretmiyoruz.
    GIT_OPTIONAL_LOCKS=0: index'e yazma ihtimalini de kaldirir.
    """
    ortam = dict(
        os.environ,
        LC_ALL="C",
        GIT_OPTIONAL_LOCKS="0",
        GIT_PAGER="cat",
        GIT_TERMINAL_PROMPT="0",
    )
    try:
        p = subprocess.run(
            ["git", "-C", depo, *arg],
            capture_output=True,
            env=ortam,
        )
    except FileNotFoundError:
        return "", "git bulunamadi", 127
    return (
        p.stdout.decode("utf-8", "replace"),
        p.stderr.decode("utf-8", "replace"),
        p.returncode,
    )


@dataclass
class Baglam:
    """Deponun o anki durumu. rules.esle() sadece bunu ve hata metnini gorur."""

    depo: str
    gecerli_depo: bool = False
    git_dir: Optional[str] = None
    branch: Optional[str] = None          # detached ise None
    detached: bool = False
    oid: Optional[str] = None             # HEAD commit'i; commit yoksa None
    upstream: Optional[str] = None
    ileri: int = 0                        # upstream'den kac commit ileride
    geri: int = 0                         # upstream'den kac commit geride
    cakisan: List[str] = field(default_factory=list)
    surmekte: List[str] = field(default_factory=list)
    sahnelenen: List[str] = field(default_factory=list)
    remote_var: bool = False
    remoteler: List[str] = field(default_factory=list)
    son_mesaj: Optional[str] = None
    user_email: Optional[str] = None

    @property
    def oid_kisa(self) -> str:
        return (self.oid or "")[:7] or "yok"


def _durum_ayristir(ctx: Baglam, cikti: str) -> None:
    """`git status --porcelain=v2 --branch` ciktisini Baglam'a isler.

    Ilgilendigimiz satirlar:
      # branch.oid <sha> | (initial)
      # branch.head <ad> | (detached)
      # branch.upstream <ad>          -- upstream yoksa bu satir hic yok
      # branch.ab +<ileri> -<geri>    -- upstream yoksa bu satir hic yok
      u <xy> ... <yol>                -- cakisan dosya
    """
    for satir in cikti.splitlines():
        if satir.startswith("# branch.oid "):
            deger = satir[len("# branch.oid "):].strip()
            ctx.oid = None if deger == "(initial)" else deger
        elif satir.startswith("# branch.head "):
            deger = satir[len("# branch.head "):].strip()
            if deger == "(detached)":
                ctx.detached = True
                ctx.branch = None
            else:
                ctx.branch = deger
        elif satir.startswith("# branch.upstream "):
            ctx.upstream = satir[len("# branch.upstream "):].strip()
        elif satir.startswith("# branch.ab "):
            for parca in satir[len("# branch.ab "):].split():
                if parca.startswith("+"):
                    ctx.ileri = int(parca[1:] or 0)
                elif parca.startswith("-"):
                    ctx.geri = int(parca[1:] or 0)
        elif satir.startswith("u "):
            # u <xy> <sub> <m1> <m2> <m3> <mW> <h1> <h2> <h3> <yol>
            alan = satir.split(" ", 10)
            if len(alan) == 11:
                ctx.cakisan.append(alan[10])


def topla(depo: str = ".") -> Baglam:
    """Deponun durumunu tek bir Baglam nesnesinde toplar. Salt-okunur."""
    ctx = Baglam(depo=os.path.abspath(depo))

    git_dir, _, rc = _git(depo, "rev-parse", "--absolute-git-dir")
    if rc != 0:
        return ctx  # git deposu degil; gecerli_depo False kalir
    ctx.gecerli_depo = True
    ctx.git_dir = git_dir.strip()

    durum, _, _ = _git(depo, "status", "--porcelain=v2", "--branch")
    _durum_ayristir(ctx, durum)

    ctx.surmekte = [
        ad for ad in SURMEKTE_YOLLARI
        if os.path.exists(os.path.join(ctx.git_dir, ad))
    ]

    sahne, _, _ = _git(depo, "diff", "--cached", "--name-only")
    ctx.sahnelenen = [y for y in sahne.splitlines() if y.strip()]

    remote, _, _ = _git(depo, "remote")
    ctx.remoteler = [r for r in remote.splitlines() if r.strip()]
    ctx.remote_var = bool(ctx.remoteler)

    mesaj, _, rc = _git(depo, "log", "-1", "--format=%s")
    ctx.son_mesaj = mesaj.strip() if rc == 0 else None

    eposta, _, rc = _git(depo, "config", "user.email")
    ctx.user_email = eposta.strip() if rc == 0 and eposta.strip() else None

    return ctx


def ignore_ediliyor(depo: str, yol: str) -> bool:
    """`git check-ignore` ile tek bir yolun ignore edilip edilmedigini sorar.

    exit 0 = ignore ediliyor, 1 = edilmiyor. Senaryo 9 ve 10 bunu kullanacak.
    """
    _, _, rc = _git(depo, "check-ignore", "-q", yol)
    return rc == 0


def reflog(depo: str, adet: int = 30) -> List[str]:
    """Senaryo 12 icin reflog satirlari. Salt-okunur."""
    cikti, _, rc = _git(depo, "reflog", "--date=relative", f"-{adet}")
    if rc != 0:
        return []
    return [s for s in cikti.splitlines() if s.strip()]
