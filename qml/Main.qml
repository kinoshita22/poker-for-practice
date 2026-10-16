import QtQuick
import QtQuick.Controls.Basic
import PokerPractice.Bridge
import "components"
import "screens"

ApplicationWindow {
    id: window
    objectName: "mainWindow"

    width: 1280
    height: 800
    minimumWidth: 1024
    minimumHeight: 640
    visible: true
    title: App.name
    color: Theme.background

    // Name of the screen on top of the stack, for navigation and tests.
    property string currentScreen: "menu"

    function showScreen(name) {
        if (name === currentScreen)
            return
        const component = {
            "table": tableScreen,
            "statistics": statisticsScreen,
            "history": historyScreen,
            "settings": settingsScreen,
            "setup": setupScreen,
            "gallery": galleryScreen
        }[name]
        if (name === "menu") {
            stack.pop(null)
        } else if (component) {
            stack.pop(null, StackView.Immediate)
            stack.push(component)
        } else {
            console.warn("Unknown screen", name)
            return
        }
        currentScreen = name
    }

    StackView {
        id: stack
        objectName: "screenStack"
        anchors.fill: parent

        initialItem: MainMenuScreen {
            onPlayRequested: window.showScreen(Game.sessionActive ? "table" : "setup")
            onNewSessionRequested: window.showScreen("setup")
            onStatisticsRequested: window.showScreen("statistics")
            onHistoryRequested: window.showScreen("history")
            onSettingsRequested: window.showScreen("settings")
        }

        pushEnter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.durationNormal }
        }
        pushExit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.durationNormal }
        }
        popEnter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.durationNormal }
        }
        popExit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.durationNormal }
        }
    }

    Component {
        id: tableScreen
        TableScreen {
            onBackRequested: window.showScreen("menu")
            onActionRequested: (kind, amount, step) => Game.submitAction(kind, amount, step)
            animated: App.animationsEnabled
            onDealRequested: Game.deal()
            onNewSessionRequested: window.showScreen("setup")
            onSessionEnded: window.showScreen("menu")
        }
    }
    Component { id: statisticsScreen; StatisticsScreen { onBackRequested: window.showScreen("menu") } }
    Component { id: historyScreen; HistoryScreen { onBackRequested: window.showScreen("menu") } }
    Component { id: settingsScreen; SettingsScreen { onBackRequested: window.showScreen("menu") } }
    Component {
        id: setupScreen
        SessionSetupScreen {
            onBackRequested: window.showScreen("menu")
            onStartRequested: config => {
                if (Game.startSession(config))
                    window.showScreen("table")
            }
        }
    }
    Component { id: galleryScreen; GalleryScreen { onBackRequested: window.showScreen("menu") } }

    // Developer shortcut to the card/chip gallery.
    Shortcut {
        sequence: "Ctrl+Shift+G"
        onActivated: window.showScreen("gallery")
    }
}
