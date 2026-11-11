# First file defines managed keys; strip only those keys from the second file.
# Include files receive no new block; main receives the policy before other rules.
NR==FNR {
    policy=policy $0 "\n"; line=$0; sub(/^[ \t]+/,"",line)
    split(line,w,/[ \t=]+/); key=tolower(w[1])
    if(key!="" && key !~ /^(#.*|host|match)$/) managed[key]=1
    if(key=="port") port=w[2]
    next
}
FNR==1 && !strip_only {printf "%s",policy;printed=1}
/^# BEGIN NOSTROMO SSH$/ {if(inside||seen++)bad=1;inside=1;next}
/^# END NOSTROMO SSH$/ {if(!inside)bad=1;inside=0;next}
{
    line=$0;sub(/^[ \t]+/,"",line);split(line,w,/[ \t=]+/);key=tolower(w[1])
    if(inside && line ~ /^Host[ \t]+\*[ \t]*$/)next
    if(key in managed)next
    if(key=="listenaddress" && port!="") {
        address=w[2]; quoted=address ~ /^".*"$/
        if(quoted) address=substr(address,2,length(address)-2)
        if(address ~ /^\[[^]]+\]:[0-9]+$/ || address ~ /^[^:]+:[0-9]+$/) {
            sub(/:[0-9]+$/,":" port,address)
            if(quoted) address="\"" address "\""
            at=index($0,w[2]);$0=substr($0,1,at-1) address substr($0,at+length(w[2]))
        }
    }
    print
}
END {if(!printed && !strip_only) printf "%s",policy; if(inside||bad)exit 1}
