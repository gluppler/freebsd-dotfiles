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
import QtQuick

// Tiled textures are uploaded once. Animation changes offsets, not a full-screen Canvas.
Item {
    id: effect
    property real seconds: 0
    property string mode: "animated"
    readonly property real time: mode === "animated" ? seconds % 256 : 0
    visible: mode !== "off"
    clip: true
    Image {
        x: 0; y: (effect.time*117*6/(2*Math.PI)) % 6 - 6
        width: parent.width; height: parent.height+6
        source: "phosphor.png"; fillMode: Image.Tile
        horizontalAlignment: Image.AlignLeft; verticalAlignment: Image.AlignTop
    }
    Image {
        x: -(Math.floor(effect.time*30)*17 % 96)
        y: -(Math.floor(effect.time*30)*29 % 96)
        width: parent.width+96; height: parent.height+96
        source: "grain.png"; fillMode: Image.Tile
        horizontalAlignment: Image.AlignLeft; verticalAlignment: Image.AlignTop
    }
    Rectangle {
        anchors.fill: parent; color: "black"
        opacity: effect.mode === "animated" ? .005*(1+Math.sin(effect.time*120)) : 0
    }
}
