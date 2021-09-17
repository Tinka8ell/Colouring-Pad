"""
A frame to handle selecting colours.
"""
from tkinter import Frame, Radiobutton, IntVar
from tkinter.colorchooser import askcolor


class ColourButton(Radiobutton):
    
    _selectedText = "***"
    _unselectedText = " "
    
    def __init__(self, 
                 strip, 
                 colour, 
                 variable,
                 value=None,
                 selected=None):
        """
        A coloured radio button that can be selected and 
        have it's colour changed.
        
        Created with the given colour, and, if not provided, 
        sets its value from the variable object. Is added to the
        given strip (Frame) as a container. 
        
        Clicking on it selects it and sets its variable to its value.
        If provided calls the selected method with its colour.
        
        Double clicking allows the colour to be changed via a dialog
        and leaves it selected (see above).
        
        Can return its colour and have its colour set. 
        """
        if value is None:
            value = variable.get()
        super().__init__(strip,
                         variable=variable, 
                         text=self._unselectedText, 
                         value=value, 
                         bg=colour, 
                         indicatoron=0, 
                         command=self._selected)
        self._selectedMethod = selected
        self.setColour(colour)
        return
        
    def getColour(self):
        """
        Get the colour of the button from its background colour.
        """
        return self["bg"]

    def changeColour(self, event=None):
        """
        Use dialog to request new colour.
        Seed dialog with current colour and
        if colour is set use its hex string value to set the colour
        and select this button.
        """
        hexString = askcolor(self.getColour())[1]
        if hexString is not None: 
            self.setColour(hexString)
        return 

    def setColour(self, colour):
        """
        Sets the colour of the button to colour.
        """
        self.config(bg=colour, 
                    fg=colour, 
                    selectcolor=colour, 
                    activebackground=colour,
                    activeforeground=colour) 
        #self.deselect() 
        #self.select() 
        self._selected()
        return
    
    def _selected(self):
        self["text"] = self._selectedText
        if self._selectedMethod is not None:
            self._selectedMethod(colour)
        return
    
    def unselect(self):
        self[text] = self._unselectedText
        return

    
class ColourFrame(Frame):
    """
    A frame with count coloured radio buttons.
    
    Seed the strip with seedList of colours.
    Sets the rest with the defaultColour.
    Starts with the first selected (0th ColourButton).
    Clicking on any button selects that colour.
    Double clicking allows the colour of that button to be changed.
    Selecting a different ColourButton or changing the colour of one
    will be reported back by calling the changed method.
    """
    
    def __init__(self, 
                 frame, 
                 seedList, 
                 changed=None,
                 count=32,
                 defaultColour="white"):
        super().__init__(frame)
        self._selected = IntVar() # index of the colour selected
        self._changed =  changed
        self._colours = [] # list ColourButtons
        for i in range(count):
            if i < len(seedList):
                colour = seedList[i]
            else:
                colour = defaultColour
            b = ColourButton(self, 
                             colour, 
                             self._wasSelected, 
                             value=i)
            b.grid(column=i, row=0)
            b.bind("<Double-Button-1>", self.changeColour)
            self._colours.append(b)
        self._lastIndex = 0 # index of the colour we last selected
        self._selected.set(self._lastIndex)  # initialise
        return

    def _wasSelected(self):
        selected = self._getColourButton() 
        for colourButton  in self_colours:
            if colourButton != selected:
                colourButton.unselect()
        self.select(selected) 
        return
    
    def changeColour(self, event=None):
        """
        Respond to double click on a colour radio button with a 
        tkinter askcolour dialog box to select a colour.
        If a new one is selected set the colour of this button to it.
        """
        index = self._selected.get()
        radioButton = self._colours[index]
        currentColour = radioButton["bg"]
        hexstr = askcolor(currentColour)[1] # get rbg hex string for new colour
        if hexstr is not None: # a colour was selected
            self.setColour(hexstr)
        return
    
    def _getColourButton(self):
        """
        Get the ColourButton selected in the ColourFrame
        """
        index = self._selected.get()
        colourButton = self._colours[index]
        return colourButton

    def getColour(self):
        """
        Get the colour selected in the ColourFrame
        """
        colourButton = self._getColourButton()
        return colourButton.getColour()

    def setColour(self, colour):
        colourButton = self._getColourButton()
        colourButton.setColour(colour)
        self.selected(colourButton)
        return
    
    def selected(self, colourButton):
        if  self._changed is not None:
            self._changed(colourButton.getColour())
        return

