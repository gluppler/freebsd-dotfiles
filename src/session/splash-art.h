/* Native splash drawing shared with deterministic previews. */
#include "space-dots.h"
static inline void nostromo_splash_art(cairo_t *cr,cairo_surface_t *logo,int width,int height,
    double t,int animated,int effects) {
    double size=fmin(280,fmin(width,height)*.26),x=(width-size)/2,y=(height-size)/2;
    double opacity=animated?fmin(1,fmax(0,(NOSTROMO_SPLASH_SECONDS-t)/.4)):1;
    int mode=effects?(animated?2:1):0;
    cairo_save(cr);
    cairo_set_operator(cr,CAIRO_OPERATOR_SOURCE);
    cairo_set_source_rgba(cr,0,0,0,opacity);cairo_paint(cr);
    cairo_set_operator(cr,CAIRO_OPERATOR_OVER);cairo_push_group(cr);
    nostromo_space_orb(cr,logo,x,y,size,t,mode);
    nostromo_space_texture(cr,width,height,t,mode);
    cairo_pop_group_to_source(cr);cairo_paint_with_alpha(cr,opacity);cairo_restore(cr);
}
