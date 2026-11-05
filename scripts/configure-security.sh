#!/bin/sh
# Sourced by configure-system.sh, sharing its rollback journal and trusted paths.
# shellcheck disable=SC2154
# Command-line options override the files below. Preserve custom startup flags
# and stop before edits instead of reporting a policy the daemon will not use.
for variable in sshd_flags pf_flags; do
    flags=$(sysrc -n "$variable" 2>/dev/null || :)
    [ -z "$flags" ] || {
        printf 'Review custom %s before installation: startup overrides are preserved.\n' "$variable" >&2
        exit 1
    }
done
security_ssh() {
    ssh_kind=$1 ssh_policy=$2
    ssh_main=/etc/ssh/${ssh_kind}_config
    printf '%s\n' "$ssh_main" >"$work/ssh-queue"
    : >"$work/ssh-seen"
    ssh_index=1
    # OpenSSH includes are configuration, never shell code. Accept normal quoted
    # or unquoted /etc/ssh globs; reject complex paths before changing files.
    while ssh_file=$(sed -n "${ssh_index}p" "$work/ssh-queue") && [ -n "$ssh_file" ]; do
        ssh_index=$((ssh_index + 1))
        grep -Fxq -e "$ssh_file" "$work/ssh-seen" && continue
        [ "$ssh_index" -le 128 ] || {
            echo 'Excessive SSH include graph.' >&2
            return 1
        }
        sf_safe "$ssh_file" && [ -f "$ssh_file" ] || return 1
        printf '%s\n' "$ssh_file" >>"$work/ssh-seen"
        awk 'tolower($1)=="include" {
            for(i=2;i<=NF;i++) {
                if($i ~ /^#/)break
                item=$i;gsub(/^"|"$/,"",item)
                if(item !~ /^[a-zA-Z0-9_./*?\[\]-]+$/ || item ~ /(^|\/)\.\.(\/|$)/)exit 1
                print item
            }
        }' "$ssh_file" >"$work/ssh-includes"
        while IFS= read -r pattern; do
            case $pattern in /etc/ssh/*) ;; /*)
                echo 'Review SSH includes outside /etc/ssh.' >&2
                return 1
                ;;
            *) pattern=/etc/ssh/$pattern ;; esac
            # Deliberate pathname expansion after restricting the pattern alphabet.
            # shellcheck disable=SC2086
            for included in $pattern; do
                [ -e "$included" ] || continue
                printf '%s\n' "$included" >>"$work/ssh-queue"
            done
        done <"$work/ssh-includes"
    done
    while IFS= read -r ssh_file; do
        strip=1
        [ "$ssh_file" != "$ssh_main" ] || strip=0
        awk -v strip_only="$strip" -f "$repo/scripts/merge-ssh.awk" "$ssh_policy" "$ssh_file" >"$work/ssh-candidate"
        ssh_mode=$(stat -f '%Lp' "$ssh_file")
        sf_put "$work/ssh-candidate" "$ssh_file" "$ssh_mode"
    done <"$work/ssh-seen"
}
sed "s/@ACCOUNT@/$account/g" "$repo/system/sshd_config" >"$work/sshd-policy"
security_ssh sshd "$work/sshd-policy"
security_ssh ssh "$repo/system/ssh_config"
# Existing keys are retained; ssh-keygen only creates missing system host keys.
ssh-keygen -A
sshd -t
sshd -T -C "user=$account,host=localhost,addr=127.0.0.1" >"$work/sshd-effective"
awk '
    $1=="port" {if($2!=2222)bad=1; ports++}
    $1=="passwordauthentication" && $2!="no" {bad=1}
    $1=="kbdinteractiveauthentication" && $2!="no" {bad=1}
    $1=="permitrootlogin" && $2!="no" {bad=1}
    $1=="authenticationmethods" && $2!="publickey" {bad=1}
    END {exit bad || ports!=1}
' "$work/sshd-effective"
ssh -G localhost >/dev/null
pf_file=$(sysrc -n pf_rules 2>/dev/null || printf '%s' /etc/pf.conf)
case $pf_file in /*) ;; *)
    echo 'PF configuration path must be absolute.' >&2
    exit 1
    ;;
esac
sf_safe "$pf_file"
if [ -f "$pf_file" ]; then original=$pf_file; else original=/dev/null; fi
if [ ! -e /usr/local/etc/nostromo/ssh-peers ]; then
    printf '# One agreed WireGuard peer IP/CIDR per line; empty denies incoming SSH.\n' >"$work/ssh-peers"
    sf_put "$work/ssh-peers" /usr/local/etc/nostromo/ssh-peers 600
fi
sf_put "$repo/system/pf.conf" /usr/local/etc/nostromo/pf.conf 644
awk -f "$repo/scripts/merge-pf.awk" "$original" >"$work/pf-candidate"
kldstat -q -m pf || kldload pf
# Parse exactly the selected native ruleset before activation. No rule flush here.
pfctl -nf "$work/pf-candidate"
sf_put "$work/pf-candidate" "$pf_file" 600
sysrc -f "$work/rc.conf" pf_enable=YES
