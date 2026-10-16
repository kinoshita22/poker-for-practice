import QtQuick
import "../components"

ScreenScaffold {
    title: "Settings"

    Text {
        anchors.centerIn: parent
        text: "Settings become available once persistence is implemented."
        font.family: Theme.fontBody
        font.pixelSize: Theme.fontSizeBody
        color: Theme.textMuted
    }
}
