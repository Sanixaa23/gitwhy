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
from typing import List, Optional, Set, Tuple

# .git dizininde varligi yarim kalmis bir islemi gosteren yollar.
SURMEKTE_YOLLARI = (
    "MERGE_HEAD",
    "rebase-merge",
    "rebase-apply",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
)


def _ortam() -> dict:
    """LC_ALL=C: kendi sorgularimizin cikti dili sabit kalsin. Kullanicinin
    gordugu hata mesaji bundan etkilenmez, onu biz uretmiyoruz.
    GIT_OPTIONAL_LOCKS=0: index'e yazma ihtimalini de kaldirir.
    """
    return dict(
        os.environ,
        LC_ALL="C",
        GIT_OPTIONAL_LOCKS="0",
        GIT_PAGER="cat",
        GIT_TERMINAL_PROMPT="0",
    )


def _git(depo: str, *arg: str) -> Tuple[str, str, int]:
    """git'i `depo` icinde kosar; (stdout, stderr, exit) dondurur."""
    try:
        p = subprocess.run(
            ["git", "-C", depo, *arg],
            capture_output=True,
            env=_ortam(),
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
    # Diskte degismis ama sahnelenmemis dosyalar. Senaryo 11 bunlari sayar.
    kaydedilmemis: List[str] = field(default_factory=list)
    # (sha, commit konusu, reflog'da bundan sonra gelen islem)
    kayip: List[Tuple[str, str, str]] = field(default_factory=list)
    remote_var: bool = False
    remoteler: List[str] = field(default_factory=list)
    # Sahnelenmis yollardan .gitignore kurallarina takilanlar. Dolu olmasi
    # "kural var ama dosya yine de sahnelenmis" demektir (git add -f, veya
    # kural dosya eklendikten sonra yazilmis).
    ignore_edilen: List[str] = field(default_factory=list)
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
      1/2 <xy> ... <yol>              -- degismis dosya; xy[1] != '.' ise
                                         degisiklik sahnelenmemis
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
        elif satir.startswith("1 ") or satir.startswith("2 "):
            # 1 <xy> <sub> <mH> <mI> <mW> <hH> <hI> <yol>
            alan = satir.split(" ", 8)
            if len(alan) == 9 and len(alan[1]) == 2 and alan[1][1] != ".":
                # 2 (kopyalanmis/tasinmis) satirinda yol "yeni\teski" bicimli
                ctx.kaydedilmemis.append(alan[8].split("\t")[0])


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
    # 200 yol siniri: dev bir ilk commit'te binlerce yol olabilir, tek
    # check-ignore cagrisini sisirmenin bir faydasi yok.
    ctx.ignore_edilen = ignore_edilenler(depo, ctx.sahnelenen[:200])

    remote, _, _ = _git(depo, "remote")
    ctx.remoteler = [r for r in remote.splitlines() if r.strip()]
    ctx.remote_var = bool(ctx.remoteler)

    mesaj, _, rc = _git(depo, "log", "-1", "--format=%s")
    ctx.son_mesaj = mesaj.strip() if rc == 0 else None

    eposta, _, rc = _git(depo, "config", "user.email")
    ctx.user_email = eposta.strip() if rc == 0 and eposta.strip() else None

    ctx.kayip = kayip_commitler(depo)

    return ctx


def ignore_ediliyor(depo: str, yol: str) -> bool:
    """`git check-ignore` ile tek bir yolun ignore edilip edilmedigini sorar.

    exit 0 = ignore ediliyor, 1 = edilmiyor.
    """
    _, _, rc = _git(depo, "check-ignore", "-q", "--no-index", yol)
    return rc == 0


def ignore_edilenler(depo: str, yollar: List[str]) -> List[str]:
    """Verilen yollardan .gitignore kurallarina takilanlari dondurur.

    --no-index SART: check-ignore varsayilan olarak index'e bakar ve
    index'te olan (yani sahnelenmis) bir yolu, kural eslesse bile "ignore
    edilmiyor" sayar. Senaryo 9 ve 10 tam olarak sahnelenmis yollari
    sorguluyor, o yuzden bu bayrak olmadan sonuc her zaman bos cikar.

    Tek cagri, --stdin ile. Salt-okunur.
    """
    yollar = [y for y in yollar if y.strip()]
    if not yollar:
        return []
    try:
        p = subprocess.run(
            ["git", "-C", depo, "check-ignore", "--no-index", "--stdin"],
            input="\n".join(yollar).encode("utf-8"),
            capture_output=True,
            env=_ortam(),
        )
    except FileNotFoundError:
        return []
    if p.returncode not in (0, 1):   # 128 = hata; sessizce bos don
        return []
    cikti = p.stdout.decode("utf-8", "replace")
    return [y for y in cikti.splitlines() if y.strip()]


def reflog(depo: str, adet: int = 30) -> List[str]:
    """Okunabilir reflog satirlari. Salt-okunur."""
    cikti, _, rc = _git(depo, "reflog", "--date=relative", "-%d" % adet)
    if rc != 0:
        return []
    return [s for s in cikti.splitlines() if s.strip()]


def erisilemezler(depo: str, shalar: List[str]) -> Set[str]:
    """Verilen commit'lerden hicbir ref'ten erisilemeyenleri dondurur.

    `rev-list --no-walk <shalar> --not --all`: --no-walk atalara inmez,
    `--not --all` ref'lerden erisilen her seyi disarida birakir. Geriye
    yalnizca hicbir branch/tag/HEAD'den ulasilamayan commit'ler kalir.
    Tek cagri, siniri yok. Salt-okunur.
    """
    if not shalar:
        return set()
    cikti, _, rc = _git(depo, "rev-list", "--no-walk", *(list(shalar) + ["--not", "--all"]))
    if rc != 0:
        return set()
    return {s.strip() for s in cikti.splitlines() if s.strip()}


def kayip_commitler(depo: str, adet: int = 10) -> List[Tuple[str, str, str]]:
    """Reflog'un son `adet` girdisinde olup hicbir ref'ten erisilemeyenler.

    Iki sinir bilerek konuldu:

    1. Yalnizca son 10 girdi. Reflog yuzlerce girdi tutuyor ve aylar once
       dusmus bir commit'i bugun "kaybettin" diye bildirmek gurultu olur.
       `gitwhy doctor` tam reflog'u gostermek icin var.
    2. Bir ustteki (daha yeni) islem `commit (amend)` ise atlanir: amend
       eski commit'i erisilemez birakir ama bu kasitli bir islemdir, kayip
       degil. Fixture ile dogrulandi (neg_amend).
    """
    cikti, _, rc = _git(depo, "reflog", "--format=%H%x09%gs%x09%s", "-%d" % adet)
    if rc != 0:
        return []
    girdiler: List[Tuple[str, str, str]] = []
    for satir in cikti.splitlines():
        alan = satir.split("\t")
        if len(alan) >= 3 and alan[0].strip():
            girdiler.append((alan[0].strip(), alan[1], alan[2]))

    adaylar: List[Tuple[str, str, str]] = []
    gorulen = set()
    for i, (sha, _gs, konu) in enumerate(girdiler):
        if i > 0 and girdiler[i - 1][1].startswith("commit (amend)"):
            continue
        if sha in gorulen:
            continue
        gorulen.add(sha)
        sonraki = girdiler[i - 1][1] if i > 0 else "(en son islem)"
        adaylar.append((sha, konu, sonraki))

    kayip_set = erisilemezler(depo, [a[0] for a in adaylar])
    return [a for a in adaylar if a[0] in kayip_set]
