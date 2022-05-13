import cv2

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QScrollArea
from PyQt5.QtCore import QUrl, QEventLoop, Qt
import pyqtgraph as pg

class ImagePlot(pg.GraphicsLayoutWidget):

    def __init__(self, image = None):
        super(ImagePlot, self).__init__()

        self.image = image
        self.image_file = None
        self.image_item = None

        self.curr_point = 0

        self.p1 = pg.PlotItem()
        self.addItem(self.p1)
        self.p1.vb.invertY(True) # Images need inverted Y axis

        # Use ScatterPlotItem to draw points
        self.scatterItem = pg.ScatterPlotItem(
            size=3,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(255, 0, 0),
            hoverable=True,
            hoverBrush=pg.mkBrush(0, 255, 255)
        )

        self.scatterItem.setZValue(2) # Ensure scatterPlotItem is always at top
        self.points = [] # Record Points

        self.p1.addItem(self.scatterItem)

        direction.setText("Select "+landmark_labels[self.curr_point])


    def set_image(self, image):

        self.p1.clear()
        self.p1.addItem(self.scatterItem)

        self.image_item = pg.ImageItem(image)
        self.image_item.setOpts(axisOrder='row-major')
        self.p1.addItem(self.image_item)

        self.image = image


    def next_image(self, image, image_file = None):
        self.set_image(image)

        self.points = []
        self.scatterItem.setData(pos=self.points)

        self.image_file = image_file


    def proceed(self):
        global proceed_ok
        if len(self.points) == len(landmark_labels):
            record_data(self.points, self.image_file)
            proceed_ok = True
        else:
            direction.setText("You have not marked all the points.\nSelect "+landmark_labels[self.curr_point])


    def add_data(self, x, y):

        self.points.append([x, y])
        self.scatterItem.setData(pos=self.points)

        t = QLabel(landmark_labels[self.curr_point]+": "+str(x)+", "+str(y))
        text_layout.addWidget(t)

        self.curr_point += 1
        if self.curr_point < len(landmark_labels):
            direction.setText("Select "+landmark_labels[self.curr_point])
        else:
            direction.setText("Press Confirm")


    def mousePressEvent(self, event):
        point = self.p1.vb.mapSceneToView(event.pos()) # get the point clicked
        # Get pixel position of the mouse click
        x, y = point.x(), point.y()

        if event.button() == Qt.LeftButton and self.curr_point < len(landmark_labels):
            self.add_data(x, y)

        super().mousePressEvent(event)


def record_data(points, image_file):
    a = open("cleft_landmarks.csv", "a")
    a.write(image_file+","+",".join([str(i) for s in points for i in s])+"\n")


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        widgetToRemove = layout.itemAt(i).widget()
        # remove it from the layout list
        layout.removeWidget(widgetToRemove)
        # remove it from the gui
        widgetToRemove.setParent(None)


def reset():
    imageplot_main.points = []
    imageplot_main.scatterItem.setData(pos=[])
    imageplot_main.curr_point = 0
    clear_layout(text_layout)
    direction.setText("Select "+landmark_labels[0])


def undo():
    del imageplot_main.points[-1]
    imageplot_main.scatterItem.setData(pos=imageplot_main.points)
    imageplot_main.curr_point -= 1
    direction.setText("Select "+landmark_labels[imageplot_main.curr_point])


def confirm():
    global proceed_ok
    imageplot_main.proceed()
    if proceed_ok:
        reset()
        global loop
        loop.quit()


def main():

    global direction
    global text_layout
    global imageplot_main

    global loop

    global proceed_ok

    #Main window
    central_win = QWidget()
    central_layout = QVBoxLayout()
    central_win.setLayout(central_layout)
    win.setCentralWidget(central_win)
    win.setWindowTitle("My Own Title")

    #Pane for instruction
    direction_win = QWidget()
    direction_layout = QVBoxLayout()
    direction_win.setLayout(direction_layout)
    central_layout.addWidget(direction_win)

    #Instruction
    direction = QLabel()
    direction_layout.addWidget(direction)

    #Pane for image viewing & selecting
    image_win = QWidget()
    image_layout = QHBoxLayout()
    image_win.setLayout(image_layout)
    central_layout.addWidget(image_win)

    image_win.setFixedHeight(500)

    #Two image panes for image pane
    imageplot_main = ImagePlot()
    image_layout.addWidget(imageplot_main)

    #Text space for recorded points for image
    text_win = QWidget()
    text_layout = QVBoxLayout()
    text_win.setLayout(text_layout)

    scroll = QScrollArea()
    scroll.setWidget(text_win)
    scroll.setWidgetResizable(True)
    central_layout.addWidget(scroll)

    #Buttons space
    button_win = QWidget()
    button_layout = QHBoxLayout()
    button_win.setLayout(button_layout)
    central_layout.addWidget(button_win)

    #Button for clearing
    reset_button = QPushButton("Reset Image Landmark")
    reset_button.clicked.connect(reset)
    button_layout.addWidget(reset_button)

    #Button for undoing
    undo_button = QPushButton("Undo")
    undo_button.clicked.connect(undo)
    button_layout.addWidget(undo_button)

    #Button for completing
    confirm_button = QPushButton("Confirm")
    confirm_button.clicked.connect(confirm)
    central_layout.addWidget(confirm_button)

    win.show()

    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    files, _ = QFileDialog.getOpenFileNames(central_win,"QFileDialog.getOpenFileNames()", "","All Files (*);;Python Files (*.py)", options=options)
    if not files:
        app.exit(app.exec_())
        return

    for img_path in files:

        proceed_ok = False

        url = QUrl.fromLocalFile(img_path)
        filename = url.fileName()

        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        imageplot_main.next_image(img, filename)

        loop = QEventLoop()
        loop.exec()

    app.quit()


if __name__ == "__main__":
    rootDir = '../../data/Unilateral/'

    landmark_labels = ['Face: Top Left Corner', 'Face: Bottom Right Corner',
                       "c'ala", "sn", "c'cphs", "nc'ch", "nc'ala",
                       "nc'chps", "c'c", "c'sbal", "nc'sbal", "c'ch",
                       "nc'c", "prn", "ls", "mchpi", "c'rl",
                       "sto", "c'nt1", "c'nt2", "lcphi", "m'rl", "c'cphi"]

    app = QApplication([])
    win = QMainWindow()

    main()
