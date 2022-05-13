import os

import cv2

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QScrollArea
from PyQt5.QtCore import QUrl, QEventLoop
import pyqtgraph as pg

class ImagePlot(pg.GraphicsLayoutWidget):

    def __init__(self, allow_pick = False, allow_zoom = False, linked_image = None, image = None, record = False):
        super(ImagePlot, self).__init__()

        self.allow_pick = allow_pick
        self.allow_zoom = allow_zoom
        self.linked_image = linked_image
        self.image = image
        self.record = record
        self.image_file = None

        self.curr_point = 0

        self.p1 = pg.PlotItem()
        self.addItem(self.p1)
        self.p1.vb.invertY(True) # Images need inverted Y axis

        # Use ScatterPlotItem to draw points
        self.scatterItem = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(255, 0, 0),
            hoverable=True,
            hoverBrush=pg.mkBrush(0, 255, 255)
        )

        self.scatterItem.setZValue(2) # Ensure scatterPlotItem is always at top
        self.points = [] # Record Points

        self.p1.addItem(self.scatterItem)

        direction.setText("Select "+landmark_labels[self.curr_point])


    def set_linked_image(self, imageplot):
        self.linked_image = imageplot


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
        if self.record:
            print("recording")
            record_data(self.points, self.image_file)


    def set_prime(self, x, y, zoom):
        self.x_prime = x
        self.y_prime = y
        self.zoom_prime = zoom


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

        if self.allow_pick:
            if self.linked_image.curr_point < len(landmark_labels):
                self.points.append([x, y])
                self.scatterItem.setData(pos=self.points)

                #add point to original image
                x_original = x/self.zoom_prime+self.x_prime
                y_original = y/self.zoom_prime+self.y_prime
                self.linked_image.add_data(x_original, y_original)

        elif self.allow_zoom:
            zoom = 5
            width = self.image.shape[1]
            height = self.image.shape[0]
            if x<width/zoom:
                x = width/zoom
            elif x>=4*width/zoom:
                x = 4*width/zoom-1
            if y<height/zoom:
                y = height/zoom
            elif y>=4*height/zoom:
                y = 4*height/zoom-1

            x = int(x)
            y = int(y)

            img = self.image[int(y-height/zoom/2):int(y+height/zoom/2), int(x-width/zoom/2):int(x+width/zoom/2)]
            img = cv2.resize(img, None, fx = zoom, fy = zoom)
            self.linked_image.next_image(img)
            self.linked_image.set_prime(x-width/zoom/2, y-height/zoom/2, zoom)

            for i, j in self.points:
                if x <= i < int(x+width/zoom) and y <= j < int(y+height/zoom):
                    self.linked_image.add_data(i-x, j-y)

        super().mousePressEvent(event)


def record_data(points, image_file):
    a = open("../cleft_landmarks.csv","a")
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
    imageplot_main.scatterItem.setData(pos=imageplot_main.points)
    imageplot_side.points = []
    imageplot_side.scatterItem.setData(pos=imageplot_side.points)
    imageplot_main.curr_point = 0
    clear_layout(text_layout)
    direction.setText("Select "+landmark_labels[0])


def confirm():
    imageplot_main.proceed()
    global loop
    loop.quit()


def main():

    global direction
    global text_layout
    global imageplot_main
    global imageplot_side

    global loop

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

    image_win.setFixedHeight(800)

    #Two image panes for image pane
    imageplot_main = ImagePlot(allow_zoom = True, record = True)
    imageplot_side = ImagePlot(allow_pick = True, linked_image = imageplot_main)
    imageplot_main.set_linked_image(imageplot_side)
    image_layout.addWidget(imageplot_main)
    image_layout.addWidget(imageplot_side)

    #Text space for recorded points for image
    text_win = QWidget()
    text_layout = QVBoxLayout()
    text_win.setLayout(text_layout)
    central_layout.addWidget(text_win)

    scrollArea = QScrollArea()
    scrollArea.setWidget(text_win)

    #Button for clearing
    reset_button = QPushButton("Reset Image Landmark")
    reset_button.clicked.connect(reset)
    central_layout.addWidget(reset_button)

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

    #open file with filenames
    # with open('cleft_filenames.txt') as file:
    #     lines = file.readlines()

    for img_path in files:

        proceed_image = False

        url = QUrl.fromLocalFile(img_path)
        filename = url.fileName()

        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        imageplot_main.next_image(img, filename)

        loop = QEventLoop()
        loop.exec()

    app.exit(app.exec_())


if __name__=="__main__":
    rootDir = '../../data/Unilateral/'

    landmark_labels = ['Face: Top Left Corner', 'Face: Bottom Right Corner',
                       "c'ala", "sn", "c'cphs", "nc'ch", "nc'ala",
                       "nc'chps", "c'c", "c'sbal", "nc'sbal", "c'ch",
                       "nc'c", "prn", "ls", "mchpi", "c'rl",
                       "sto", "c'nt1", "c'nt2", "lcphi", "m'rl", "c'cphi"]

    app = QApplication([])
    win = QMainWindow()

    main()