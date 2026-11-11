import QtQuick 2.15

Item {
    id: frame
    property alias text: input.text
    property alias input: input
    property string label: ""
    property string face: "Michroma"
    property bool secret: false
    property bool animated: true
    property real unit: 1
    property real phase: 0
    property Item nextField
    property Item previousField
    signal accepted()
    implicitHeight: 60 * unit

    Canvas {
        id: drawing
        anchors.fill: parent
        anchors.margins: -12 * frame.unit
        onPaint: {
            var ctx = getContext("2d"); ctx.reset();
            var pad = 12 * frame.unit, cut = 12 * frame.unit;
            var w = frame.width, h = frame.height;
            ctx.strokeStyle = "white"; ctx.lineWidth = 1.5 * frame.unit;
            ctx.beginPath(); ctx.moveTo(pad, pad); ctx.lineTo(pad+w, pad);
            ctx.lineTo(pad+w, pad+h-cut); ctx.lineTo(pad+w-cut, pad+h);
            ctx.lineTo(pad, pad+h); ctx.closePath(); ctx.stroke();
            if (!input.activeFocus) return;
            var pulse = frame.animated ? (1+Math.sin(frame.phase))/2 : 1;
            var gap = (7+2*pulse)*frame.unit, arm = 28*frame.unit;
            ctx.globalAlpha = 0.6 + 0.4*pulse; ctx.lineWidth = 2.5*frame.unit;
            ctx.beginPath(); ctx.moveTo(pad-gap+arm, pad-gap);
            ctx.lineTo(pad-gap, pad-gap); ctx.lineTo(pad-gap, pad+h+gap);
            ctx.lineTo(pad-gap+arm, pad+h+gap); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(pad+w+gap-arm, pad-gap);
            ctx.lineTo(pad+w+gap, pad-gap); ctx.lineTo(pad+w+gap, pad+h+gap-cut);
            ctx.lineTo(pad+w+gap-cut, pad+h+gap); ctx.lineTo(pad+w+gap-arm, pad+h+gap);
            ctx.stroke();
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
    TextInput {
        id: input
        anchors.fill: parent
        anchors.leftMargin: 18*frame.unit; anchors.rightMargin: 24*frame.unit
        color: "white"; selectionColor: "white"; selectedTextColor: "black"
        font.family: frame.face; font.pixelSize: 18*frame.unit
        verticalAlignment: TextInput.AlignVCenter
        echoMode: frame.secret ? TextInput.Password : TextInput.Normal
        passwordCharacter: "●"
        inputMethodHints: frame.secret ? Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoPredictiveText : Qt.ImhNoPredictiveText
        maximumLength: frame.secret ? 1024 : 64
        selectByMouse: true; clip: true
        Accessible.name: frame.label
        KeyNavigation.tab: frame.nextField
        KeyNavigation.backtab: frame.previousField
        onActiveFocusChanged: drawing.requestPaint()
        onAccepted: frame.accepted()
    }
    Text {
        anchors.fill: input
        color: "#aaa"; text: frame.label; visible: !input.text.length
        font: input.font; verticalAlignment: Text.AlignVCenter
    }
    onPhaseChanged: drawing.requestPaint()
    onAnimatedChanged: drawing.requestPaint()
}
