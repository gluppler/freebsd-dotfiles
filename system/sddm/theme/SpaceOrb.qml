import QtQuick
import QtQuick.Window

Item {
    id: orb
    property url source
    property real seconds: 0
    property string mode: "animated"
    function enter(t) {
        var x=Math.max(0,Math.min(1,t/1.2)),lo=0,hi=1,u=0;
        if (x >= 1) return 1;
        for (var i=0;i<16;i++) {
            u=(lo+hi)/2;
            var v=1-u,bx=3*v*v*u*.1+3*v*u*u*.1+u*u*u;
            if (bx<x) lo=u; else hi=u;
        }
        v=1-u;
        return 3*v*v*u*1.1+3*v*u*u*1.1+u*u*u;
    }
    readonly property real arrival: mode === "animated" ? enter(seconds) : 1
    readonly property real phase: mode === "animated" ? Math.floor(seconds*30)/30 : 0
    Item {
        anchors.fill: parent
        scale: .92+.08*orb.arrival
        opacity: orb.mode === "animated" ? Math.max(0,Math.min(1,orb.seconds/.18)) : 1
        transform: Translate {
            x: orb.mode === "animated" ? .45*Math.sin(orb.phase*17)*Math.sin(orb.phase*3) : 0
            y: 12*(1-orb.arrival)
        }
        Repeater {
            model: orb.mode === "off" ? 0 : 4
            Image {
                required property int index
                x: index === 0 ? -2 : index === 1 ? 2 : 0
                y: index === 2 ? -2 : index === 3 ? 2 : 0
                width: orb.width; height: orb.height; opacity: .1
                source: orb.source; fillMode: Image.PreserveAspectFit
                sourceSize.width: width*Screen.devicePixelRatio
                sourceSize.height: height*Screen.devicePixelRatio
            }
        }
        Image {
            anchors.fill: parent; source: orb.source; fillMode: Image.PreserveAspectFit
            sourceSize.width: width*Screen.devicePixelRatio
            sourceSize.height: height*Screen.devicePixelRatio
        }
    }
}
