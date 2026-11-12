/* A small clock for vis and a scrollable Fastfetch view. No background service. */
#include <errno.h>
#include <limits.h>
#include <locale.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/select.h>
#include <termios.h>
#include <unistd.h>
#include <wchar.h>

#define MAX_LINES 4096
#define MAX_BYTES (2 * 1024 * 1024)
#define FRAMES 4
static volatile sig_atomic_t stopped;
static struct termios saved;
static int terminal_changed;
static sigset_t wait_mask;

static void stop(int sig) { (void)sig; stopped = 1; }
static void resize(int sig) { (void)sig; }
static int wait_input(int milliseconds) {
    fd_set input;
    FD_ZERO(&input); FD_SET(STDIN_FILENO, &input);
    struct timespec timeout = {milliseconds/1000, (milliseconds%1000)*1000000L};
    /* Unblock signals atomically with sleeping: a stop between draws cannot be lost. */
    return pselect(STDIN_FILENO+1, &input, NULL, NULL,
                   milliseconds < 0 ? NULL : &timeout, &wait_mask);
}
static void restore(void) {
    if (terminal_changed) {
        fputs("\033[0m\033[?25h\033[?1049l", stdout);
        fflush(stdout);
        tcsetattr(STDIN_FILENO, TCSANOW, &saved);
        terminal_changed = 0;
    }
}

static int animated(void) {
    const char *mode = getenv("NOSTROMO_EFFECTS");
    char path[PATH_MAX], value[32];
    if (!mode) {
        const char *state = getenv("XDG_STATE_HOME"), *home = getenv("HOME");
        int n;
        if (state && *state) n = snprintf(path, sizeof path, "%s/nostromo/crt-mode", state);
        else if (home) n = snprintf(path, sizeof path, "%s/.local/state/nostromo/crt-mode", home);
        else return 1;
        if (n < 0 || (size_t)n >= sizeof path) return 0;
        FILE *file = fopen(path, "r");
        if (file) {
            if (fgets(value, sizeof value, file)) {
                value[strcspn(value, "\r\n")] = 0;
                mode = value;
            }
            fclose(file);
        }
    }
    return !mode || !strcmp(mode, "animated");
}

static char *load(const char *path) {
    FILE *file = fopen(path, "rb");
    if (!file) { perror(path); return NULL; }
    char *data = malloc(MAX_BYTES + 1);
    if (!data) { fclose(file); return NULL; }
    size_t n = fread(data, 1, MAX_BYTES, file);
    int bad = ferror(file) || fgetc(file) != EOF;
    fclose(file);
    if (bad || memchr(data, 0, n)) { free(data); return NULL; }
    data[n] = 0;
    return data;
}

/* Print a glyph at *column unless it is scrolled off the left; 0 once the row is full. */
static int put(const char *bytes, size_t n, int width, int *column, int skip, int columns) {
    int end = *column + width;
    if (end - skip > columns) return 0;
    if (*column >= skip) fwrite(bytes, 1, n, stdout);
    else for (int at = skip; at < end; at++) putchar(' '); /* A wide glyph cut by the scroll. */
    *column = end;
    return 1;
}

/* Clip by display columns, including wide glyphs. Fastfetch aligns values with
   ESC [ n G even in pipe mode: pad to that column. Drop every other control. */
static void line(const char *text, int skip, int columns) {
    mbstate_t state = {0};
    int column = 0;
    size_t left = strlen(text);
    while (left) {
        size_t n = 1;
        if (*text == '\033') {
            int target = -1;
            if (left > 1 && text[1] == '[') {
                int value = 0;
                for (n = 2; n < left && text[n] >= 0x30 && text[n] <= 0x3f; n++)
                    if (text[n] >= '0' && text[n] <= '9' && value < 4096) value = value*10 + text[n]-'0';
                while (n < left && text[n] >= 0x20 && text[n] <= 0x2f) n++;
                if (n < left) { if (text[n] == 'G') target = (value ? value : 1) - 1; n++; }
            } else if (left > 1 && text[1] == ']') {
                /* OSC, such as a clipboard write, through BEL or ST. */
                n = 2;
                while (n < left && text[n] != '\a' && !(text[n] == '\033' && n+1 < left && text[n+1] == '\\')) n++;
                if (n < left) n += text[n] == '\a' ? 1 : 2;
            } else if (left > 1) n = 2;
            while (column < target) if (!put(" ", 1, 1, &column, skip, columns)) return;
        } else if (*text == '\t') {
            do if (!put(" ", 1, 1, &column, skip, columns)) return; while (column % 8);
        } else {
            wchar_t wc;
            const char *glyph = text;
            size_t bytes = n = mbrtowc(&wc, text, left, &state);
            int width = 1;
            if (n == (size_t)-1 || n == (size_t)-2 || n == 0) {
                n = bytes = 1; glyph = "?"; memset(&state, 0, sizeof state);
            } else if ((width = wcwidth(wc)) < 0) { width = 1; bytes = 1; glyph = " "; }
            if (!put(glyph, bytes, width, &column, skip, columns)) return;
        }
        text += n; left -= n;
    }
}

static int split(char *data, char **lines, int capacity) {
    int count = 0;
    char *at = data;
    while (*at) {
        if (count == capacity) return -1;
        lines[count++] = at;
        char *end = strchr(at, '\n');
        if (!end) break;
        *end = 0; at = end + 1;
    }
    return count;
}

