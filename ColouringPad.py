# Colouring Sheet

'''
Add on ideas - width / height and both options for zoom
Rotate 90 option to fit more on screen (portrait on landscape systems)
Current selected colour button
Colour dialog - Select from known names of colours, dropper for grabbing existing colour
Sorting known colours in some order
Removal of low use colours with similar used ones - eg nearly black to black ...
'''

import gc
import math
import os
from tkinter import Frame, Label, Canvas, Menu, Button, Radiobutton, Scale, Toplevel
from tkinter import HORIZONTAL, VERTICAL, E, W, N, S
from tkinter import Tk, ttk, IntVar, filedialog, messagebox
from tkinter.colorchooser import askcolor

from PIL import Image, ImageTk, ImageDraw, ImageColor

from ColourFrame import ColourFrame


def PadError(errorText, title="Colouring Pad - Oops!"):
    return messagebox.showerror(title, errorText)  # @IndentOk


def PadInfo(infoText, title="Colouring Pad"):
    return messagebox.showinfo(title, infoText)


def PadConfirm(questionText, title="Colouring Pad"):
    # return messagebox.askyesno("Are you sure?", questionText)
    return messagebox.askyesno(title=title, message=questionText)


def PadWait(parent, waitText, title="Please Wait"):
    class Wait:
        '''
        
        '''
    
        def __init__(self, parent, text, title):
            # print("Wait init", title, text)
            self.parent = parent
            top = self.top = Toplevel(parent)
            self.top.title(title)
            # self.top.overrideredirect(True)
            self.top.focus_set()
            self.top.grab_set()
            self.label = Label(top, text=text)
            self.label.grid(column=1, row=0)
            self.top.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
            return
    
        def quit(self):
            # print("Wait quit")
            self.parent.focus_set()
            self.top.destroy()
            return
          
    return Wait(parent, waitText, title)


