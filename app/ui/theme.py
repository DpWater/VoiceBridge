APP_STYLE = """
QWidget { background: #0b1020; color: #f4f7ff; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif; font-size: 13px; }
QMainWindow, QDialog { background: #0b1020; }
QFrame#topBar { background: #10182a; border-bottom: 1px solid #263350; }
QFrame#card, QFrame#routeCard, QFrame#contextCard { background: #121c31; border: 1px solid #2a3858; border-radius: 14px; }
QLabel#brand { font-size: 19px; font-weight: 700; color: #f5f7ff; }
QLabel#eyebrow { color: #22d3ee; font-size: 12px; font-weight: 700; }
QLabel#headline { font-size: 25px; font-weight: 700; color: #f4f7ff; }
QLabel#subtitle, QLabel#muted, QLabel#targetStatus { color: #9aaccc; }
QLabel#statusChip { background: #143e3a; color: #b7ffdf; border-radius: 10px; padding: 6px 10px; }
QLabel#sectionTitle { color: #dce7fc; font-weight: 700; font-size: 14px; }
QLabel#targetName { color: #f4f7ff; font-weight: 700; font-size: 15px; }
QLabel#capability { background: #1d3150; color: #c7d6f1; border-radius: 9px; padding: 4px 7px; font-size: 11px; }
QLabel#capabilityActive { background: #153d39; color: #b9ffe8; border-radius: 9px; padding: 4px 7px; font-size: 11px; }
QFrame#floatingFeedback { background: #142138; border: 1px solid #3b5879; border-radius: 14px; }
QLabel#feedbackIcon { color: #67f0bd; font-size: 18px; font-weight: 700; }
QLabel#feedbackTitle { color: #f2f7ff; font-size: 13px; font-weight: 700; }
QLabel#feedbackElapsed { color: #a8b9d2; font-size: 12px; }
QLabel#feedbackDetail { color: #9eafca; font-size: 11px; }
QProgressBar#feedbackProgress { height: 3px; border: 0; border-radius: 1px; background: #20314d; }
QProgressBar#feedbackProgress::chunk { border-radius: 1px; background: #59e1be; }
QDialog#pasteBubble { background: transparent; }
QFrame#pasteBubbleCard { background: #152239; border: 1px solid #50688e; border-radius: 17px; }
QLabel#pasteBadge { min-width: 22px; min-height: 22px; padding: 1px; border-radius: 7px; color: #241b48; background: #aa95ff; font-size: 14px; font-weight: 700; }
QLabel#pasteTitle { color: #f1f5ff; font-size: 12px; font-weight: 700; }
QLabel#pasteEditable { color: #97d9bd; font-size: 11px; }
QLabel#pasteHint { color: #91a5c4; font-size: 10px; }
QPushButton#pasteCancel { padding: 6px 9px; border-color: transparent; color: #9fb1cc; background: transparent; }
QPushButton#pasteCancel:hover { color: #eef5ff; background: #25344e; }
QPushButton { border: 1px solid #405171; border-radius: 9px; padding: 9px 13px; color: #e3ebfc; background: #18243c; font-weight: 600; }
QPushButton:hover { background: #223252; border-color: #58709c; }
QPushButton#primary { border: 0; background: #7051e8; color: white; min-height: 22px; }
QPushButton#primary:hover { background: #815ff5; }
QPushButton#record { border: 0; background: #12a98a; color: white; min-height: 26px; font-size: 14px; }
QPushButton#record:hover { background: #1fc2a1; }
QComboBox, QTextEdit, QPlainTextEdit, QKeySequenceEdit { background: #0b1222; color: #eef4ff; border: 1px solid #344463; border-radius: 9px; padding: 8px; }
QComboBox::drop-down { border: 0; width: 24px; }
QComboBox QAbstractItemView { background: #131e34; color: #eff4ff; selection-background-color: #354c7b; }
QTextEdit, QPlainTextEdit { selection-background-color: #6049c6; }
QTabWidget::pane { border: 1px solid #2a3858; border-radius: 10px; top: -1px; }
QTabBar::tab { background: #151f35; color: #9aaccc; padding: 8px 12px; border: 1px solid #2a3858; border-bottom: 0; }
QTabBar::tab:selected { color: #f4f7ff; background: #202d49; }
QCheckBox { color: #dce7fc; spacing: 8px; }
"""
