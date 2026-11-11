/* ISC: Copyright 2026 Nostromo contributors. Provided without warranty.
 * GPU output treatment through wlroots 0.20's public GLES2/EGL interfaces.
 * No CPU readback, client-texture modification or private renderer fields. */
#include <wlr/render/egl.h>
#include <wlr/render/gles2.h>
#include "nostromo-control-v1-server.h"

struct NostromoCRT {
    struct wl_list link;
    Monitor *monitor;
    GLuint texture;
    int width, height;
    bool render_locked;
};
static struct wl_list nostromo_crt_outputs;
static struct wl_event_source *nostromo_crt_timer;
static unsigned int nostromo_crt_mode=2;
static GLuint nostromo_crt_program, nostromo_crt_vertices;
/* A brief map fade shares the existing effect timer. No per-window idle timer. */
static void nostromo_animate_buffer(struct wlr_scene_buffer *buffer, int x, int y, void *data) {
    /* Client surfaces (including popups), never compositor-drawn rails. */
    if(buffer->opacity!=*(float *)data && wlr_scene_surface_try_from_buffer(buffer))
        wlr_scene_buffer_set_opacity(buffer, *(float *)data);
}
static void nostromo_animate_start(Client *c) {
    if(nostromo_crt_mode!=2 || !c->scene)return;
    c->nfade_started=(uint64_t)g_get_monotonic_time();
    float opacity=nostromo_client_opacity(client_get_appid(c),.35f);
    wlr_scene_node_for_each_buffer(&c->scene->node,nostromo_animate_buffer,&opacity);
}
static void nostromo_animate_tick(void) {
    Client *c;
    uint64_t now=(uint64_t)g_get_monotonic_time();
    wl_list_for_each(c,&clients,link) {
        if(!c->scene)continue;
        double elapsed=c->nfade_started?(now-c->nfade_started)/240000.0:1;
        float fade=nostromo_crt_mode==2 && elapsed<1 ? .35f+.65f*(1-(1-elapsed)*(1-elapsed)) : 1;
        float opacity=nostromo_client_opacity(client_get_appid(c),fade);
        wlr_scene_node_for_each_buffer(&c->scene->node,nostromo_animate_buffer,&opacity);
        if(fade>=1)c->nfade_started=0;
    }
}
static const char nostromo_crt_fragment[] =
#include "crt-shader.h"
;
static const char nostromo_crt_vertex[] =
    "attribute vec2 position; varying vec2 uv;"
    "void main(){uv=position*0.5+0.5;gl_Position=vec4(position,0.0,1.0);}";

