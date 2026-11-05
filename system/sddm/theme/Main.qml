import QtQuick
import QtQuick.Window 2.15

Rectangle {
    id: screen
    width: 1920; height: 1080; color: "black"
    property real unit: Math.max(0.65, Math.min(width/1920, height/1080, 2))
    property string effectMode: typeof config !== "undefined" ? config.Effects : "animated"
    property bool busy: false
    property string errorText: ""
    property real effectTime: 0
    property bool animateClock: true
    FontLoader {
        id: michroma
        source: typeof config !== "undefined" ? config.FontFile : "../../../assets/fonts/Michroma-Regular.ttf"
    }
    function authenticate() {
        if (busy || !login.text.length || !password.text.length) return;
        if (typeof sddm === "undefined") { errorText = "Preview only"; password.text = ""; return; }
        busy = true; errorText = "";
        // Dedicated SessionDir contains exactly nostromo.desktop; no remembered X session.
        sddm.login(login.text, password.text, 0);
        password.text = "";
    }
    Connections {
        target: typeof sddm !== "undefined" ? sddm : null
        function onLoginFailed() {
            screen.busy = false; password.text = "";
            screen.errorText = "Authentication failed"; password.input.forceActiveFocus();
        }
        function onInformationMessage(message) { screen.errorText = message; }
    }
    Column {
        width: Math.min(430*screen.unit, screen.width-64)
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        spacing: 30*screen.unit
        SpaceOrb {
            seconds: screen.effectTime; mode: screen.effectMode
            width: 230*screen.unit; height: width
            anchors.horizontalCenter: parent.horizontalCenter
            source: typeof config !== "undefined" ? config.LogoFile : "../../../assets/nostromo-orb.png"
        }
        Item { width: 1; height: 16*screen.unit }
        InputFrame {
            id: login
            objectName: "login"
            width: parent.width; height: 60*screen.unit; unit: screen.unit
            label: "Login"; face: michroma.name; enabled: !screen.busy
            animated: screen.effectMode === "animated"
            phase: screen.effectTime*4
            nextField: password.input
            previousField: password.input
            onAccepted: password.input.forceActiveFocus()
        }
        InputFrame {
            id: password
            objectName: "password"
            width: parent.width; height: 60*screen.unit; unit: screen.unit
            label: "Password"; face: michroma.name; secret: true; enabled: !screen.busy
            animated: screen.effectMode === "animated"
            phase: screen.effectTime*4
            nextField: login.input
            previousField: login.input
            onAccepted: screen.authenticate()
        }
        Text {
            width: parent.width; height: 32*screen.unit
            text: screen.errorText; textFormat: Text.PlainText; color: "white"
            font.family: michroma.name; font.pixelSize: 12*screen.unit
            horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
        }
    }
    SpaceDots {
        anchors.fill: parent; seconds: screen.effectTime; mode: screen.effectMode
    }
    FrameAnimation {
        running: screen.visible && screen.animateClock && screen.effectMode === "animated"
        onTriggered: {
            var step=Math.floor(elapsedTime*30)/30;
            if (step !== screen.effectTime) screen.effectTime=step;
        }
    }
    Component.onCompleted: login.input.forceActiveFocus()
}
