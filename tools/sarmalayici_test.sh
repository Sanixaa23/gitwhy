#!/usr/bin/env bash
# `gitwhy shell-init` sarmalayicisinin uctan uca testi.
#
# Birim testler sarmalayiciyi kapsamiyor: orada shell yok. Burada
# sarmalayici gercekten kuruluyor, gercek git komutlari basarisiz
# ediliyor ve gitwhy'in dogru senaryoyu buldugu kontrol ediliyor.
#
# Kullanim:
#   bash tools/sarmalayici_test.sh            # varsayilan mod
#   GITWHY_TEE=1 bash tools/sarmalayici_test.sh
#
# gitwhy'in PATH'te olmasi gerekiyor (`pip install -e .`).
set -u

export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@e
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@e
export GIT_CONFIG_GLOBAL="${TMPDIR:-/tmp}/gitwhy_ayar_yok"
export GIT_CONFIG_SYSTEM="$GIT_CONFIG_GLOBAL"
export LC_ALL=C GIT_TERMINAL_PROMPT=0

GECEN=0; KALAN=0
KOK="$(mktemp -d)"
trap 'rm -rf "$KOK"' EXIT
export GITWHY_CACHE="$KOK/onbellek"

if ! command -v gitwhy >/dev/null 2>&1; then
  echo "ATLANDI: gitwhy PATH'te yok. Once: pip install -e ."
  exit 0
fi

# Ayni betik hem bash hem zsh ile kosuluyor; sarmalayici o kabuga gore
# uretiliyor. zsh'te fark tek: boru hattinin cikis kodu ${pipestatus[1]}.
if [ -n "${ZSH_VERSION:-}" ]; then
  KABUK=zsh
else
  KABUK=bash
fi
eval "$(gitwhy shell-init "$KABUK")"
# `type -t` bash'e ozgu; `typeset -f` ikisinde de calisiyor.
if ! typeset -f git >/dev/null 2>&1; then
  echo "BASARISIZ: $KABUK icin sarmalayici kurulamadi"
  exit 1
fi

# Bir adim: ad, beklenen senaryo basligi, depo kurulumu, basarisiz komut.
dene() {
  local ad="$1" beklenen="$2"
  local d="$KOK/$ad"; mkdir -p "$d"; cd "$d" || return 1
  "kur_$ad" >/dev/null 2>&1
  local cikti; cikti="$("calistir_$ad" 2>&1)"
  local kod=$?
  if printf '%s' "$cikti" | grep -qF "$beklenen"; then
    echo "GECTI   $ad  (exit=$kod)  -> $beklenen"
    GECEN=$((GECEN + 1))
  else
    echo "KALDI   $ad  (exit=$kod)  '$beklenen' bulunamadi"
    printf '%s\n' "$cikti" | sed -n '1,12p' | sed 's/^/        | /'
    KALAN=$((KALAN + 1))
  fi
}

temel_depo() {
  command git init -q -b main
  printf 'a\n' > a.txt
  command git add a.txt
  command git commit -qm ilk
}

uzak_ekle() {
  command git init --bare -q -b main ../uzak.git
  command git remote add origin ../uzak.git
}

# 05 - remote hic yok
kur_05() { temel_depo; }
calistir_05() { git push; }

# 06 - remote var, upstream yok
kur_06() { temel_depo; uzak_ekle; }
calistir_06() { git push; }

# 07 - push reddedildi
kur_07() {
  temel_depo; uzak_ekle
  command git push -q -u origin main
  command git clone -q ../uzak.git ../klon07
  ( cd ../klon07 && printf 'baskasi\n' > a.txt \
    && command git commit -qam baskasi && command git push -q )
  printf 'ben\n' > a.txt
  command git commit -qam benim
}
calistir_07() { git push; }

# 03 - rebase ortasi (durumdan bulunur, metin gerekmez)
kur_03() {
  temel_depo
  printf 'a\nmain\n' > a.txt
  command git commit -qam main-tarafi
  command git checkout -q -b ozellik HEAD~1
  printf 'a\nozellik\n' > a.txt
  command git commit -qam ozellik-tarafi
}
calistir_03() { git rebase main; }

# 11 - kaydedilmemis degisiklik checkout'u engelliyor
kur_11() {
  temel_depo
  command git checkout -q -b ozellik
  printf 'a\nozellik\n' > a.txt
  command git commit -qam ozellik-tarafi
  command git checkout -q main
  printf 'a\nkaydedilmemis\n' > a.txt
}
calistir_11() { git checkout ozellik; }

# basarili komut: sarmalayici hic karismamali
kur_ok() { temel_depo; }
calistir_ok() { git status --short --branch; }

echo "=== kabuk=$KABUK  GITWHY_TEE=${GITWHY_TEE:-0} ==="
dene 05 "git remote add origin"
dene 06 "push.autoSetupRemote"
if [ "${GITWHY_TEE:-0}" = "1" ]; then
  dene 07 "git pull --rebase"
else
  echo "ATLANDI 07  (metin gerekiyor; GITWHY_TEE=1 ile kosulur)"
fi
dene 03 "git rebase --continue"
dene 11 "git stash push"
dene ok "## main"

echo
echo "gecen $GECEN, kalan $KALAN"
[ "$KALAN" -eq 0 ]