struct NostromoEGL {
    EGLDisplay display, previous_display;
    EGLContext previous_context;
    EGLSurface draw, read;
};
static bool nostromo_egl_begin(struct NostromoEGL *saved) {
    if (!drw || !wlr_renderer_is_gles2(drw)) return false;
    struct wlr_egl *egl=wlr_gles2_renderer_get_egl(drw);
    saved->display=wlr_egl_get_display(egl);
    saved->previous_display=eglGetCurrentDisplay();
    saved->previous_context=eglGetCurrentContext();
    saved->draw=eglGetCurrentSurface(EGL_DRAW);
    saved->read=eglGetCurrentSurface(EGL_READ);
    return eglMakeCurrent(saved->display,EGL_NO_SURFACE,EGL_NO_SURFACE,wlr_egl_get_context(egl));
}
static void nostromo_egl_end(struct NostromoEGL *saved) {
    if (saved->previous_display!=EGL_NO_DISPLAY)
        eglMakeCurrent(saved->previous_display,saved->draw,saved->read,saved->previous_context);
    else eglMakeCurrent(saved->display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);
}
static struct NostromoCRT *nostromo_crt_find(Monitor *m) {
    struct NostromoCRT *output;
    wl_list_for_each(output,&nostromo_crt_outputs,link) if(output->monitor==m)return output;
    return NULL;
}
static void nostromo_crt_rearm(void) {
    if(!nostromo_crt_timer)return;
    Monitor *m;
    bool active=false;
    wl_list_for_each(m,&mons,link) if(m->wlr_output->enabled)active=true;
    wl_event_source_timer_update(nostromo_crt_timer,nostromo_crt_mode==2 && active?83:0);
}
static int nostromo_crt_tick(void *data) {
    Monitor *m;
    if(nostromo_crt_mode==2) wl_list_for_each(m,&mons,link) {
        if(!m->wlr_output->enabled)continue;
        wlr_damage_ring_add_whole(&m->scene_output->damage_ring);
        wlr_output_schedule_frame(m->wlr_output);
    }
    nostromo_crt_rearm();
    return 0;
}
static void nostromo_crt_texture_free(struct NostromoCRT *output) {
    struct NostromoEGL saved;
    if(output->texture && nostromo_egl_begin(&saved)) {
        glDeleteTextures(1,&output->texture);
        nostromo_egl_end(&saved);
    }
    output->texture=0;output->width=output->height=0;
}
static void nostromo_crt_set(unsigned int mode) {
    struct NostromoCRT *output;
    if(mode>2 || (mode && !wlr_renderer_is_gles2(drw)))mode=0;
    nostromo_crt_mode=mode;
    if(mode!=2)nostromo_animate_tick();
    wl_list_for_each(output,&nostromo_crt_outputs,link) {
        bool enabled=mode!=0;
        if(enabled!=output->render_locked) {
            wlr_output_lock_attach_render(output->monitor->wlr_output,enabled);
            output->render_locked=enabled;
        }
        if(!enabled)nostromo_crt_texture_free(output);
        wlr_damage_ring_add_whole(&output->monitor->scene_output->damage_ring);
        wlr_output_schedule_frame(output->monitor->wlr_output);
    }
    nostromo_crt_rearm();
}
static void nostromo_crt_add(Monitor *m) {
    struct NostromoCRT *output=ecalloc(1,sizeof *output);
    output->monitor=m;
    wl_list_insert(&nostromo_crt_outputs,&output->link);
    nostromo_crt_set(nostromo_crt_mode);
}
static void nostromo_crt_remove(Monitor *m) {
    struct NostromoCRT *output=nostromo_crt_find(m);
    if(!output)return;
    nostromo_crt_texture_free(output);
    wl_list_remove(&output->link);free(output);
}
static void nostromo_crt_gpu_reset(void) {
    /* Called before the lost renderer is replaced; old object IDs are unusable. */
    struct NostromoCRT *output;
    wl_list_for_each(output,&nostromo_crt_outputs,link) {
        output->texture=0;output->width=output->height=0;
    }
    nostromo_crt_program=nostromo_crt_vertices=0;
}
static GLuint nostromo_crt_shader(GLenum type,const char *source) {
    GLuint shader=glCreateShader(type);
    GLint ok=0;
    glShaderSource(shader,1,&source,NULL);glCompileShader(shader);
    glGetShaderiv(shader,GL_COMPILE_STATUS,&ok);
    if(!ok) {
        char log[1024];glGetShaderInfoLog(shader,sizeof log,NULL,log);
        fprintf(stderr,"CRT shader: %s\n",log);glDeleteShader(shader);return 0;
    }
    return shader;
}
static bool nostromo_crt_init_program(void) {
    if(nostromo_crt_program)return true;
    GLuint vertex=nostromo_crt_shader(GL_VERTEX_SHADER,nostromo_crt_vertex);
    GLuint fragment=nostromo_crt_shader(GL_FRAGMENT_SHADER,nostromo_crt_fragment);
    if(!vertex || !fragment){if(vertex)glDeleteShader(vertex);if(fragment)glDeleteShader(fragment);return false;}
    nostromo_crt_program=glCreateProgram();
    glAttachShader(nostromo_crt_program,vertex);glAttachShader(nostromo_crt_program,fragment);
    glBindAttribLocation(nostromo_crt_program,0,"position");glLinkProgram(nostromo_crt_program);
    glDeleteShader(vertex);glDeleteShader(fragment);
    GLint ok=0;glGetProgramiv(nostromo_crt_program,GL_LINK_STATUS,&ok);
    if(!ok){glDeleteProgram(nostromo_crt_program);nostromo_crt_program=0;return false;}
    const GLfloat vertices[]={-1,-1, 1,-1, -1,1, 1,1};
    glGenBuffers(1,&nostromo_crt_vertices);glBindBuffer(GL_ARRAY_BUFFER,nostromo_crt_vertices);
    glBufferData(GL_ARRAY_BUFFER,sizeof vertices,vertices,GL_STATIC_DRAW);
    return true;
}
static bool nostromo_crt_draw(Monitor *m,struct wlr_output_state *state) {
    struct NostromoCRT *output=nostromo_crt_find(m);
    struct NostromoEGL saved;
    if(!output || !state->buffer || !nostromo_egl_begin(&saved))return false;
    bool ok=false;
    GLint framebuffer,program,array,active,texture,viewport[4],size,type,stride,normalized,enabled,attribute_buffer;
    GLboolean mask[4];void *pointer;
    const GLenum capabilities[]={GL_BLEND,GL_SCISSOR_TEST,GL_DEPTH_TEST,GL_CULL_FACE,GL_STENCIL_TEST};
    GLboolean capabilities_before[LENGTH(capabilities)];
    glGetIntegerv(GL_FRAMEBUFFER_BINDING,&framebuffer);glGetIntegerv(GL_CURRENT_PROGRAM,&program);
    glGetIntegerv(GL_ARRAY_BUFFER_BINDING,&array);glGetIntegerv(GL_ACTIVE_TEXTURE,&active);
    glActiveTexture(GL_TEXTURE0);glGetIntegerv(GL_TEXTURE_BINDING_2D,&texture);
    glGetIntegerv(GL_VIEWPORT,viewport);glGetBooleanv(GL_COLOR_WRITEMASK,mask);
    glGetVertexAttribiv(0,GL_VERTEX_ATTRIB_ARRAY_SIZE,&size);glGetVertexAttribiv(0,GL_VERTEX_ATTRIB_ARRAY_TYPE,&type);
    glGetVertexAttribiv(0,GL_VERTEX_ATTRIB_ARRAY_STRIDE,&stride);glGetVertexAttribiv(0,GL_VERTEX_ATTRIB_ARRAY_NORMALIZED,&normalized);
    glGetVertexAttribiv(0,GL_VERTEX_ATTRIB_ARRAY_ENABLED,&enabled);
    glGetVertexAttribiv(0,GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING,&attribute_buffer);
    glGetVertexAttribPointerv(0,GL_VERTEX_ATTRIB_ARRAY_POINTER,&pointer);
    for(size_t i=0;i<LENGTH(capabilities);i++){capabilities_before[i]=glIsEnabled(capabilities[i]);glDisable(capabilities[i]);}
    /* A lost context must not turn error draining into an infinite loop. */
    for(unsigned int errors=0;glGetError()!=GL_NO_ERROR;errors++)if(errors==15)goto restore;
    GLuint fbo=wlr_gles2_renderer_get_buffer_fbo(drw,state->buffer);
    GLint maximum;glGetIntegerv(GL_MAX_TEXTURE_SIZE,&maximum);
    int width=state->buffer->width,height=state->buffer->height;
    if(!fbo || width<=0 || height<=0 || width>maximum || height>maximum || !nostromo_crt_init_program())goto restore;
    glBindFramebuffer(GL_FRAMEBUFFER,fbo);
    if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)goto restore;
    if(!output->texture)glGenTextures(1,&output->texture);
    glBindTexture(GL_TEXTURE_2D,output->texture);
    if(width!=output->width || height!=output->height) {
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);
        output->width=width;output->height=height;
    }
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
    glCopyTexSubImage2D(GL_TEXTURE_2D,0,0,0,0,0,width,height);
    if(glGetError()!=GL_NO_ERROR)goto restore;
    struct timespec now;clock_gettime(CLOCK_MONOTONIC,&now);
    double time=(now.tv_sec%340)*1000.0+now.tv_nsec/1000000.0;
    float phase=nostromo_crt_mode==2?(float)((int)(time/83.0)*0.083):0.0f;
    glViewport(0,0,width,height);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);
    glUseProgram(nostromo_crt_program);
    glUniform1i(glGetUniformLocation(nostromo_crt_program,"image"),0);
    glUniform2f(glGetUniformLocation(nostromo_crt_program,"resolution"),(float)width,(float)height);
    glUniform1f(glGetUniformLocation(nostromo_crt_program,"phase"),phase);
    glUniform1f(glGetUniformLocation(nostromo_crt_program,"motion"),nostromo_crt_mode==2?1.0f:0.0f);
    glBindBuffer(GL_ARRAY_BUFFER,nostromo_crt_vertices);
    glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,0,NULL);glEnableVertexAttribArray(0);
    glDrawArrays(GL_TRIANGLE_STRIP,0,4);
    /* An earlier explicit scene fence cannot cover later custom GL work. */
    if(state->wait_timeline)glFinish();else glFlush();
    ok=glGetError()==GL_NO_ERROR;
