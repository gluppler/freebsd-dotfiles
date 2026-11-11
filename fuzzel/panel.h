/* ISC: Copyright (c) 2026 Nostromo contributors. Provided without warranty. */
#ifndef NOSTROMO_MENU_PANEL_H
#define NOSTROMO_MENU_PANEL_H
#include <math.h>
#include <stdlib.h>
#include <pixman.h>

struct nostromo_panel_size { int width, height, rows; };
/* All inputs are buffer pixels. Keep full rows and paginate inside the output. */
static inline struct nostromo_panel_size
nostromo_panel_dimensions(int text_width, int padding, int fixed_height,
    int row_height, int rows, int available_width, int available_height, double scale)
{
    int limit = (int)fmax(1, fmin(720 * scale, available_width));
    int minimum = (int)fmin(240 * scale, limit);
    int fitted_rows = (int)fmax(0, (available_height - fixed_height) / fmax(1, row_height));
    struct nostromo_panel_size result = {
        .width = (int)fmin(limit, fmax(minimum, text_width + 2 * padding)),
        .rows = rows < fitted_rows ? rows : fitted_rows,
    };
    result.height = (int)fmax(1, fmin(available_height, fixed_height + result.rows * row_height));
    return result;
}

/* Paint only when the menu's background buffer is invalidated. Text remains in
 * fuzzel's padded content area; the attached left rail has no decorative label. */
static void
nostromo_panel(pixman_image_t *image, const pixman_color_t *background,
    const pixman_color_t *border, int width, int height, int stroke,
    float scale, int padding)
{
    const pixman_color_t clear = {0};
    pixman_rectangle16_t rect = {0, 0, width, height};
    pixman_image_fill_rectangles(PIXMAN_OP_SRC, image, &clear, 1, &rect);
    int rail = (int)fmin(fmax(4, round(12 * scale)), padding * .65);
    int cut = (int)fmin(round(12 * scale), fmin(width, height) / 4.);
    int depth = (int)fmin(fmax(1, round(rail * .3)), height * .15);
    int cap = (int)round(height * .10);
    for (int y = 0; y < height; y++) {
        int end = y < height / 2 ? y : height - 1 - y;
        int left = end <= cap ? 0 : end < cap + depth ? end - cap : depth;
        int right = width - (y >= height - cut ? y - (height - cut) + 1 : 0);
        if (right <= left) continue;
        rect = (pixman_rectangle16_t){left, y, right - left, 1};
        pixman_image_fill_rectangles(PIXMAN_OP_SRC, image, border, 1, &rect);
        if (y < stroke || y >= height - stroke) continue;
        /* A diagonal needs sqrt(2) times the horizontal stroke inset. */
        int inset = y >= height - cut ? (int)ceil(stroke * sqrt(2)) : stroke;
        int inner = right - inset;
        if (inner > rail) {
            rect = (pixman_rectangle16_t){rail, y, inner - rail, 1};
            pixman_image_fill_rectangles(PIXMAN_OP_SRC, image, background, 1, &rect);
        }
    }
}
#endif
