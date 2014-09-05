from rezgui.qt import QtCore, QtGui
from rez.util import readable_time_duration
from rez.resolved_context import PatchLock
from functools import partial
import os.path
import time


def create_pane(widgets, horizontal, parent_widget=None, compact=False,
                compact_spacing=2):
    """Create a widget containing an aligned set of widgets.

    Args:
        widgets (list of `QWidget`).
        horizontal (bool).
        align (str): One of:
            - 'left', 'right' (horizontal);
            - 'top', 'bottom' (vertical)
        parent_widget (`QWidget`): Owner widget, QWidget is created if this
            is not provided.

    Returns:
        `QWidget`
    """
    pane = parent_widget or QtGui.QWidget()
    type_ = QtGui.QHBoxLayout if horizontal else QtGui.QVBoxLayout
    layout = type_()
    if compact:
        layout.setSpacing(compact_spacing)
        layout.setContentsMargins(compact_spacing, compact_spacing,
                                  compact_spacing, compact_spacing)

    for widget in widgets:
        stretch = 0
        if isinstance(widget, tuple):
            widget, stretch = widget

        if isinstance(widget, int):
            layout.addSpacing(widget)
        elif widget:
            layout.addWidget(widget, stretch)
        else:
            layout.addStretch()

    pane.setLayout(layout)
    return pane


icons = {}


def get_icon(name, as_qicon=False):
    """Returns a `QPixmap` containing the given image, or a QIcon if `as_qicon`
    is True"""
    filename = name + ".png"
    icon = icons.get(filename)
    if not icon:
        path = os.path.dirname(__file__)
        path = os.path.join(path, "icons")
        filepath = os.path.join(path, filename)
        if not os.path.exists(filepath):
            filepath = os.path.join(path, "pink.png")

        icon = QtGui.QPixmap(filepath)
        icons[filename] = icon

    return QtGui.QIcon(icon) if as_qicon else icon


def get_icon_widget(filename, tooltip=None):
    icon = get_icon(filename)
    icon_label = QtGui.QLabel()
    icon_label.setPixmap(icon)
    if tooltip:
        icon_label.setToolTip(tooltip)
    return icon_label


def get_timestamp_str(timestamp):
    now = int(time.time())
    release_time = time.localtime(timestamp)
    release_time_str = time.strftime('%d %b %Y %H:%M:%S', release_time)
    ago = readable_time_duration(now - timestamp)
    return "%s (%s ago)" % (release_time_str, ago)


def add_menu_action(menu, label, slot, icon_name=None, group=None):
    nargs = [label, menu]
    if icon_name:
        icon = get_icon(icon_name, as_qicon=True)
        nargs.insert(0, icon)
    action = QtGui.QAction(*nargs)
    action.triggered.connect(slot)
    if group:
        action.setCheckable(True)
        group.addAction(action)
    menu.addAction(action)
    return action


def create_toolbutton(entries, parent=None):
    """Create a toolbutton.

    Args:
        entries: List of (label, slot) tuples.

    Returns:
        `QtGui.QToolBar`.
    """
    btn = QtGui.QToolButton(parent)
    menu = QtGui.QMenu()
    actions = []

    for label, slot in entries:
        action = add_menu_action(menu, label, slot)
        actions.append(action)

    btn.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
    btn.setDefaultAction(actions[0])
    btn.setMenu(menu)
    return btn, actions


def add_locking_submenu(menu, slot):
    group = QtGui.QActionGroup(menu)
    lock_menu = menu.addMenu("Lock To...")
    actions = {}

    for lock_type in PatchLock:
        fn = partial(slot, lock_type)
        action = add_menu_action(lock_menu, lock_type.description, fn,
                                 lock_type.name, group)
        actions[lock_type] = action

    return lock_menu, actions


def update_font(widget, italic=None, bold=None):
    font = widget.font()
    if italic is not None:
        font.setItalic(italic)
    if bold is not None:
        font.setBold(bold)
    widget.setFont(font)