static int report(const char *report_path, const char *art_path) {
    if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO)) return 2;
    char *text = load(report_path), *art = load(art_path);
    if (!text || !art) { free(text); free(art); return 1; }
    char *lines[MAX_LINES], *frames[FRAMES][32];
    int count = split(text, lines, MAX_LINES), heights[FRAMES];
    char *part = art;
    for (int i = 0; i < FRAMES; i++) {
        char *end = strchr(part, '\f');
        if (end) *end = 0;
        heights[i] = split(part, frames[i], 32);
        if (heights[i] < 1 || (i < FRAMES-1 && !end)) { count = -1; break; }
        if (end) part = end + 1;
    }
    if (count < 1 || tcgetattr(STDIN_FILENO, &saved) < 0) {
        free(text); free(art); return 1;
    }
    struct termios input = saved;
    input.c_lflag &= (tcflag_t)~(ICANON | ECHO);
    input.c_iflag &= (tcflag_t)~(IXON | ICRNL);
    input.c_cc[VMIN] = 0; input.c_cc[VTIME] = 0;
    if (tcsetattr(STDIN_FILENO, TCSANOW, &input) < 0) { free(text); free(art); return 1; }
    terminal_changed = 1;
    fputs("\033[?1049h\033[?25l", stdout);
    int first = 0, horizontal = 0;
    unsigned tick = 0;
    while (!stopped) {
        struct winsize size = {0};
        ioctl(STDOUT_FILENO, TIOCGWINSZ, &size);
        int width = size.ws_col ? size.ws_col : 80;
        int height = size.ws_row ? size.ws_row : 24;
        if (width > 512) width = 512;
        if (height > 256) height = 256;
        int moving = animated(), frame = moving ? (int)(tick % FRAMES) : 0;
        int side = width >= 96 && height >= heights[frame]+2;
        int top = !side && height >= heights[frame]+8 && width >= 32 ? heights[frame]+1 : 0;
        int rows = height-top-1;
        if (rows < 1) rows = 1;
        int last = count > rows ? count-rows : 0;
        if (first > last) first = last;
        fputs("\033[H", stdout);
        for (int y = 0; y < height-1; y++) {
            fputs("\033[2K", stdout);
            if (side) {
                if (y < heights[frame]) line(frames[frame][y], 0, 29);
                printf("\033[%dG", 34);
            } else if (top && y < heights[frame]) {
                printf("\033[%dG", (width-28)/2+1);
                line(frames[frame][y], 0, 28);
            }
            int row = first+y-top;
            if (y >= top && row < count) line(lines[row], horizontal, width-(side ? 34 : 1));
            fputs("\r\n", stdout);
        }
        char footer[128];
        snprintf(footer, sizeof footer, " j/k scroll  h/l columns  g/G ends  q close  | %d/%d ", first+1, count);
        fputs("\033[2K\033[7m", stdout); line(footer, 0, width-1); fputs("\033[0m", stdout);
        fflush(stdout);
        int ready = wait_input(moving ? 500 : -1);
        if (ready < 0) { if (errno == EINTR) continue; break; }
        if (!ready) { tick++; continue; }
        char key;
        if (read(STDIN_FILENO, &key, 1) != 1) break;
        if (key == 'q' || key == '\033' || key == '\r' || key == '\n') break;
        if (key == 'j' || key == 14) { if (first < last) first++; }
        if (key == 'k' || key == 16) { if (first > 0) first--; }
        if (key == ' ' || key == 6) first = first > last-rows ? last : first+rows;
        if (key == 'b' || key == 2) first = first < rows ? 0 : first-rows;
        if (key == 'g') first = 0;
        if (key == 'G') first = last;
        if (key == 'h') horizontal = horizontal < 8 ? 0 : horizontal-8;
        if (key == 'l' && horizontal < MAX_BYTES-8) horizontal += 8;
    }
    restore(); free(text); free(art);
    return 0;
}

int main(int argc, char **argv) {
    setlocale(LC_CTYPE, "");
    struct sigaction action = {0};
    action.sa_handler = stop; sigemptyset(&action.sa_mask);
    sigaction(SIGINT, &action, NULL); sigaction(SIGTERM, &action, NULL);
    sigaction(SIGHUP, &action, NULL); sigaction(SIGQUIT, &action, NULL);
    sigaction(SIGTSTP, &action, NULL);
    action.sa_handler = resize; sigaction(SIGWINCH, &action, NULL);
    sigset_t blocked;
    sigemptyset(&blocked);
    const int signals[] = {SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGTSTP, SIGWINCH};
    for (size_t i = 0; i < sizeof signals / sizeof signals[0]; i++) sigaddset(&blocked, signals[i]);
    if (sigprocmask(SIG_BLOCK, &blocked, &wait_mask) < 0) return 1;
    atexit(restore);
    if (argc == 2 && !strcmp(argv[1], "--ticks")) {
        unsigned tick = 0;
        while (!stopped) {
            int moving = animated();
            printf("%u\n", moving ? tick % FRAMES : 0); fflush(stdout);
            if (!moving) break;
            int ready = wait_input(500);
            if (ready > 0 || (ready < 0 && errno != EINTR)) break;
            tick++;
        }
        return 0;
    }
    if (argc == 5 && !strcmp(argv[1], "--report") && !strcmp(argv[3], "--art"))
        return report(argv[2], argv[4]);
    fputs("Usage: nostromo-terminal-idle --ticks | --report FILE --art FILE\n", stderr);
    return 2;
}
