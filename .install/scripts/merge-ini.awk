# First input contains only owned section/key pairs; second is existing INI.
# Keep other sections/keys and comments. Append the owned pairs in each section.
NR==FNR {
    if($0 ~ /^[[:space:]]*[#;]/ || $0 ~ /^[[:space:]]*$/)next
    if($0 ~ /^\[[^]]+\]$/){section=substr($0,2,length($0)-2);next}
    at=index($0,"=");key=substr($0,1,at-1)
    if(!at || section=="" || key !~ /^[A-Za-z][A-Za-z0-9]*$/ || (section SUBSEP key) in owned){bad=1;next}
    owned[section SUBSEP key]=$0
    if(!(section in sections)){sections[section]=1;order[++count]=section}
    keys[section]=keys[section] key " "
    next
}
function emit(s, n, j, a) {
    if(!(s in sections) || s in emitted)return
    n=split(keys[s],a," ");for(j=1;j<=n;j++)if(a[j]!="")print owned[s SUBSEP a[j]]
    emitted[s]=1
}
FNR==1 {section=""}
/^[[:space:]]*\[[^]]+\][[:space:]]*$/ {
    section=$0;sub(/^[[:space:]]*\[/,"",section);sub(/\][[:space:]]*$/,"",section)
    print;emit(section);next
}
{
    line=$0;sub(/^[[:space:]]*/,"",line);key=line;sub(/[[:space:]=].*$/,"",key)
    if((section SUBSEP key) in owned && line ~ /^[A-Za-z][A-Za-z0-9]*[[:space:]]*=/)next
    print
}
END {
    if(bad)exit 1
    for(i=1;i<=count;i++) {
        section=order[i];if(section in emitted)continue
        print "[" section "]";emit(section)
    }
}
