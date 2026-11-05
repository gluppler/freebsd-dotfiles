# Input is the kernel-validated current rules string, not shell configuration.
# Replace the former root grant with ACPI-device group access. Keep other rules.
BEGIN {
    if (uid !~ /^[0-9]+$/ || uid + 0 == 0 || uid + 0 > 4294967294) exit 2
    if (gid !~ /^[0-9]+$/ || gid + 0 < 1000 || gid + 0 > 4294967294) exit 2
    old = "uid=" uid ">uid=0"
    wanted = "uid=" uid ">uid=.,gid=" gid ",!gid=."
}
{
    if (NR > 1) rules = rules " "
    rules = rules $0
}
END {
    if (wanted == "") exit 2
    count = split(rules, entries, ";")
    for (i = 1; i <= count; i++) {
        canonical = entries[i]
        gsub(/[[:space:]]/, "", canonical)
        if (canonical == old || canonical == wanted || canonical == "") continue
        kept = kept (kept == "" ? "" : ";") entries[i]
    }
    print kept (kept == "" ? "" : ";") wanted
}
