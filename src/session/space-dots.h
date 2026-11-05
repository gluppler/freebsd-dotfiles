/*
Copyright 2023 Maxim Samoliuk

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/
/* Monochrome, bounded-cost adaptation of space_dots' CRT treatment.
 * Shared by the native splash and authenticated lock; no input geometry is moved. */
#ifndef NOSTROMO_SPACE_DOTS_H
#define NOSTROMO_SPACE_DOTS_H
#include <math.h>
#include <stdint.h>
#include <string.h>
#include <cairo.h>
#include <glib.h>
#define NOSTROMO_EFFECT_FPS 30
#define NOSTROMO_SPLASH_SECONDS 2.4
#define NOSTROMO_ENTER_SECONDS 1.2

static inline int nostromo_space_mode(void) {
    const char *mode=g_getenv("NOSTROMO_EFFECTS");
    char *saved=NULL;
    if(!mode) {
        char *path=g_build_filename(g_get_user_state_dir(),"nostromo","crt-mode",NULL);
        if(g_file_get_contents(path,&saved,NULL,NULL))mode=g_strstrip(saved);
        g_free(path);
    }
    int result=!mode || !strcmp(mode,"animated")?2:!strcmp(mode,"static")?1:0;
    g_free(saved);return result;
}

/* Solve the reference winIn cubic (.1, 1.1, .1, 1.1) in elapsed-time space. */
static inline double nostromo_space_enter(double seconds) {
    double x=fmin(1,fmax(0,seconds/NOSTROMO_ENTER_SECONDS)),lo=0,hi=1,u=0;
    if(x>=1)return 1;
    for(int i=0;i<16;i++) {
        u=(lo+hi)/2;
        double v=1-u,bx=3*v*v*u*.1+3*v*u*u*.1+u*u*u;
        if(bx<x)lo=u;else hi=u;
    }
    double v=1-u;
    return 3*v*v*u*1.1+3*v*u*u*1.1+u*u*u;
}

/* Decode once into a 1 MiB surface shared by all frames and outputs. */
static inline cairo_surface_t *nostromo_space_logo(const char *path) {
    cairo_surface_t *image=cairo_image_surface_create_from_png(path);
    if(cairo_surface_status(image)!=CAIRO_STATUS_SUCCESS) {
        cairo_surface_destroy(image);return NULL;
    }
    double w=cairo_image_surface_get_width(image),h=cairo_image_surface_get_height(image);
    double scale=fmin(512/w,512/h);
    cairo_surface_t *surface=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,512,512);
    cairo_t *cr=cairo_create(surface);
    cairo_translate(cr,(512-w*scale)/2,(512-h*scale)/2);cairo_scale(cr,scale,scale);
    cairo_set_source_surface(cr,image,0,0);cairo_paint(cr);
    cairo_status_t status=cairo_status(cr);
    cairo_destroy(cr);cairo_surface_destroy(image);
    if(status!=CAIRO_STATUS_SUCCESS){cairo_surface_destroy(surface);return NULL;}
    return surface;
}

static inline void nostromo_space_orb(cairo_t *cr,cairo_surface_t *surface,double x,double y,
    double size,double seconds,int mode) {
    if(!surface)return;
    double enter=mode==2?nostromo_space_enter(seconds):1;
    double scale=.92+.08*enter,alpha=mode==2?fmin(1,fmax(0,seconds/.18)):1;
    double phase=mode==2?floor(seconds*NOSTROMO_EFFECT_FPS)/NOSTROMO_EFFECT_FPS:0;
    double jitter=mode==2?.45*sin(phase*17)*sin(phase*3):0;
    cairo_save(cr);
    cairo_translate(cr,x+size/2+jitter,y+size/2+12*(1-enter));
    cairo_scale(cr,scale,scale);cairo_translate(cr,-size/2,-size/2);
    if(mode) {
        const double offsets[4][2]={{-2,0},{2,0},{0,-2},{0,2}};
        for(int i=0;i<4;i++) {
            cairo_save(cr);cairo_translate(cr,offsets[i][0],offsets[i][1]);
            cairo_scale(cr,size/512,size/512);cairo_set_source_surface(cr,surface,0,0);
            cairo_paint_with_alpha(cr,.10*alpha);cairo_restore(cr);
        }
    }
    cairo_scale(cr,size/512,size/512);cairo_set_source_surface(cr,surface,0,0);
    cairo_paint_with_alpha(cr,alpha);cairo_restore(cr);
}

static inline void nostromo_space_texture(cairo_t *cr,int width,int height,double seconds,int mode) {
    if(!mode)return;
    double t=mode==2?fmod(seconds,256):0;
    /* Repeated six-row phosphor pattern; the reference scan phase is 60*1.95.
     * Real elapsed time controls speed, independently of output refresh rate. */
    cairo_surface_t *tile=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,6,6);
    cairo_t *tc=cairo_create(tile);
    for(int y=0;y<6;y++) {
        cairo_set_source_rgba(tc,0,0,0,.065+.065*sin(y*6.283185307179586/6-117*t));
        cairo_rectangle(tc,0,y,6,1);cairo_fill(tc);
    }
    cairo_set_source_rgba(tc,0,0,0,.025);cairo_rectangle(tc,2,0,1,6);cairo_fill(tc);
    cairo_destroy(tc);
    cairo_save(cr);cairo_set_source_surface(cr,tile,0,0);
    cairo_pattern_set_extend(cairo_get_source(cr),CAIRO_EXTEND_REPEAT);cairo_paint(cr);
    cairo_surface_destroy(tile);
    /* Sparse monochrome grain: one tiny repeated tile, no full-output noise buffer. */
    tile=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,96,96);tc=cairo_create(tile);
    uint32_t seed=17;
    cairo_set_source_rgba(tc,1,1,1,.035);
    for(int i=0;i<128;i++) {
        seed=seed*1664525u+1013904223u;int x=(seed>>16)%96;
        seed=seed*1664525u+1013904223u;int y=(seed>>16)%96;
        cairo_rectangle(tc,x,y,1,1);
    }
    cairo_fill(tc);cairo_destroy(tc);
    int frame=(int)(t*NOSTROMO_EFFECT_FPS);
    cairo_set_source_surface(cr,tile,-(frame*17%96),-(frame*29%96));
    cairo_pattern_set_extend(cairo_get_source(cr),CAIRO_EXTEND_REPEAT);cairo_paint(cr);
    cairo_surface_destroy(tile);
    if(mode==2) {
        cairo_set_source_rgba(cr,0,0,0,.005*(1+sin(t*120)));cairo_paint(cr);
    }
    cairo_translate(cr,width/2.0,height/2.0);cairo_scale(cr,width/2.0,height/2.0);
    cairo_pattern_t *edge=cairo_pattern_create_radial(0,0,.45,0,0,1.45);
    cairo_pattern_add_color_stop_rgba(edge,0,0,0,0,0);
    cairo_pattern_add_color_stop_rgba(edge,1,0,0,0,.18);
    cairo_set_source(cr,edge);cairo_paint(cr);cairo_pattern_destroy(edge);cairo_restore(cr);
}
#endif
