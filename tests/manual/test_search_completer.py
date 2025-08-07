#!/usr/bin/env python3
"""
Simple test script to verify QCompleter functionality
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QCompleter
from PySide6.QtCore import QStringListModel, Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Search Completer Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入 A 测试自动完成...")
        layout.addWidget(self.search_input)
        
        # Setup completer
        self.setup_completer()
    
    def setup_completer(self):
        # Create sample hole IDs (like AC001R001, AC002R001, etc.)
        hole_ids = []
        for i in range(1, 101):
            hole_ids.append(f"AC{i:03d}R001")
            hole_ids.append(f"BC{i:03d}R001")
        
        print(f"Created {len(hole_ids)} test hole IDs")
        print(f"Sample: {hole_ids[:5]}")
        
        # Create completer
        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)  
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setMaxVisibleItems(10)
        
        # Set model
        model = QStringListModel(hole_ids)
        completer.setModel(model)
        
        # Apply to input
        self.search_input.setCompleter(completer)
        
        # Style popup
        popup = completer.popup()
        popup.setStyleSheet("QListView { border: 1px solid gray; background-color: white; }")
        
        print("Completer setup完成")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("Type 'A' in the search box to test autocomplete")
    sys.exit(app.exec())