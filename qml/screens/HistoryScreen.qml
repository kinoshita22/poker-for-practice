import QtQuick
import "../components"

ScreenScaffold {
    title: "Hand History"

    Text {
        anchors.centerIn: parent
        text: "No hands recorded yet."
        font.family: Theme.fontBody
        font.pixelSize: Theme.fontSizeBody
        color: Theme.textMuted
    }
}
