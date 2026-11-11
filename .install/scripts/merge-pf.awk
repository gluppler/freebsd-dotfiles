# Own one block; preserve all other text. Outgoing default precedes user filters,
# so later administrator restrictions still take precedence.
function block() {
    print "# BEGIN NOSTROMO PF"
    print "pass out all keep state"
    print "anchor \"nostromo\" in on ! lo0"
    print "load anchor \"nostromo\" from \"/usr/local/etc/nostromo/pf.conf\""
    print "# END NOSTROMO PF"
    emitted=1
}
/^# BEGIN NOSTROMO PF$/ {if(inside||seen++)bad=1;inside=1;next}
/^# END NOSTROMO PF$/ {if(!inside)bad=1;inside=0;next}
inside {next}
{
    # Includes may hide an earlier quick pass. A skip on a real interface bypasses
    # the anchor entirely. Keep such configurations untouched for explicit review.
    if($0 ~ /^[ \t]*include[ \t]/)bad=1
    if($0 ~ /^[ \t]*set[ \t]+skip[ \t]+on[ \t]/ &&
       $0 !~ /^[ \t]*set[ \t]+skip[ \t]+on[ \t]+lo0[ \t]*(#.*)?$/)bad=1
    if($0 ~ /^[ \t]*(load[ \t]+)?anchor[ \t]+("nostromo"|nostromo)([ \t{]|$)/)bad=1
    if(!emitted && $0 ~ /^[ \t]*(pass|block|match|anchor|antispoof)[ \t]/)block()
    print
}
END {if(!emitted)block(); if(inside||bad)exit 1}
