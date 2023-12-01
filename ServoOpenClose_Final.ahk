CoordMode, Mouse, Screen

HotkeysEnabled := true

^8:: ; Ctrl+8
    if (HotkeysEnabled)
        ClickAction(1716, 249)
    return

^9:: ; Ctrl+9
    if (HotkeysEnabled)
        ClickAction(1818, 249)
    return

^Esc:: ; Ctrl+Esc^Esc:: ; Ctrl+Esc
    ExitApp

q:: ; Q key
    if (HotkeysEnabled)
        ClickAction(754, 264, "DoubleClick")
    return

w:: ; W key
    if (HotkeysEnabled)
        ClickAction(621, 759)
    return

e:: ; E key
    if (HotkeysEnabled)
        ClickAction(753, 759)
    return

ClickAction(x, y, action := "Click") {
    MouseMove, %x%, %y%, 0
    if (action = "DoubleClick")
        Click
    else
        Click
}
