# wpa_cli scan_results escapes nonprintable SSID bytes with \xHH.
# Convert one displayed SSID to configuration hex without interpreting shell escapes.
BEGIN {for(i=1;i<256;i++) ordinal[sprintf("%c",i)]=i}
{
    out=""
    for(i=1;i<=length($0);i++) {
        c=substr($0,i,1)
        if(c=="\\") {
            c=substr($0,++i,1)
            if(c=="x") {
                h=substr($0,i+1,2)
                if(h !~ /^[0-9a-fA-F][0-9a-fA-F]$/) exit 2
                out=out tolower(h); i+=2; continue
            }
            if(c=="n") {out=out "0a";continue}
            if(c=="r") {out=out "0d";continue}
            if(c=="t") {out=out "09";continue}
            if(c=="e") {out=out "1b";continue}
            if(c!="\\" && c!="\"") exit 2
        }
        if(!(c in ordinal)) exit 2
        out=out sprintf("%02x",ordinal[c])
    }
    if(length(out)<2 || length(out)>64) exit 2
    print out
}
END {if(NR!=1) exit 2}