restore:
    glBindBuffer(GL_ARRAY_BUFFER,attribute_buffer);glVertexAttribPointer(0,size,(GLenum)type,(GLboolean)normalized,stride,pointer);
    if(enabled)glEnableVertexAttribArray(0);else glDisableVertexAttribArray(0);
    glBindBuffer(GL_ARRAY_BUFFER,array);glUseProgram(program);glBindTexture(GL_TEXTURE_2D,texture);glActiveTexture(active);
    glBindFramebuffer(GL_FRAMEBUFFER,framebuffer);glViewport(viewport[0],viewport[1],viewport[2],viewport[3]);
    glColorMask(mask[0],mask[1],mask[2],mask[3]);
    for(size_t i=0;i<LENGTH(capabilities);i++)if(capabilities_before[i])glEnable(capabilities[i]);
    nostromo_egl_end(&saved);
    return ok;
}
static bool nostromo_crt_commit(Monitor *m) {
    /* Apply before every scene commit, including CRT-off and newly mapped
     * subsurfaces/popups. Unchanged opacity causes no damage or new timer. */
    nostromo_animate_tick();
    if(!nostromo_crt_mode)return wlr_scene_output_commit(m->scene_output,NULL);
    /* Repaint the clean scene before processing: never compound the previous CRT frame. */
    wlr_damage_ring_add_whole(&m->scene_output->damage_ring);
    struct wlr_output_state state;wlr_output_state_init(&state);
    bool ok=wlr_scene_output_build_state(m->scene_output,&state,NULL);
    if(ok && !nostromo_crt_draw(m,&state)) {
        fprintf(stderr,"CRT rendering failed; returning to normal composition\n");
        nostromo_crt_set(0);ok=false;
    }
    if(ok)ok=wlr_output_commit_state(m->wlr_output,&state);
    wlr_output_state_finish(&state);
    if(!ok){wlr_damage_ring_add_whole(&m->scene_output->damage_ring);wlr_output_schedule_frame(m->wlr_output);}
    return ok;
}
static void nostromo_control_state(struct wl_client *client,struct wl_resource *resource) {
    nostromo_control_v1_send_state(resource,nostromo_crt_mode,locked?(cur_lock?1:2):0);
}
static void nostromo_control_effect(struct wl_client *client,struct wl_resource *resource,uint32_t mode) {
    if(mode>2){wl_resource_post_error(resource,0,"Invalid effect mode");return;}
    nostromo_crt_set(mode);nostromo_control_state(client,resource);
}
static void nostromo_control_destroy(struct wl_client *client,struct wl_resource *resource) {wl_resource_destroy(resource);}
static const struct nostromo_control_v1_interface nostromo_control_impl={
    .destroy=nostromo_control_destroy,.get_state=nostromo_control_state,.set_effect=nostromo_control_effect,
};
static void nostromo_control_bind(struct wl_client *client,void *data,uint32_t version,uint32_t id) {
    struct wl_resource *resource=wl_resource_create(client,&nostromo_control_v1_interface,1,id);
    if(!resource){wl_client_post_no_memory(client);return;}
    wl_resource_set_implementation(resource,&nostromo_control_impl,NULL,NULL);
}
static void nostromo_crt_setup(void) {
    wl_list_init(&nostromo_crt_outputs);
    nostromo_crt_timer=wl_event_loop_add_timer(event_loop,nostromo_crt_tick,NULL);
    if(!nostromo_crt_timer || !wl_global_create(dpy,&nostromo_control_v1_interface,1,NULL,nostromo_control_bind))
        die("Could not create native session control");
}
