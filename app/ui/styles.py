APP_STYLE = """
QMainWindow {
    background-color: #f3f4f6;
}

#menuLateral {
    background-color: #111827;
}

#tituloMenu {
    color: white;
    font-size: 24px;
    font-weight: bold;
}

#subtituloMenu {
    color: #9ca3af;
    font-size: 12px;
}

QPushButton {
    background-color: #1f2937;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px;
    text-align: left;
    font-size: 15px;
}

QPushButton:hover {
    background-color: #374151;
}

QPushButton:pressed {
    background-color: #2563eb;
}

#tituloPagina {
    color: #111827;
    font-size: 30px;
    font-weight: bold;
}

#subtituloPagina {
    color: #6b7280;
    font-size: 15px;
}

#card {
    background-color: white;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
}

#cardTitulo {
    color: #6b7280;
    font-size: 13px;
}

#cardValor {
    color: #111827;
    font-size: 24px;
    font-weight: bold;
}

#seccionTitulo {
    color: #111827;
    font-size: 18px;
    font-weight: bold;
}

QTableWidget {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    gridline-color: #e5e7eb;
    font-size: 13px;
}

QHeaderView::section {
    background-color: #f9fafb;
    color: #374151;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    font-weight: bold;
}

QTableWidget::item {
    padding: 8px;
}

#botonPrincipal {
    background-color: #2563eb;
    color: white;
    font-weight: bold;
    text-align: center;
}

#botonPrincipal:hover {
    background-color: #1d4ed8;
}

QScrollArea#scrollPagina {
    background-color: #f3f4f6;
    border: none;
}

QScrollArea#scrollPagina > QWidget > QWidget {
    background-color: #f3f4f6;
}

QScrollBar:vertical {
    background-color: #f3f4f6;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-height: 32px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}
"""