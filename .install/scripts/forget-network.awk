# Remove every network block that wpa_supplicant reads as the network whose SSID is
# the hex in ssid, so a new profile replaces it; other lines pass through unchanged.
# LC_ALL=C awk -v ssid=hex [-v mode=find] -f forget-network.awk wpa_supplicant.conf
# mode=find prints nothing and succeeds only when such a block exists. Lines are read
# as src/utils/config.c reads them and names as common.c parses them: "text",
# P"escaped" or hex, while NULL clears one. A name wpa_supplicant rejects, or an
# unterminated block, exits 2.
BEGIN {
    if (ssid !~ /^([0-9a-f][0-9a-f])+$/ || length(ssid) > 64 || (mode != "" && mode != "find")) {
        bad = 1
        exit
    }
    for (i = 1; i < 256; i++) ordinal[sprintf("%c", i)] = i
    simple["\\"] = "5c"; simple["\""] = "22"; simple["n"] = "0a"
    simple["r"] = "0d"; simple["t"] = "09"; simple["e"] = "1b"
}
function hex(text,    out, i) {
    for (i = 1; i <= length(text); i++) out = out sprintf("%02x", ordinal[substr(text, i, 1)])
    return out
}
# printf_decode(): \x takes one or two hex digits and an octal escape up to three
# digits; any other escape drops only its backslash.
function unescape(text,    out, i, c, n) {
    for (i = 1; i <= length(text); i++) {
        c = substr(text, i, 1)
        if (c != "\\") {
            out = out hex(c)
            continue
        }
        c = substr(text, ++i, 1)
        if (c in simple) {
            out = out simple[c]
        } else if (c == "x" && substr(text, i + 1, 2) ~ /^[0-9a-fA-F][0-9a-fA-F]$/) {
            out = out tolower(substr(text, i + 1, 2))
            i += 2
        } else if (c == "x" && substr(text, i + 1, 1) ~ /^[0-9a-fA-F]$/) {
            out = out "0" tolower(substr(text, ++i, 1))
        } else if (c ~ /^[0-7]$/) {
            n = c
            if (substr(text, i + 1, 1) ~ /^[0-7]$/) n = n * 8 + substr(text, ++i, 1)
            if (substr(text, i + 1, 1) ~ /^[0-7]$/) n = n * 8 + substr(text, ++i, 1)
            out = out sprintf("%02x", n % 256)
        } else if (c != "x") {
            i--
        }
    }
    return out
}
# The name a value sets, in hex: "" for none, "-" for a value wpa_supplicant rejects.
function ssid_of(value,    text) {
    if (value == "NULL") return ""
    if (value ~ /^".*"$/ && length(value) > 1) text = hex(substr(value, 2, length(value) - 2))
    else if (value ~ /^P".*"$/ && length(value) > 2) text = unescape(substr(value, 3, length(value) - 3))
    else if (value ~ /^([0-9A-Fa-f][0-9A-Fa-f])*$/) text = tolower(value)
    else return "-"
    return length(text) > 64 ? "-" : text
}
# A line as wpa_config_get_line() returns it: no leading blanks, no # comment outside
# double quotes, no trailing white space; "" for a comment or empty line.
function effective(line,    end, start, quote, closing) {
    sub(/^[ \t\r]+/, "", line)
    if (line ~ /^#/) return ""
    end = index(line, "#")
    start = 1
    while (end) {
        quote = index(substr(line, start), "\"")
        if (!quote || start + quote - 1 > end) break
        closing = index(substr(line, start + quote), "\"")
        if (!closing) break
        start += quote + closing
        if (start > end) {
            end = index(substr(line, start), "#")
            if (end) end += start - 1
        }
    }
    if (end) line = substr(line, 1, end - 1)
    sub(/[ \t\r]+$/, "", line)
    return line
}
{
    line = effective($0)
    if (!inside) {
        if (line == "network={") {
            inside = 1
            block = $0 "\n"
            current = ""
        } else if (mode != "find") {
            print
        }
        next
    }
    block = block $0 "\n"
    if (line == "}") {
        inside = 0
        if (current == ssid) found++
        else if (mode != "find") printf "%s", block
    } else if (substr(line, 1, 5) == "ssid=") {
        # A later ssid line replaces an earlier one, but each must parse.
        current = ssid_of(substr(line, 6))
        if (current == "-") {
            bad = 1
            exit
        }
    }
}
END {
    if (bad || inside) exit 2
    if (mode == "find") exit !found
}
