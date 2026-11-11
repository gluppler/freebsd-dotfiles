# First input: explicit key=value replacements; second: rc/loader/sysctl file.
# Replace only listed simple assignments. Preserve every unrelated line.
NR==FNR {
    if ($0 ~ /^[[:space:]]*(#|$)/) next
    at=index($0,"="); key=substr($0,1,at-1)
    if (!at || key !~ /^[a-zA-Z0-9_.]+$/ || key in values) {bad=1;next}
    values[key]=$0; order[++count]=key; next
}
{
    line=$0; sub(/^[[:space:]]*/,"",line)
    key=line; sub(/[[:space:]=].*$/,"",key)
    if (key in values && line ~ /^[a-zA-Z0-9_.]+[[:space:]]*=/) {
        if (line ~ /\\[[:space:]]*$/) {bad=1;print "Refusing a multiline managed setting: " key > "/dev/stderr"}
        next
    }
    print
}
END {if (bad) exit 1; for(i=1;i<=count;i++) print values[order[i]]}