class ColouringPad(Frame):

    def __init__(self, master=None):
        if not master:
            master = Tk()  # get root
        super().__init__(master)
        self.master = master
        self.master.title("Colouring Pad")
        self.saved = True
        self.undoSaved = False
        self.undoList = []  # use: self.undoList.insert(0, image) to add, and self.undoList.pop([0]) to remove
        self.dragging = False
        # get the name of our directory to access data
        self.baseDir = os.path.dirname(__file__)  # includes this module name (Editor)
        # self.baseDir = os.path.dirname(self.baseDir) # so strip it
        self.lastdir = self.baseDir
        self.foreground = '#ff0000'
        self.icon = None
        self.x, self.y, self.tox, self.toy = 0, 0, 0, 0
        # set of default colours till loaded a picture ...
        self.defaultColours = ["white", "black", "red", "green", "blue", "cyan", "yellow", "magenta"]
        self.used = self.defaultColours
        self.colourSelected = IntVar()
        self.mode = IntVar()
        self.mode.set(1)
        self.lastMode = self.mode.get()
        self.zoom = 100
        self.image = None  # Image.new("RGB", (3000, 3000), color="white")
        self.wait = None
        self.oldColour = None
        self.granularity = 2 / 1000  # how course line fixing should be
        self.oldValue = -1
        self.ok = True
        self.col, self.row = 1, 3  # for canvas
        self.canvas = None
        self.create_widgets()
        self.filename = os.path.join(self.lastdir, "default.png")
        self.frame.update_idletasks()
        self.loadFile()

    def create_widgets(self):
        # Create and grid the outer content frame
        master = self
        frame = self.master
        self.frame = frame
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # Add menu items
        self.cpMenu()

        # buttons
        self.addButtons(1)

        # colours
        self.colourRow = 2
        self.addColours()

        # Picture display area:
        col, row = 1, 3
        self.col, self.row = col, row
        width, height = (3000, 3000)
        if self.image:
            width, height = self.image.size
        self.pictureCanvas(width, height)

        # make it stretchy
        ttk.Sizegrip(frame).grid(column=col + 1, row=row, sticky=(S, E))
        # but only the display
        for i in range(col + 2):
            frame.grid_columnconfigure(i, weight=0)
        frame.grid_columnconfigure(col, weight=3)
        for i in range(row + 2):
            frame.grid_rowconfigure(i, weight=0)
        frame.grid_rowconfigure(row, weight=3)
        return

    def cpMenu(self):
        frame = self.frame
        menubar = Menu(frame)
        frame['menu'] = menubar
        menu_file = Menu(menubar)
        menu_edit = Menu(menubar)
        menubar.add_cascade(menu=menu_file, label='File', underline=0)
        menubar.add_cascade(menu=menu_edit, label='Edit', underline=0)
        menu_file.add_command(label='Load...', command=self.load, 
                              underline=0, accelerator="ctrl+L")
        menu_file.add_command(label='Save...', command=self.save, 
                              underline=0, accelerator="ctrl+S")
        menu_file.add_command(label='Adjust', command=self.adjust, 
                              underline=0, accelerator="ctrl+a")
        menu_file.add_command(label='Exit', command=self.exit, 
                              underline=1, accelerator="ctrl+X")
        menu_edit.add_command(label='Undo', command=self.undo, 
                              accelerator="ctrl+Z")
        menu_edit.add_command(label='Change colour', command=self.colourChange, 
                              underline=7, accelerator="ctrl+C")
        menu_edit.add_command(label='Mode - Fill', command=self.setFill, 
                              underline=7, accelerator="ctrl+F")
        menu_edit.add_command(label='Mode - Fix', command=self.setFix, 
                              underline=8, accelerator="ctrl+I")
        menu_edit.add_command(label='Info', command=self.info, 
                              underline=4, accelerator="ctrl+O")
        # Add keyboard short cuts
        frame.bind("<Control-l>", lambda event: self.load())
        frame.bind("<Control-s>", lambda event: self.save())
        frame.bind("<Control-a>", lambda event: self.adjust())
        frame.bind("<Control-x>", lambda event: self.exit())
        frame.bind("<Control-c>", lambda event: self.colour(None))
        frame.bind("<Control-f>", lambda event: self.setFill())
        frame.bind("<Control-i>", lambda event: self.setFix())
        frame.bind("<Control-z>", lambda event: self.undo())
        frame.bind("<Control-o>", lambda event: self.info())
        return

    def pictureCanvas(self, width, height):
        # print("pictureCanvas")
        frame = self.frame
        col, row = self.col, self.row
        h = ttk.Scrollbar(frame, orient=HORIZONTAL)
        h.grid(column=col, row=row + 1, sticky=(W, E))
        v = ttk.Scrollbar(frame, orient=VERTICAL)
        v.grid(column=col + 1, row=row, sticky=(N, S))
        self.canvas = Canvas(frame, scrollregion=(0, 0, width, height),
                               yscrollcommand=v.set, xscrollcommand=h.set,
                               borderwidth=2, relief="groove")  
        # alternatives are: raised, sunken, flat, ridge, solid, and groove 
        # and (width=3000, height=3000,)
        self.canvas.grid(column=col, row=row, sticky=(N, W, E, S))
        h['command'] = self.canvas.xview
        v['command'] = self.canvas.yview
        self.canvas.bind("<ButtonPress-1>", self.pressed)
        # self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<ButtonRelease-1>", self.released)
        # print("pictureCanvas-ret")
        return

    def addButtons(self, buttonRow):
        frame = self.frame
        buttonCol, buttonWidth = 1, 2
        self.buttonStrip = Frame(frame) 
        self.buttonStrip.grid(column=buttonCol, row=buttonRow, 
                              columnspan=buttonWidth, sticky=(N, E, W, S))
        # define
        self.buttonLoad = Button(self.buttonStrip, text="Load", 
                                 underline=0, command=self.load)
        self.buttonSave = Button(self.buttonStrip, text="Save", 
                                 underline=0, command=self.save)
        self.buttonQuit = Button(self.buttonStrip, text="Exit", 
                                 underline=1, command=self.exit)
        self.buttonZoom = Label(self.buttonStrip, text="Zoom")
        self.buttonSpin = Scale(self.buttonStrip, from_=1, to=14, 
                                label="Zooom", showvalue=0,
                                repeatdelay=1000, repeatinterval=1000, 
                                command=self.zoomed, orient=HORIZONTAL)
        self.buttonMode = Label(self.buttonStrip, text="Mode")
        self.buttonFill = Radiobutton(self.buttonStrip, variable=self.mode, 
                                      text="Fill", value=1)
        self.buttonFix = Radiobutton(self.buttonStrip, variable=self.mode, 
                                     text="Fix", value=0)
        self.buttonDropper = Radiobutton(self.buttonStrip, variable=self.mode, 
                                         text="Dropper", value=2)
        # arrange
        self.buttonLoad.grid(column=1, row=0, pady=5, padx=5)
        self.buttonSave.grid(column=2, row=0, pady=5, padx=5)
        self.buttonQuit.grid(column=3, row=0, pady=5, padx=5)
        # stick zoom in the middle
        self.buttonZoom.grid(column=6, row=0)
        self.buttonSpin.grid(column=7, row=0)
        # stick mode at the end
        self.buttonMode.grid(column=11, row=0)
        self.buttonFill.grid(column=12, row=0)
        self.buttonFix.grid(column=13, row=0)
        self.buttonDropper.grid(column=14, row=0)
        # print("AddButtons - call set zoom")
        self.setZoom(100)
        return

    def addColours(self):
        buttonCol, buttonWidth, buttonRow = 1, 2, self.colourRow
        self.colourStrip = ColourFrame(self.frame,
                                       self.used,
                                       self.colourChanged) 
        # the rest are defaults:       ,
        #                              count=32,
        #                              defaultColour="white")
        self.colourStrip.grid(column=buttonCol, row=buttonRow, 
                              columnspan=buttonWidth, sticky=(N, E, W, S))
        self.chosen = self.colourStrip.getColour()
        return

    def colourChanged(self, colour):
        # called when the colour is changed
        self.undoSaved = False
        self.chosen = colour
        return

    def zoomed(self, event):
        # print("zoomed")
        value = self.buttonSpin.get()
        if value < 0:
            # print("zoomed-ret(none)")
            return
        if value == self.oldValue:
            # print("zoomed-ret(none)")
            return
        self.oldValue = value
        self.buttonSpin.configure(state="disabled")
        # print("zoomer changed to", value)
        value = (value - 10) / 2
        value = 2 ** value
        self.zoom = int(value * 100)
        # print("zoomed to", self.zoom)
        self.buttonSpin.config(label=str(self.zoom) + "%")
        self.ok = True
        self.resize()
        if not self.ok:
            self.ok = True
            # print("Zoomed not ok, so try and set from:", \
            # self.zoom, "to:", self.zoom / 2)
            # self.buttonSpin.set(self.buttonSpin.get() - 1)
        self.buttonSpin.configure(state="normal")
        # print("zoomed-ret")
        return

    def setZoom(self, value):
        # print("setZoom")
        self.zoom = int(value)
        # print("set Zoom", value)
        value = value / 100
        value = math.log2(value)
        value = value * 2
        value = int(value + 10)
        # print("setting spin to", value)
        self.buttonSpin.set(value)
        # print("set spin to", value, "now not calling zoomed")
        # self.zoomed(None)
        # print("setZoom-ret")
        return

    def setFill(self):
        self.mode.set(1)
        self.undoSaved = False
        return

    def setFix(self):
        self.mode.set(0)
        self.undoSaved = False
        return

    def colourChange(self):
        self.colourStrip.changeColour()
        return

    def exit(self):
        if not self.saved:
            response = PadConfirm("Unsaved picture! \n" 
                                  "Do you want to quit without saving it?")
            if response:
                self._quit()
        else:
            self._quit()
        return

    def _quit(self):
        self.master.destroy()
        return

    def info(self):
        if self.wait:
            self.wait.quit()
            self.wait = None
        else:
            self.wait = PadWait(self.canvas, "Please wait")
        # print("image", self.image.size)
        widget = self.canvas
        # print("Canvas: width", widget.winfo_width(),
        #       "rootx", widget.winfo_rootx(),
        #       "xview", widget.xview(), 
        #       (self.image.width*widget.xview()[0], 
        #       self.image.width*widget.xview()[1]))
        # print("1.0 - widget.xview()[1]", 
        #       1.0 - widget.xview()[1], 
        #       ((1.0 - widget.xview()[1]) > 0.01))
        while ((1.0 - widget.xview()[1]) > 0.01):
            s = input('--> ')
            if len(s) > 0:
                break
            # print("about to scroll", "1 p")
            widget.xview_scroll(1, "p")
            self.frame.update_idletasks()
            # print("Canvas: width", widget.winfo_width(),
            #       "rootx", widget.winfo_rootx(),
            #       "xview", widget.xview(), 
            #       (self.image.width*widget.xview()[0],  
            #       self.image.width*widget.xview()[1]))
            # print("1.0 - widget.xview()[1]",  
            #       1.0 - widget.xview()[1],  
            #       ((1.0 - widget.xview()[1]) > 0.01))
        return

    def load(self):
        if not self.saved:
            response = PadConfirm("Unsaved picture! \n"
                                  "Do you want to load without saving it?")
            if response:
                self._load()
        else:
            self._load()
        return

    def _load(self):
        self.filename = filedialog.askopenfilename(initialdir=self.lastdir, 
                                                   title="Load picture",
                                                   filetypes=(
                                                       ("picture files", 
                                                        "*.png"), 
                                                       ("all files", 
                                                        "*.*")
                                                       )
                                                   )
        self.loadFile()
        return

    def loadFile(self):
        # print("loadFile")
        if self.filename != "":
            self.lastdir = os.path.dirname(self.filename)
            image = Image.open(self.filename)
            # print("Loaded", "size", image.size, "mode", image.mode)
            enough = image.width * image.height / 100  # 1% of image ...
            image = image.convert()  # to RBG
            # print("Converted", "size", image.size, "mode", image.mode)
            image = image.quantize(colors=32)  # reduce to max 32 colours
            # print("Quantized", "size", image.size, "mode", image.mode)
            image = image.convert()  # to RBG (again) so can do the colour fill
            # print("Converted", "size", image.size, "mode", image.mode)
            # palette = image.getpalette()
            colours = image.getcolors()
            count = 0
            used = []
            if colours:
                for i in range(len(colours)):
                    if colours[i][0] > enough:
                        # make minimum list of colours in #rrggbb format
                        used.append("#%02x%02x%02x" % colours[i][1][0:3])  
                        count += 1
            # print("count", count)
            if count < len(self.defaultColours):
                used.extend(self.defaultColours)
            used = sorted(used)
            self.used = used
            self.setImage(image)
        # print("loadFile-ret")
        return

    def undo(self):
        if len(self.undoList) > 0:  # we have an undo available
            image = self.undoList.pop()
            self.setImage(image)
        return

    def saveUndo(self):
        self.undoList.append(self.image.copy())
        self.undoSaved = True
        return

    def setImage(self, image):
        # print("setImage")
        self.image = image
        self.undoSaved = False
        self.addColours()
        self.canvas = None  # new image, new canvas
        w = self.frame.winfo_width()
        h = (self.frame.winfo_height() 
             - self.buttonStrip.winfo_height() 
             - self.colourStrip.winfo_height()
             )
        width, height = self.image.size
        if w < 2 or h < 2:
            w, h = (width, height)
        rw, rh = (w / width, h / height)
        ratio = min(1, rw, rh)
        # print("setImage: (width, height)", (width, height), 
        #       "w, h", (w, h), "rw, rh", (rw, rh))
        self.setZoom(ratio * 100)
        # print("setImage after setZoom")
        self.resize()
        # print("setImage-ret")
        return

    def resize(self):
        # print("resize")
        if not self.image:
            # print("resize-ret(none)")
            return  # nothing to resize!
        ratio = self.zoom / 100
        self.width = int(self.image.width * ratio) + 2
        self.height = int(self.image.height * ratio) + 2
        '''
        widget = self.canvas
        if widget: # have set up canvas
            x = (widget.xview()[0] + widget.xview()[1]) / 2
            y = (widget.yview()[0] + widget.yview()[1]) / 2
            w = widget.xview()[1] - widget.xview()[0]
            h = widget.yview()[1] - widget.yview()[0]
            # print("resize() before:", ratio, (x, y), 
            #       (x * self.image.width, y * self.image.height), (w, h))
            # x,y is middle before zoom as fraction of 1
        '''
        self.show()
        '''
        if widget: # have set up canvas
            widget = self.canvas # as canvas mybe new ...
            w = widget.xview()[1] - widget.xview()[0]
            h = widget.yview()[1] - widget.yview()[0]
            # w, h new size as fraction of 1
            x = max(x - w/2, 0)
            y = max(y - h/2, 0)
            # print("resize() taget:", ratio, (x, y), 
            #       (x * self.image.width, y * self.image.height), (w, h))
            # x, y new top left (ensuring on picture)
            widget.xview_moveto(x)
            widget.yview_moveto(y)
            w = widget.xview()[1] - widget.xview()[0]
            h = widget.yview()[1] - widget.yview()[0]
            x = (widget.xview()[0] + widget.xview()[1]) / 2
            y = (widget.yview()[0] + widget.yview()[1]) / 2
            # print("resize() after:", ratio, (x, y), 
            #       (x * self.image.width, y * self.image.height), (w, h))
            # image re-centred!
        '''
        # print("resize-ret")
        return

    def show(self):
        # print("show")
        self.pictureCanvas(self.width, self.height)
        self.display()
        # print("show-ret")
        return

    def display(self):
        # print("display")
        image = self.image
        wait = PadWait(self.canvas, "Please wait")
        wait.label.wait_visibility()
        try:
            image = image.quantize(colors=32)  # reduce to max 32 colours
            # print("Quantized", "size", image.size, "mode", image.mode)
            image = image.resize((self.width, self.height))
            self.picture = ImageTk.PhotoImage(image=image)
        except Exception as e:
            # print("Exception in display()\n" + str(e))
            wait.quit()
            PadError("Not enough memory to magnify that far!\n" + str(e))
            self.ok = False
            image = None
            self.picture = None
            # try and recover ...
            gc.collect()
        if self.ok:
            self.canvas.create_image(
                (self.width / 2 + 1, 
                 self.height / 2 + 1), 
                image=self.picture)
        wait.quit()
        # print("display-ret")
        return

    def adjust(self):
        fudge = 2
        w, h = self.image.size
        image = self.image.resize(
            (int(w / fudge), 
             int(h / fudge)), 
            resample=Image.BOX)  # shrink to merge lines (fudge)
        self.image = image.resize((w, h))  # restore size
        self.show()
        return

    def save(self):
        if self.image:
            self.filename = filedialog.asksaveasfilename(
                initialdir=self.lastdir, title="Save picture",
                filetypes=(("picture files", "*.png"), ("all files", "*.*")), 
                defaultextension=".png")
            if self.filename != "":
                self.lastdir = os.path.dirname(self.filename)
                self.image.save(self.filename)
                self.saved = True
                self.undoSaved = False
        else:
            PadError("You will need load or generate a knot first!")
        return

    def colourIt(self):
        if not self.image:
            return  # nothing to do
        # print("colourIt() called")
        if not self.undoSaved:
            self.saveUndo()
        ratio = self.zoom / 100
        x, y = int(self.tox / ratio), int(self.toy / ratio)
        try:
            target = self.image.getpixel((x, y))
        except IndexError:
            target = None
            # print ("Ignoring click outside picture:", e)
        if not target:
            return  # nothing to do
        colour = ImageColor.getcolor(self.chosen, self.image.mode)
        # print("target", target, "(x, y)", (x, y), 
        #       "chosen", self.chosen, "colour", colour)
        if self.mode.get() == 1:  # fill
            self.lastMode = self.mode.get()
            self.canvas.config(cursor="watch")
            wait = PadWait(self.canvas, "Please wait")
            wait.label.wait_visibility()
            ImageDraw.floodfill(self.image, (x, y), colour)
            wait.quit()
            self.canvas.config(cursor="")
        elif self.mode.get() == 0:  # fix
            self.lastMode = self.mode.get()
            delta = int(min(self.image.size) * self.granularity / 2)
            draw = ImageDraw.Draw(self.image)
            wait = PadWait(self.canvas, "Please wait")
            wait.label.wait_visibility()
            draw.rectangle(
                (x - delta, y - delta, x + delta, y + delta), 
                fill=colour)  # draw a blob
            wait.quit()
        else:  # dropper
            self.mode.set(self.lastMode)  # reset to what was last used
            # target is colour to use
            selected = self.colourSelected.get()
            hexstr = "#%02x%02x%02x" % target
            self.colourStrip.setColour(hexstr)
        self.display()
        self.saved = False
        # print("colourIt() ended")
        return

    def pressed(self, event):
        # place where button pressed
        if self.image:
            # lastx, lasty = self.x, self.y
            # remember where we are for later
            self.x, self.y = self.getPos(event)  
            # print("Pressed:", self.x, self.y)
            self.dragging = True
            # so we can see where the selection starts from ...
            self.tox = self.x
            self.toy = self.y
        else:
            PadInfo("No knot yet!")
        return

    def motion(self, event):
        # place where mouse moved
        if self.dragging:  # only care while dragging!
            # lastx, lasty = self.tox, self.toy
            self.tox, self.toy = self.getPos(event)  # we are now here
            # print("Moved:", self.tox, self.toy)
        return

    def getPos(self, event):
        # place where mouse is in event
        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        # print("getPos =", (x, y))
        return x, y

    def released(self, event):
        # place where button released
        if self.image:
            # lastx, lasty = self.tox, self.toy
            # so we can see where the selection ends ...
            self.tox, self.toy = self.getPos(event)
            # ## print("Released:", self.tox, self.toy)
            self.dragging = False
            self.colourIt()
        else:
            PadInfo("No picture yet!")
        return


if __name__ == "__main__":
    # run the colouring pad ...
    root = Tk()
    # root.state(newstate="zoomed")
    pad = ColouringPad(master=root)
    pad.mainloop()
