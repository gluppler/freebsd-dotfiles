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
// Monochrome adaptation: three samples, native output pixels, no geometry warp.
// GPU cost is bounded independently of the reference's 96-sample bloom.
precision highp float;
varying vec2 uv;
uniform sampler2D image;
uniform vec2 resolution;
uniform float phase;
uniform float motion;
float luminance(vec3 rgb) { return dot(rgb,vec3(0.2126,0.7152,0.0722)); }
float grain(vec2 xy) { return fract(sin(dot(xy,vec2(12.9898,78.233))+phase)*43758.5453); }
void main() {
    vec2 pixel=1.0/resolution;
    float center=luminance(texture2D(image,uv).rgb);
    float neighbours=luminance(texture2D(image,uv+vec2(pixel.x,0.0)).rgb)
                    +luminance(texture2D(image,uv-vec2(pixel.x,0.0)).rgb);
    float glow=max(0.0,neighbours*0.5-center)*0.045;
    float rows=1.0-0.045*(0.5+0.5*cos(gl_FragCoord.y*3.14159265));
    float dots=1.0-0.012*step(2.0,mod(gl_FragCoord.x,3.0));
    vec2 corner=uv*2.0-1.0;
    float vignette=1.0-0.045*dot(corner,corner);
    float sweep=motion*0.015*exp(-pow((uv.y-fract(phase*0.035))*22.0,2.0));
    float noise=(grain(gl_FragCoord.xy)-0.5)*0.004;
    float value=(center+glow)*rows*dots*vignette+sweep*center+noise*center;
    gl_FragColor=vec4(vec3(clamp(value,0.0,1.0)),1.0);
}
