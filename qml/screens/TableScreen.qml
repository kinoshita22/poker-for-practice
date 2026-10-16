import QtQuick
import QtQuick.Layouts
import PokerPractice.Bridge
import "../components"

// The poker table. Everything shown here comes from the Game bridge.
Rectangle {
    id: root

    property bool animated: true

    signal backRequested()
    signal actionRequested(string kind, int amount, int step)

    color: Theme.background

    // ---------------------------------------------------------------- top bar
    Rectangle {
        id: topBar
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: Theme.topBarHeight
        color: Theme.backgroundRaised
        z: 2

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Theme.spacing
            anchors.rightMargin: Theme.spacing
            spacing: Theme.spacingLarge

            ToolbarButton {
                objectName: "backButton"
                text: "‹  Menu"
                onClicked: root.backRequested()
            }
            Text {
                objectName: "handInfo"
                visible: Game.handNumber > 0
                text: "Hand #" + Game.handNumber + "   ·   Blinds "
                      + Theme.formatChips(Game.smallBlind) + " / " + Theme.formatChips(Game.bigBlind)
                font.family: Theme.fontBody
                font.pixelSize: Theme.fontSizeBody - 1
                color: Theme.textSecondary
            }
            Text {
                objectName: "tableMessage"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: Game.message
                elide: Text.ElideRight
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fontSizeLarge - 2
                color: Theme.goldBright
            }
            // Balances the left side so the message stays centred.
            Item { Layout.preferredWidth: 160 }
        }

        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 1
            color: Theme.divider
        }
    }

    // ------------------------------------------------------------- table area
    Item {
        id: area
        objectName: "tableArea"
        anchors {
            left: parent.left; right: parent.right
            top: topBar.bottom; bottom: actionPanel.top
        }

        readonly property real aspect: 2.05
        readonly property real tableWidth: Math.min(width * 0.8, height * 0.7 * aspect)
        readonly property real tableHeight: tableWidth / aspect
        readonly property real tableX: (width - tableWidth) / 2
        readonly property real tableY: (height - tableHeight) / 2 - height * 0.01
        // Size unit for seats, cards and chips.
        readonly property real unit: Math.max(52, Math.min(104, tableWidth / 12))

        // Positions relative to the table rectangle, indexed by display slot
        // (0 = human at the bottom, then clockwise).
        readonly property var seatPoints: [[0.5, 1.04], [0.1, 0.82], [0.1, 0.22], [0.5, 0.03], [0.9, 0.22], [0.9, 0.82]]
        readonly property var betPoints: [[0.5, 0.69], [0.25, 0.68], [0.25, 0.32], [0.62, 0.21], [0.75, 0.32], [0.75, 0.68]]
        readonly property var markerPoints: [[0.39, 0.71], [0.18, 0.6], [0.18, 0.4], [0.39, 0.19], [0.82, 0.4], [0.82, 0.6]]

        function px(point) { return tableX + point[0] * tableWidth }
        function py(point) { return tableY + point[1] * tableHeight }

        PokerTable {
            id: table
            objectName: "pokerTable"
            x: area.tableX
            y: area.tableY
            width: area.tableWidth
            height: area.tableHeight
        }

        PotDisplay {
            objectName: "potDisplay"
            anchors.horizontalCenter: parent.horizontalCenter
            y: area.py([0, 0.38]) - height
            pots: Game.pots
            totalPot: Game.totalPot
            chipWidth: area.unit * 0.36
            animated: root.animated
        }

        BoardCards {
            id: board
            objectName: "boardCards"
            cardWidth: area.unit * 0.86
            anchors.horizontalCenter: parent.horizontalCenter
            y: area.py([0, 0.5]) - height / 2
            cards: Game.board
            highlightCards: Game.winningCards
            animated: root.animated
        }

        // Bets and position markers, one set per seat.
        Repeater {
            model: Game.players
            Item {
                id: furniture
                required property int slot
                required property int bet
                required property bool isDealer
                required property bool isSmallBlind
                required property bool isBigBlind
                anchors.fill: parent

                BetDisplay {
                    objectName: "bet" + furniture.slot
                    amount: furniture.bet
                    chipWidth: area.unit * 0.32
                    animated: root.animated
                    x: area.px(area.betPoints[furniture.slot]) - width / 2
                    y: area.py(area.betPoints[furniture.slot]) - height / 2
                }
                Row {
                    spacing: 3
                    x: area.px(area.markerPoints[furniture.slot]) - width / 2
                    y: area.py(area.markerPoints[furniture.slot]) - height / 2
                    PositionMarker { kind: "D"; size: area.unit * 0.32; visible: furniture.isDealer }
                    PositionMarker { kind: "SB"; size: area.unit * 0.28; visible: furniture.isSmallBlind }
                    PositionMarker { kind: "BB"; size: area.unit * 0.28; visible: furniture.isBigBlind }
                }
            }
        }

        Repeater {
            objectName: "seatRepeater"
            model: Game.players
            PlayerSeat {
                // Existing PlayerSeat properties filled from model roles.
                required name
                required stack
                required cards
                required folded
                required allIn
                required busted
                required isHuman
                required toAct
                required lastAction
                required isWinner
                required wonAmount
                required handLabel
                required bestCards
                required property int slot
                required property string style

                objectName: "seat" + slot
                unit: area.unit
                playerStyle: style
                animated: root.animated
                // Centre the nameplate on the slot point.
                x: area.px(area.seatPoints[slot]) - width / 2
                y: area.py(area.seatPoints[slot]) - (height - plateHeight / 2)
                z: isHuman ? 2 : 1
            }
        }

        Text {
            anchors.centerIn: parent
            visible: !Game.sessionActive
            text: "No session in progress"
            font.family: Theme.fontBody
            font.pixelSize: Theme.fontSizeLarge
            color: Theme.textMuted
        }
    }

    ActionPanel {
        id: actionPanel
        objectName: "actionPanel"
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        actions: Game.actions
        totalPot: Game.totalPot
        bigBlind: Game.bigBlind
        onActionRequested: (kind, amount, step) => root.actionRequested(kind, amount, step)
    }

    // Keyboard shortcuts for the betting actions.
    Shortcut { sequence: "F"; enabled: actionPanel.ready; onActivated: actionPanel.fold() }
    Shortcut { sequence: "C"; enabled: actionPanel.ready; onActivated: actionPanel.checkOrCall() }
    Shortcut { sequence: "R"; enabled: actionPanel.canSize; onActivated: actionPanel.betOrRaise() }
    Shortcut { sequence: "A"; enabled: actionPanel.ready; onActivated: actionPanel.allIn() }
}
