/* Verify the real painters: animated frames differ, static/off do not, and the
 * splash releases its opaque overlay. No compositor or authentication involved. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../../gtklock/art.h"
#include "../../session/splash-art.h"

static uint64_t frame(cairo_surface_t *logo,int mode,double time,int scene)
{
    cairo_surface_t *s=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,800,600);
    cairo_t *cr=cairo_create(s);
    if(scene==1)nostromo_splash_art(cr,logo,800,600,time,mode==2,mode!=0);
    else {
        cairo_set_source_rgb(cr,0,0,0);cairo_paint(cr);
        nostromo_lock_art(cr,logo,800,600,time,mode,scene==2,210,390,380,48,1);
    }
    cairo_destroy(cr);cairo_surface_flush(s);
    uint64_t hash=14695981039346656037ull;
    for(int y=0;y<600;y++) {
        uint32_t *row=(uint32_t *)(cairo_image_surface_get_data(s)+y*cairo_image_surface_get_stride(s));
        for(int x=0;x<800;x++) {
            uint32_t p=row[x];
            assert((p&255)==((p>>8)&255) && (p&255)==((p>>16)&255));
            if(scene==1 && mode==2 && time>=NOSTROMO_SPLASH_SECONDS)assert(p==0);
            hash=(hash^p)*1099511628211ull;
        }
    }
    cairo_surface_destroy(s);return hash;
}
int main(int argc,char **argv)
{
    if(argc==2 && !strcmp(argv[1],"--mode")){printf("%d\n",nostromo_space_mode());return 0;}
    assert(nostromo_space_enter(0)<.001 && nostromo_space_enter(1.2)==1);
    cairo_surface_t *logo=nostromo_space_logo("art/nostromo-orb.png");assert(logo);
    assert(nostromo_space_logo("missing-logo.png")==NULL);
    assert(nostromo_bounce(1,100,35)==35 && nostromo_bounce(4,100,35)==60);
    for(int scene=0;scene<3;scene++) {
        for(int mode=0;mode<=1;mode++)assert(frame(logo,mode,.3,scene)==frame(logo,mode,1.5,scene));
        assert(frame(logo,2,.3,scene)!=frame(logo,2,.6,scene));
    }
    frame(logo,2,NOSTROMO_SPLASH_SECONDS,1);
    cairo_surface_destroy(logo);
    puts("Shared CRT: monochrome, real motion, static/off stability and splash transparency passed.");
    return 0;
}
