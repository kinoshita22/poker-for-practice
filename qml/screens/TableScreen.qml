import QtQuick
import QtQuick.Layouts
import "../components"

// Poker table screen. Phase 1: layout frame (top bar, table surface, action area).
Rectangle {
    id: root

    signal backRequested()

    color: Theme.background

    Rectangle {
        id: topBar
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: Theme.topBarHeight
        color: Theme.backgroundRaised

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Theme.spacing
            anchors.rightMargin: Theme.spacing
            spacing: Theme.spacing

            ToolbarButton {
                objectName: "backButton"
                text: "‹  Menu"
                onClicked: root.backRequested()
            }
            Item { Layout.fillWidth: true }
        }

        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 1
            color: Theme.divider
        }
    }

    Item {
        id: tableArea
        anchors {
            left: parent.left; right: parent.right
            top: topBar.bottom; bottom: actionArea.top
            margins: Theme.spacingLarge
        }

        // Stadium-shaped table with a 2.1:1 aspect ratio, as large as fits.
        readonly property real aspect: 2.1
        readonly property real tableWidth: Math.min(width, height * aspect)

        Rectangle {
            id: rail
            objectName: "tableRail"
            anchors.centerIn: parent
            width: tableArea.tableWidth
            height: width / tableArea.aspect
            radius: height / 2
            color: Theme.rail
            border.width: 2
            border.color: Theme.railEdge

            Rectangle {
                id: felt
                anchors.fill: parent
                anchors.margins: Math.max(14, rail.height * 0.075)
                radius: height / 2
                border.width: 1
                border.color: Theme.railHighlight
                gradient: Gradient {
                    GradientStop { position: 0.0; color: Theme.feltLight }
                    GradientStop { position: 0.55; color: Theme.felt }
                    GradientStop { position: 1.0; color: Theme.feltDark }
                }
            }
        }
    }

    Rectangle {
        id: actionArea
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 96
        color: Theme.backgroundRaised

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 1
            color: Theme.divider
        }

        Text {
            anchors.centerIn: parent
            text: "Gameplay controls will appear here."
            font.family: Theme.fontBody
            font.pixelSize: Theme.fontSizeBody
            color: Theme.textMuted
        }
    }
}
