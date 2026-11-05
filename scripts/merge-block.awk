# Replace exactly one named managed block; reject malformed/nested markers.
# awk -v name=... -v replacement=/private/file -f merge-block.awk original
BEGIN {begin="# BEGIN NOSTROMO " name; end="# END NOSTROMO " name}
$0 == begin {if (inside || seen++) bad=1; inside=1; next}
$0 == end {if (!inside) bad=1; inside=0; next}
!inside {print}
END {
    if (inside || bad) exit 2
    print begin
    while ((getline line < replacement) > 0) print line
    close(replacement)
    print end
}
