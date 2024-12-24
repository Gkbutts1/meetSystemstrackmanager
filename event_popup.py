from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QWidget, QGroupBox, QGridLayout
)


class EventSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Event Selector")
        self.setGeometry(100, 100, 600, 400)

        # Main layout
        main_layout = QVBoxLayout()

        # Division and Gender dropdowns
        dropdown_layout = QHBoxLayout()

        self.division_label = QLabel("Division")
        self.division_dropdown = QComboBox()
        self.division_dropdown.addItems(["8 and under", "9-10", "11-12", "13-14", "15-16", "17-18"])

        self.gender_label = QLabel("Gender")
        self.gender_dropdown = QComboBox()
        self.gender_dropdown.addItems(["Male", "Female"])

        dropdown_layout.addWidget(self.division_label)
        dropdown_layout.addWidget(self.division_dropdown)
        dropdown_layout.addWidget(self.gender_label)
        dropdown_layout.addWidget(self.gender_dropdown)

        main_layout.addLayout(dropdown_layout)

        # Event categories
        event_layout = QGridLayout()

        self.run_group = self.create_event_group("Run",
                                                 ["100 Meter", "200 Meter", "400 Meter", "800 Meter", "1500 Meter",
                                                  "3000 Meter", "5000 Meter"])
        self.jump_group = self.create_event_group("Jumps", ["High Jump", "Long Jump", "Pole Vault", "Triple Jump"])
        self.throw_group = self.create_event_group("Throws", ["Javelin", "Shot Put", "Discus Throw", "Hammer Throw"])
        self.multi_event_group = self.create_event_group("Multi Events", ["Decathlon", "Heptathlon", "Pentathlon"])
        self.relay_event_group = self.create_event_group("Relay Events", ["Decathlon", "Heptathlon", "Pentathlon"])

        event_layout.addWidget(self.run_group, 0, 0)
        event_layout.addWidget(self.jump_group, 0, 1)
        event_layout.addWidget(self.throw_group, 1, 0)
        event_layout.addWidget(self.multi_event_group, 1, 1)
        event_layout.addWidget(self.relay_event_group, 2, 0)

        main_layout.addLayout(event_layout)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_selection)
        main_layout.addWidget(self.save_button)

        # Set main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_event_group(self, title, events):
        group_box = QGroupBox(title)
        layout = QVBoxLayout()

        self.checkboxes = {}
        for event in events:
            checkbox = QCheckBox(event)
            layout.addWidget(checkbox)
            self.checkboxes[event] = checkbox

        group_box.setLayout(layout)
        return group_box

    def save_selection(self):
        selected_division = self.division_dropdown.currentText()
        selected_gender = self.gender_dropdown.currentText()

        selected_events = []
        for category in [self.run_group, self.jump_group, self.throw_group, self.multi_event_group]:
            for checkbox in category.findChildren(QCheckBox):
                if checkbox.isChecked():
                    selected_events.append(checkbox.text())

        print("Division:", selected_division)
        print("Gender:", selected_gender)
        print("Selected Events:", selected_events)


if __name__ == "__main__":
    app = QApplication([])
    window = EventSelector()
    window.show()
    app.exec()
