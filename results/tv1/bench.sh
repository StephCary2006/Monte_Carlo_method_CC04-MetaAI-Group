if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <runs> <program> [args...]" >&2
    exit 1
fi
runs=$1
prog=$2
shift 2

case "$runs" in
    ''|*[!0-9]*|0) echo "Error: <runs> must be a positive integer." >&2; exit 1 ;;
esac
if [ ! -x "$prog" ]; then
    echo "Error: $prog not found or not executable (run make first)." >&2
    exit 1
fi

i=1
while [ "$i" -le "$runs" ]; do
    t=$("$prog" "$@" | awk '/^Time:/ {print $2}')
    if [ -z "$t" ]; then
        echo "Error: no Time line in the output of $prog." >&2
        exit 1
    fi
    echo "run $i: $t s"
    echo "$t"
    i=$((i + 1))
done | awk '
    /^run / { print; next }
    { n++; s += $1; ss += $1 * $1; if (n == 1 || $1 < mn) mn = $1; if (n == 1 || $1 > mx) mx = $1 }
    END {
        mean = s / n
        sd = (n > 1) ? sqrt((ss - n * mean * mean) / (n - 1)) : 0
        printf "---\nruns=%d  mean=%.6f s  stddev=%.6f s  min=%.6f s  max=%.6f s\n", n, mean, sd, mn, mx
    }'