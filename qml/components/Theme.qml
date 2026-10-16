pragma Singleton
import QtQuick

// Central palette, typography and spacing for every screen.
QtObject {
    // Surfaces
    readonly property color background: "#141414"
    readonly property color backgroundRaised: "#1d1c1a"
    readonly property color panel: "#22201d"
    readonly property color panelBorder: "#3a3530"
    readonly property color divider: "#2f2b27"

    // Table
    readonly property color felt: "#0f4d32"
    readonly property color feltDark: "#0a3824"
    readonly property color feltLight: "#16613f"
    readonly property color rail: "#1b1816"
    readonly property color railHighlight: "#3a332d"
    readonly property color railEdge: "#0c0b0a"

    // Text
    readonly property color textPrimary: "#f3ede1"
    readonly property color textSecondary: "#b9b1a3"
    readonly property color textMuted: "#7d766b"

    // Accents
    readonly property color gold: "#c8a45a"
    readonly property color goldBright: "#e2c27e"
    readonly property color goldDim: "#8c7340"
    readonly property color accentRed: "#a8382f"
    readonly property color accentGreen: "#4f9a6a"

    // Typography
    readonly property string fontDisplay: "Georgia"
    readonly property string fontBody: "Segoe UI"
    readonly property int fontSizeSmall: 12
    readonly property int fontSizeBody: 14
    readonly property int fontSizeLarge: 18
    readonly property int fontSizeTitle: 30

    // Geometry
    readonly property int spacingSmall: 6
    readonly property int spacing: 12
    readonly property int spacingLarge: 24
    readonly property int radius: 6
    readonly property int topBarHeight: 48

    // Motion
    readonly property int durationFast: 120
    readonly property int durationNormal: 220
}
