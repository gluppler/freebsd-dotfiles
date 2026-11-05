/* Host composition, not a running FreeBSD capture. Geometry comes from native code. */
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <fontconfig/fontconfig.h>
#include <cairo.h>
#include <pango/pangocairo.h>
#include "../src/dwl/rail.h"
#include "../src/gtklock/art.h"
#include "../src/session/splash-art.h"
#include "../src/fuzzel/panel.h"
#include "preview-tag.h"
#include "preview-notification.h"

static cairo_surface_t *logo;
static void cells(cairo_t *c,double x,double y,const char *value) {
    const double cw=8.9,ch=19;
    int column=0,row=0;
    for(const char *p=value;*p;p=g_utf8_next_char(p)){
        gunichar cp=g_utf8_get_char(p);
        if(cp=='\n'){column=0;row++;continue;}
        double px=x+column*cw,py=y+row*ch;
        if(cp==0x2588 || cp==0x2580 || cp==0x2584){
            cairo_save(c);cairo_set_antialias(c,CAIRO_ANTIALIAS_NONE);
            cairo_set_source_rgb(c,1,1,1);
            cairo_rectangle(c,px,py+(cp==0x2584?ch/2:0),cw,cp==0x2588?ch:ch/2);
            cairo_fill(c);
            cairo_restore(c);
        }else if(cp!=' '){
            char letter[8]={0};g_unichar_to_utf8(cp,letter);
            PangoLayout *layout=pango_cairo_create_layout(c);
            PangoFontDescription *font=pango_font_description_from_string("Azeret Mono 11");
            pango_layout_set_font_description(layout,font);pango_font_description_free(font);
            pango_layout_set_text(layout,letter,-1);cairo_set_source_rgb(c,1,1,1);
            cairo_move_to(c,px,py);pango_cairo_show_layout(c,layout);g_object_unref(layout);
        }
        column++;
    }
}
static void text(cairo_t *c, double x, double y, const char *value, const char *face, double gray) {
    PangoLayout *p=pango_cairo_create_layout(c);
    PangoFontDescription *font=pango_font_description_from_string(face);
    pango_layout_set_font_description(p,font);pango_font_description_free(font);
    pango_layout_set_text(p,value,-1);cairo_set_source_rgb(c,gray,gray,gray);
    cairo_move_to(c,x,y);pango_cairo_show_layout(c,p);g_object_unref(p);
}
static void image(cairo_t *c,const char *path,int x,int y,int w,int h) {
    cairo_surface_t *s=cairo_image_surface_create_from_png(path);
    if(cairo_surface_status(s)!=CAIRO_STATUS_SUCCESS){fprintf(stderr,"Missing image: %s\n",path);exit(1);}
    cairo_save(c);cairo_translate(c,x,y);cairo_scale(c,(double)w/cairo_image_surface_get_width(s),(double)h/cairo_image_surface_get_height(s));
    cairo_set_source_surface(c,s,0,0);cairo_paint(c);cairo_restore(c);cairo_surface_destroy(s);
}
static void line(cairo_t *c,int x,int y,int w,int h) {
    cairo_set_source_rgb(c,1,1,1);cairo_set_line_width(c,1);
    cairo_move_to(c,x+.5,y+.5);cairo_line_to(c,x+w+.5,y+h+.5);cairo_stroke(c);
}
static void window(cairo_t *c,int x,int y,int w,int h,int side,const char *label) {
    int right=side==NOSTROMO_RIGHT?28:0,bottom=side==NOSTROMO_BOTTOM?20:0,top=side==NOSTROMO_TOP?20:0;
    /* Match dwl: outline/background cover the body, never the attached rail. */
    if(right){cairo_set_source_rgba(c,0,0,0,.90);cairo_rectangle(c,x,y,w-right,h);cairo_fill(c);}
    cairo_set_source_rgb(c,1,1,1);cairo_set_line_width(c,2);
    cairo_rectangle(c,x+1,y+top+1,w-right-2,h-top-bottom-2);cairo_stroke(c);
    cairo_save(c);cairo_translate(c,right?x+w-right:x,bottom?y+h-bottom:y);
    nostromo_rail_draw(c,right?right:w,right?h:20,side,label);cairo_restore(c);
}
/* A normal GUI supplies a finished surface, which dwl blends once at 90%.
 * Draw its entire content into one group; keep server-side rails outside it. */
