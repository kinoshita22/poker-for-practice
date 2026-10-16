import QtQuick
import "../components"

ScreenScaffold {
    title: "Statistics"

    Text {
        anchors.centerIn: parent
        text: "No statistics recorded yet."
        font.family: Theme.fontBody
        font.pixelSize: Theme.fontSizeBody
        color: Theme.textMuted
    }
}
