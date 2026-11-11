/* Pixel checks use the real painters, without a compositor or window server. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "../../dwl/rail.h"
#include "../../fuzzel/panel.h"

static unsigned alpha(cairo_surface_t *surface, int x, int y)
{
    cairo_surface_flush(surface);
    uint32_t *row=(uint32_t *)(cairo_image_surface_get_data(surface)+y*cairo_image_surface_get_stride(surface));
    return row[x]>>24;
}
int main(void)
{
    assert(nostromo_rail_kind("foot")==NOSTROMO_RIGHT);
    assert(nostromo_rail_kind("nostromo.foot.scratch")==NOSTROMO_RIGHT);
    assert(nostromo_rail_kind("org.pwmt.zathura")==NOSTROMO_BOTTOM);
    assert(nostromo_rail_kind("swayimg")==NOSTROMO_BOTTOM);
    assert(nostromo_rail_kind("qutebrowser")==NOSTROMO_TOP);
    assert(nostromo_rail_kind(NULL)==NOSTROMO_TOP);
    const char *clients[]={"qutebrowser","org.pwmt.zathura","swayimg","other",NULL};
    for(size_t i=0;i<sizeof clients/sizeof clients[0];i++) {
        assert(fabs(nostromo_client_opacity(clients[i],1)-.90)<.0001);
        assert(fabs(nostromo_client_opacity(clients[i],.35)-.315)<.0001);
    }
    assert(nostromo_client_opacity("foot",1)==1);
    assert(nostromo_client_opacity("nostromo.foot.scratch",1)==1);
    char title[64], small_title[8];
    nostromo_viewer_title("guide 日本語.pdf",title,sizeof title);
    assert(!strcmp(title,"guide 日本語.pdf"));
    nostromo_viewer_title("bad\nname.pdf",title,sizeof title);assert(!*title);
    nostromo_viewer_title("bad\xff",title,sizeof title);assert(!*title);
    nostromo_viewer_title("日本語.png",small_title,sizeof small_title);
    assert(g_utf8_validate(small_title,-1,NULL) && strlen(small_title)<sizeof small_title);
    /* Content width, row count, DPI and a small output all change panel size. */
    struct nostromo_panel_size short_menu=nostromo_panel_dimensions(100,26,76,32,2,1880,1040,1);
    struct nostromo_panel_size long_menu=nostromo_panel_dimensions(590,26,76,32,8,1880,1040,1);
    assert(short_menu.width<long_menu.width && short_menu.height<long_menu.height);
    assert(long_menu.width>=590+52 && long_menu.rows==8);
    struct nostromo_panel_size small=nostromo_panel_dimensions(900,26,76,32,12,280,200,1);
    assert(small.width<=280 && small.height<=200 && small.rows>0 && small.rows<12);
    struct nostromo_panel_size hidpi=nostromo_panel_dimensions(1180,52,152,64,8,3760,2080,2);
    assert(hidpi.width==2*long_menu.width && hidpi.height==2*long_menu.height);
    for(int scale=1;scale<=4;scale*=2) {
        for(int side=NOSTROMO_RIGHT;side<=NOSTROMO_BOTTOM;side++) {
            int w=side==NOSTROMO_RIGHT?28:600,h=side==NOSTROMO_RIGHT?600:28;
            cairo_surface_t *s=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,w*scale,h*scale);
            cairo_t *c=cairo_create(s);cairo_scale(c,scale,scale);
            nostromo_rail_draw(c,w,h,side,"");cairo_destroy(c);
            /* Only outer corners are square; the approved recess is unchanged. */
            assert(alpha(s,(w-1)*scale,0)==255);
            assert(alpha(s,(w-1)*scale,(h-1)*scale)==255);
            assert(alpha(s,0,(h-1)*scale)==255);
            /* End caps remain full; the middle and 15%/85% edges are recessed. */
            int along[]={30,90,300,510,570};
            for(size_t i=0;i<sizeof along/sizeof along[0];i++) {
                int x=side==NOSTROMO_RIGHT?27:along[i],y=side==NOSTROMO_RIGHT?along[i]:27;
                assert(alpha(s,x*scale,y*scale)==(i==0||i==4?255:0));
            }
            assert(alpha(s,(side==NOSTROMO_RIGHT?13:300)*scale,(side==NOSTROMO_RIGHT?300:13)*scale)==255);
            cairo_surface_destroy(s);
        }
        cairo_surface_t *label=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,28*scale,600*scale);
        cairo_t *lc=cairo_create(label);cairo_scale(lc,scale,scale);
        nostromo_rail_draw(lc,28,600,NOSTROMO_RIGHT,"~/project");cairo_destroy(lc);
        cairo_surface_flush(label);
        int first=600*scale,last=-1;
        for(int y=0;y<600*scale;y++) {
            uint32_t *row=(uint32_t *)(cairo_image_surface_get_data(label)+y*cairo_image_surface_get_stride(label));
            for(int x=0;x<19*scale;x++)if((row[x]>>24)==255 && (row[x]&255)<128) {
                if(y<first)first=y;
                if(y>last)last=y;
            }
        }
        assert(last>first && abs(first+last-600*scale)<12*scale);
        cairo_surface_destroy(label);
        label=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,600*scale,20*scale);
        lc=cairo_create(label);cairo_scale(lc,scale,scale);
        nostromo_rail_draw(lc,600,20,NOSTROMO_BOTTOM,"BASE-SETUP.pdf");cairo_destroy(lc);
        cairo_surface_flush(label);first=600*scale;last=-1;
        for(int y=0;y<20*scale;y++) {
            uint32_t *row=(uint32_t *)(cairo_image_surface_get_data(label)+y*cairo_image_surface_get_stride(label));
            for(int x=0;x<600*scale;x++)if((row[x]>>24)==255 && (row[x]&255)<128) {
                assert(y<14*scale); /* Text stays inside the white spine. */
                if(x<first)first=x;
                if(x>last)last=x;
            }
        }
        assert(last>first && abs(first+last-600*scale)<12*scale);
        cairo_surface_destroy(label);
        cairo_surface_t *s=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,400*scale,600*scale);
        pixman_image_t *p=pixman_image_create_bits(PIXMAN_a8r8g8b8,400*scale,600*scale,
            (uint32_t *)cairo_image_surface_get_data(s),cairo_image_surface_get_stride(s));
        pixman_color_t bg={0,0,0,0xe6e6},fg={65535,65535,65535,65535};
        nostromo_panel(p,&bg,&fg,400*scale,600*scale,scale,scale,24*scale);
        pixman_image_unref(p);cairo_surface_mark_dirty(s);
        assert(alpha(s,0,30*scale)==255);
        assert(alpha(s,0,90*scale)==0);
        assert(alpha(s,0,300*scale)==0);
        assert(alpha(s,0,510*scale)==0);
        assert(alpha(s,0,570*scale)==255);
        assert(alpha(s,8*scale,300*scale)==255);
        assert(alpha(s,200*scale,300*scale)==230);
        cairo_surface_destroy(s);
    }
    puts("Rails: unchanged divots, square corners and centered labels passed at 1x/2x/4x. Panels fit content/outputs, use 90% opacity and never double-blend foot.");
    return 0;
}
