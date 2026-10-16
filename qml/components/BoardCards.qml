import QtQuick

// Five community-card positions. Empty positions show a faint outline.
Row {
    id: root

    property var cards: []  // up to five card codes
    property var highlightCards: []
    property real cardWidth: 70
    property bool animated: true

    spacing: cardWidth * 0.12

    Repeater {
        model: 5
        Item {
            width: root.cardWidth
            height: width * 88 / 63

            Rectangle {
                anchors.fill: parent
                radius: width * 34 / 630
                color: Qt.rgba(0, 0, 0, 0.12)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.12)
            }

            PlayingCard {
                objectName: "boardCard" + index
                readonly property string code: index < root.cards.length ? root.cards[index] : ""
                anchors.fill: parent
                visible: code !== ""
                card: code
                highlighted: code !== "" && root.highlightCards.indexOf(code) >= 0
                animated: root.animated
                onCodeChanged: if (code !== "") dealFrom(0, -height * 0.6, index >= 3 ? 0 : index * 90)
            }
        }
    }
}