static void panel_begin(cairo_t *c,int x,int y,int w,int h) {
    cairo_save(c);cairo_rectangle(c,x,y,w,h);cairo_clip(c);cairo_push_group(c);
    cairo_set_source_rgb(c,0,0,0);cairo_paint(c);
}
static void panel_end(cairo_t *c,const char *appid) {
    cairo_pop_group_to_source(c);cairo_paint_with_alpha(c,nostromo_client_opacity(appid,1));cairo_restore(c);
}
static void bar(cairo_t *c) {
    cairo_surface_t *s=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,1920,40);
    pixman_image_t *p=pixman_image_create_bits(PIXMAN_a8r8g8b8,1920,40,(uint32_t *)cairo_image_surface_get_data(s),cairo_image_surface_get_stride(s));
    cairo_set_source_rgb(c,0,0,0);cairo_rectangle(c,0,0,1920,40);cairo_fill(c);
    for(int i=0;i<9;i++)nostromo_tag(p,i*36,(i+1)*36,40,i==0,1);
    pixman_image_unref(p);cairo_surface_mark_dirty(s);cairo_set_source_surface(c,s,0,0);cairo_paint(c);cairo_surface_destroy(s);
    for(int i=0;i<9;i++){char n[2]={(char)('1'+i),0};text(c,i*36+12,9,n,"Michroma 10.5",i?1:0);}
    text(c,342,9,"> <","Michroma 10.5",1);
    /* Unavailable hardware readings stay unavailable in a host preview. */
    const char *status="♨ --   ▰ --   ≋ --   ◇ DOWN   ᛒ --   ♪ --   ☼ --   文 EN   ◷ 11-03 12:00";
    PangoLayout *measure=pango_cairo_create_layout(c);
    PangoFontDescription *font=pango_font_description_from_string("Michroma 10.5");
    pango_layout_set_font_description(measure,font);pango_font_description_free(font);
    pango_layout_set_text(measure,status,-1);int width;pango_layout_get_pixel_size(measure,&width,NULL);
    g_object_unref(measure);text(c,1904-width,9,status,"Michroma 10.5",1);
}
static void notification(cairo_t *c) {
    cairo_save(c);cairo_translate(c,1564,60);
    PangoContext *context=pango_cairo_create_context(c);
    PangoFontDescription *font=pango_font_description_from_string("Michroma 10");
    PangoLayout *label=nostromo_source(context,font,"NOTIF");
    int height=nostromo_source_height(label,1);
    cairo_set_source_rgba(c,0,0,0,230/255.);nostromo_frame(c,.5,height/2.0,339,112,12,1,C_BOT_RIGHT);cairo_fill_preserve(c);
    cairo_set_source_rgb(c,1,1,1);cairo_set_line_width(c,1);cairo_stroke(c);
    text(c,12,height+12,"Screenshot saved","Michroma 10",1);
    text(c,12,height+39,"~/Pictures/Screenshots","Michroma 9",.8);
    nostromo_source_draw(c,label,340,1);
    g_object_unref(label);g_object_unref(context);pango_font_description_free(font);cairo_restore(c);
}
static void browser(cairo_t *c) {
    panel_begin(c,780,124,1100,772);
    text(c,794,132,"1  Start · nostromo","Azeret Mono 10",1);
    image(c,".build/start-page.png",790,158,1080,718);
    text(c,794,878,"file:///home/gluppler/.local/share/nostromo/start/index.html","Azeret Mono 8",.8);
    panel_end(c,"qutebrowser");window(c,780,104,1100,792,NOSTROMO_TOP,"");
}
static void terminal(cairo_t *c,int mux) {
    const int x=74,y=264,w=1148,h=716;
    window(c,x,y,w,h,1,"/home/gluppler/Projects/firmware");
    if(!mux){
        gchar *dashboard=NULL;
        if(!g_file_get_contents(".build/dashboard-preview.txt",&dashboard,NULL,NULL))exit(1);
        cells(c,x+18,y+18,dashboard);g_free(dashboard);
        text(c,x+18,y+h-32,"NORMAL   [No Name]","Azeret Mono 10",1);
    }else{
        int split=x+(w-28)*65/100;
        line(c,split,y+2,0,h-36);line(c,split,y+h/2,w-30-(split-x),0);
        text(c,x+16,y+18,"src/lib.rs   [vis]","Azeret Mono 11",1);
        text(c,x+16,y+68,"#![no_std]\n\n/// Logic shared with the board application.\npub fn next_counter(value: u32) -> u32 {\n    value.wrapping_add(1)\n}","Azeret Mono 11",1);
        text(c,split+16,y+18,"gluppler@nostromo firmware\n> cargo check\n\n    Checking nostromo_embedded\n    Finished dev profile\n\n> ","Azeret Mono 10",1);
        text(c,split+16,y+h/2+18,"lazygit\n\nFiles\n  M  src/lib.rs\n\nBranches\n  main","Azeret Mono 10",1);
        line(c,x+2,y+h-34,w-32,0);
        text(c,x+16,y+h-27,"1 vis    2 shell    3 git                         abduco · firmware","Azeret Mono 10",1);
    }
}
static void menu(cairo_t *c,const char *name,int output_width,int output_height,double scale) {
    char path[160];gchar *contents=NULL;
    snprintf(path,sizeof path,".build/native-preview/%s-menu.txt",name);
    if(!g_file_get_contents(path,&contents,NULL,NULL))exit(1);
    gchar **rows=g_strsplit(g_strchomp(contents),"\n",-1);
    cairo_save(c);cairo_identity_matrix(c);cairo_scale(c,scale,scale);
    PangoLayout *layout=pango_cairo_create_layout(c);
    PangoFontDescription *font=pango_font_description_from_string("Michroma 10.5");
    pango_layout_set_font_description(layout,font);pango_font_description_free(font);
    int cell,measured=0,th=0;
    pango_layout_set_text(layout,"o",-1);pango_layout_get_pixel_size(layout,&cell,&th);
    for(int i=0;rows[i];i++) {
        int width;
        pango_layout_set_text(layout,rows[i],-1);pango_layout_get_pixel_size(layout,&width,NULL);
        measured=MAX(measured,width+(i==0?cell*6:0));
    }
    g_object_unref(layout);
    int count=MIN(12,(int)g_strv_length(rows)-1),row_height=32;
    struct nostromo_panel_size size=nostromo_panel_dimensions(measured,26,76,
        row_height,count,output_width/scale-40,output_height/scale-40,1);
    int w=size.width,h=size.height,x=(output_width/scale-w)/2,y=(output_height/scale-h)/2;
    cairo_surface_t *surface=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,w,h);
    pixman_image_t *pix=pixman_image_create_bits(PIXMAN_a8r8g8b8,w,h,
        (uint32_t *)cairo_image_surface_get_data(surface),cairo_image_surface_get_stride(surface));
    pixman_color_t bg={0,0,0,0xe6e6},fg={65535,65535,65535,65535};
    nostromo_panel(pix,&bg,&fg,w,h,2,1,24);pixman_image_unref(pix);
    cairo_surface_mark_dirty(surface);cairo_set_source_surface(c,surface,x,y);cairo_paint(c);cairo_surface_destroy(surface);
    cairo_save(c);cairo_rectangle(c,x+26,y+18,w-52,h-36);cairo_clip(c);
    text(c,x+26,y+18+(row_height-th)/2,rows[0],"Michroma 10.5",1);
    for(int i=0;i<size.rows;i++) {
        int row_y=y+18+row_height+8+i*row_height;
        if(!i){cairo_set_source_rgb(c,1,1,1);cairo_rectangle(c,x+26,row_y,w-52,row_height);cairo_fill(c);}
        text(c,x+26,row_y+(row_height-th)/2,rows[i+1],"Michroma 10.5",i?1:0);
    }
    cairo_restore(c);cairo_restore(c);g_strfreev(rows);g_free(contents);
}
static void viewers(cairo_t *c) {
    panel_begin(c,100,140,690,760);
    text(c,146,180,"FreeBSD Base-Setup","Michroma 17",1);
    text(c,146,245,"Manual installation\n\nThinkPad T14 Gen 2 Intel\nFreeBSD 15.1-RELEASE amd64\n\nHostname: nostromo\nKeymap: United States of America\n\nComplete the manual installation before\nrunning the post-install setup.","Azeret Mono 11",1);
    panel_end(c,"org.pwmt.zathura");window(c,100,140,690,780,NOSTROMO_BOTTOM,"BASE-SETUP.pdf");
    panel_begin(c,900,250,880,580);
    image(c,"assets/wallpapers/nostromo-1920x1080.png",912,264,856,482);
    panel_end(c,"swayimg");window(c,900,250,880,600,NOSTROMO_BOTTOM,"nostromo-1920x1080.png");
}
static void documentation(cairo_t *c) {
    window(c,64,230,860,650,NOSTROMO_RIGHT,"/home/gluppler/Projects/firmware");
    gchar *code=NULL,*markup=NULL;
    if(!g_file_get_contents(".build/native-preview/example.c",&code,NULL,NULL) ||
       !g_file_get_contents(".build/native-preview/reference-markup.txt",&markup,NULL,NULL))exit(1);
    text(c,82,250,code,"Azeret Mono 11",1);
    text(c,82,842,"NORMAL   example.c","Azeret Mono 10",1);
    window(c,1000,140,850,800,NOSTROMO_RIGHT,"/home/gluppler/Projects/firmware");
    cairo_save(c);cairo_rectangle(c,1016,156,792,735);cairo_clip(c);
    PangoLayout *layout=pango_cairo_create_layout(c);
    PangoFontDescription *font=pango_font_description_from_string("Azeret Mono 10.5");
    pango_layout_set_font_description(layout,font);pango_font_description_free(font);
    pango_layout_set_markup(layout,markup,-1);cairo_set_source_rgb(c,1,1,1);
    cairo_move_to(c,1016,156);pango_cairo_show_layout(c,layout);g_object_unref(layout);
    cairo_restore(c);g_free(code);g_free(markup);
    text(c,1018,908,":","Azeret Mono 10",1);
}
int main(int argc,char **argv) {
    if(argc!=6 && argc!=7)return 2;
    const char *scene=argv[1];int width=atoi(argv[3]),height=atoi(argv[4]);double time=atof(argv[5]);
    if(width<320 || height<180 || width>7680 || height>4320)return 2;
    if(!FcConfigAppFontAddFile(NULL,(const FcChar8 *)"assets/fonts/Michroma-Regular.ttf") ||
       !FcConfigAppFontAddFile(NULL,(const FcChar8 *)"assets/fonts/AzeretMono.ttf")){
        fprintf(stderr,"Cannot load the bundled preview fonts.\n");return 1;
    }
    PangoFontMap *map=pango_cairo_font_map_new_for_font_type(CAIRO_FONT_TYPE_FT);
    if(!map){fprintf(stderr,"Preview requires Pango Fontconfig/FreeType support.\n");return 1;}
    pango_cairo_font_map_set_default(PANGO_CAIRO_FONT_MAP(map));
    PangoContext *font_context=pango_font_map_create_context(map);
    const char *families[]={"Michroma","Azeret Mono"};
    for(size_t i=0;i<sizeof families/sizeof families[0];i++){
        PangoFontDescription *wanted=pango_font_description_from_string(families[i]);
        PangoFont *resolved=pango_font_map_load_font(map,font_context,wanted);
        PangoFontDescription *actual=resolved?pango_font_describe(resolved):NULL;
        if(!actual || strcmp(pango_font_description_get_family(actual),families[i])){
            fprintf(stderr,"Preview font substituted: %s\n",families[i]);return 1;
        }
        pango_font_description_free(actual);pango_font_description_free(wanted);g_object_unref(resolved);
    }
    g_object_unref(font_context);g_object_unref(map);
    logo=nostromo_space_logo("assets/nostromo-orb.png");if(!logo)return 1;
    /* Opaque preview frames keep one PNG pixel format through the splash fade.
     * Mixing RGB/RGBA makes ffmpeg reset its buffered palette graph mid-animation. */
    cairo_surface_t *s=cairo_image_surface_create(CAIRO_FORMAT_RGB24,width,height);cairo_t *c=cairo_create(s);
    cairo_set_source_rgb(c,0,0,0);cairo_paint(c);cairo_scale(c,width/1920.,height/1080.);
    if(!strcmp(scene,"lock") || !strcmp(scene,"idle")){
        int idle=!strcmp(scene,"idle");
        if(!idle){text(c,770,562,"Password","Michroma 10.5",1);text(c,790,611,"••••••••","Michroma 12",1);}
        nostromo_lock_art(c,logo,1920,1080,time,2,idle,770,598,380,48,1);
    }else if(!strcmp(scene,"splash")){
        nostromo_splash_art(c,logo,1920,1080,time,1,1);
    }else{
        int network=!strcmp(scene,"wifi") || !strcmp(scene,"vpn") || !strcmp(scene,"bluetooth") || !strncmp(scene,"panel-",6);
        image(c,"assets/wallpapers/nostromo-1920x1080.png",0,0,1920,1080);bar(c);
        if(strcmp(scene,"desktop") && strcmp(scene,"viewers") && strcmp(scene,"docs") && !network)browser(c);
        if(!strcmp(scene,"docs"))documentation(c);
        if(!strcmp(scene,"viewers"))viewers(c);
        if(!strcmp(scene,"workspace") || !strcmp(scene,"menu"))terminal(c,0);
        if(!strcmp(scene,"multiplexer"))terminal(c,1);
        if(!strcmp(scene,"menu"))menu(c,"main",width,height,argc==7?atof(argv[6]):width/1920.);
        if(!strcmp(scene,"notification"))notification(c);
        if(network)menu(c,!strncmp(scene,"panel-",6)?scene+6:scene,width,height,argc==7?atof(argv[6]):1);
    }
    cairo_destroy(c);cairo_status_t status=cairo_surface_write_to_png(s,argv[2]);
    cairo_surface_destroy(s);cairo_surface_destroy(logo);return status!=CAIRO_STATUS_SUCCESS;
}
