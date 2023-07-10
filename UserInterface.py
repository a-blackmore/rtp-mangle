import wx
import subprocess
import pydicom


class PopUp(wx.Frame):
    def __init__(self, text):
        super().__init__(parent=None, title='', size = (600,100))

        panel = wx.Panel(self)
        my_sizer = wx.BoxSizer(wx.VERTICAL) 

        self.text = wx.StaticText(panel, label=text, style=wx.TE_MULTILINE | wx.TE_READONLY)
        
        my_sizer.Add(self.text, 1, flag = wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border = 20)

        panel.SetSizer(my_sizer)
        self.Show()

class MyFrame(wx.Frame):
    def __init__(self):

        self.commandString = ''
        self.pathname = ''
        self.directory = ''
        self.outFile = ''
        self.addedInFile = False
        self.addedKeepUid = False 
        self.addedVerbose = False
        self.dark_mode = False

        super().__init__(parent=None, title='Plan Mnagler', size = (1500, 650))

        panel = wx.Panel(self)   

        my_sizer = wx.BoxSizer(wx.VERTICAL)  

        initialOptions = wx.GridSizer(2,9,5,5)
        beamData = wx.GridSizer(9,9,5,5)
        helptext = wx.GridSizer(6,1,5,5,)
        perform = wx.FlexGridSizer(1,4,5,5)

        file_open = wx.Button(panel, label='Input File')
        file_open.Bind(wx.EVT_BUTTON, self.OnOpen)


        self.uid = wx.CheckBox(panel, label = 'Keep SOPInstanceUID' )
        self.verbose = wx.CheckBox(panel, label = 'Verbose Console Ouput ?')
 
      
# Filters
        self.beam = wx.ComboBox(panel)
        self.controlPointsFrom = wx.ComboBox(panel)
        self.controlPointsTo = wx.ComboBox(panel)


        # Checkbox to choose either jaw or Mlc to be modified.
        self.mlc_jaw = wx.ToggleButton(panel, label = 'Edit MLC')
        self.mlc_jaw.Bind(wx.EVT_TOGGLEBUTTON, self.on_check)
     
        self.jaw_label = wx.StaticText(panel , label ='Jaw :')
        self.jaw = wx.ComboBox(panel, choices=['0- X Jaws','1- Y Jaws','0,1- Both Jaws'], style=wx.BORDER_NONE)
        self.jaw.Bind(wx.EVT_COMBOBOX, self.OnJawChoice)
        self.jaw_bank_label = wx.StaticText(panel , label ='Jaw Bank:')
        self.jawBank = wx.ComboBox(panel, choices=[''])

        self.leaf_bank_label = wx.StaticText(panel , label ='Leaf Bank :')
        self.leafBank = wx.ComboBox(panel, choices=['0','1','0,1'])
        self.leaf_pair_label = wx.StaticText(panel , label ='Leaf Pair From:')
        self.leaf_pair_from_label = wx.StaticText(panel , label ='From :')
        self.leafPairFrom = wx.ComboBox(panel)
        self.leaf_pair_to_label = wx.StaticText(panel , label ='To :')
        self.leafPairTo = wx.ComboBox(panel)
    

        # Checkbox to choose either postion absolute or position relative for jaw or MlC modifications.
        self.jaw_relative = wx.CheckBox(panel, label = 'Relative Change ?' )
        self.jaw_position = wx.TextCtrl(panel)

        self.leaf_relative = wx.CheckBox(panel, label = 'Relative Change ?' )
        self.leaf_position = wx.TextCtrl(panel)

        self.outputFile = wx.TextCtrl(panel)

        self.commandString_view = wx.TextCtrl(panel, -1,'' ,style=wx.TE_MULTILINE)

        self.darkMode = wx.ToggleButton(panel, label='Dark Mode')
        self.darkMode.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleDark)


# Setters 
        self.MU = wx.TextCtrl(panel)
        self.Machine = wx.TextCtrl(panel)
        self.Gantry = wx.TextCtrl(panel)
        self.Collimator = wx.TextCtrl(panel)
       
        perform_btn = wx.Button(panel, label='Perform')
        perform_btn.Bind(wx.EVT_BUTTON, self.perform)

        self.AddToCommand = wx.Button(panel, label = 'Add to Command')
        self.AddToCommand.Bind(wx.EVT_BUTTON, self.on_press)
 
        initialOptions.AddMany([

            (file_open, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(self.darkMode,0,wx.EXPAND,5),

            (self.uid, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(self.verbose, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel, label ='Output File Name:' ),0, wx.ALIGN_CENTER_VERTICAL,5),(self.outputFile,0,wx.EXPAND,5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),


        ])
        
        beamData.AddMany([

            (wx.StaticText(panel, label ='Beam :'),0, wx.ALIGN_CENTER_VERTICAL,5),(self.beam, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),

            (wx.StaticText(panel , label ='Control Points From:'),0, wx.ALIGN_CENTER_VERTICAL,5),(self.controlPointsFrom, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='To:'),0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,5),(self.controlPointsTo, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label =''),0, wx.ALIGN_CENTER_VERTICAL| wx.ALIGN_CENTER_HORIZONTAL,5),

            (self.mlc_jaw, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),
            
            (self.jaw_label,0, wx.ALIGN_CENTER_VERTICAL,5),(self.jaw, 0 , wx.EXPAND, 5),(self.jaw_bank_label,0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,5),(self.jawBank, 0 , wx.EXPAND, 5),(self.jaw_relative, 0 , wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 5), (self.jaw_position, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),

            (self.leaf_bank_label,0, wx.ALIGN_CENTER_VERTICAL,5),(self.leafBank, 0 , wx.EXPAND, 5),(self.leaf_pair_label,0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,5),(self.leafPairFrom, 0 , wx.EXPAND, 5),(self.leaf_pair_to_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,5),(self.leafPairTo, 0, wx.EXPAND, 5),(self.leaf_relative, 0 , wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 5), (self.leaf_position, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),

            (wx.StaticText(panel, label ='MU :' ),0, wx.ALIGN_CENTER_VERTICAL,5),(self.MU, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),
            
            (wx.StaticText(panel, label ='Machine ID:' ),0, wx.ALIGN_CENTER_VERTICAL,5),(self.Machine, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),
            
            (wx.StaticText(panel, label ='Gantry Angle:' ),0, wx.ALIGN_CENTER_VERTICAL,5),(self.Gantry, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),
            
            (wx.StaticText(panel, label ='Collimator Angle :' ),0, wx.ALIGN_CENTER_VERTICAL,5),(self.Collimator, 0, wx.EXPAND, 5),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),(wx.StaticText(panel , label ='')),
 

        ])

        helptext.AddMany([

            (wx.StaticLine(panel, 0, size =(1450,1), style=wx.LI_HORIZONTAL),0,wx.ALIGN_CENTER_VERTICAL,5),

            (wx.StaticText(panel , label ='• Not all parameters are required, only specify what requires modification.'),0,wx.ALIGN_CENTER_HORIZONTAL,5),
            
            (wx.StaticText(panel , label ='• SOPInstanceUID - Some devices require this to remain unchanged to allow analysis, others refuse to import files with duplicate UID.'),0,wx.ALIGN_CENTER_HORIZONTAL,5),
            
            (wx.StaticText(panel , label ='• Leaf bank defines the A or B side, experimentation is required to determine which is 0 and which is 1.'),0,wx.ALIGN_CENTER_HORIZONTAL,5),

            (wx.StaticText(panel , label ='• Absolute values or relative changes can be applied to Jaws, Leafs, MU, Gantry Angle, and Collimator Angle. Relative changes can be specified as either +/- values (+10 or -5 for example) or percent values (+10% or -5% for example).'),0,wx.ALIGN_CENTER_HORIZONTAL,5),

            (wx.StaticLine(panel, 0, size =(1450,1), style=wx.LI_HORIZONTAL),0,wx.ALIGN_CENTER_VERTICAL,5),
        ])

        
        perform.AddMany([

            (self.AddToCommand,0,wx.EXPAND,5),(wx.StaticText(panel , label ='Current Command :'),0,wx.ALIGN_CENTER_VERTICAL,5),(self.commandString_view, 0, wx.EXPAND, 5),(perform_btn, 0, wx.EXPAND, 5)

        ])

        perform.AddGrowableCol(2)
        perform.AddGrowableRow(0)

        my_sizer.Add(initialOptions, 1, flag = wx.ALL | wx.EXPAND, border = 15)
        my_sizer.Add(beamData, 1, flag = wx.ALL | wx.EXPAND, border = 15)   
        my_sizer.Add(helptext, 1, flag = wx.ALL | wx.EXPAND, border = 15)
        my_sizer.Add(perform, 1, flag = wx.ALL | wx.EXPAND, border = 15)    

        panel.SetSizer(my_sizer)      
        
        self.Show()

        self.jaw_label.Show()
        self.jaw.Show()
        self.jaw_bank_label.Show()
        self.jawBank.Show()
        self.jaw_relative.Show()
        self.jaw_position.Show()

        self.leaf_bank_label.Hide()
        self.leafBank.Hide()
        self.leaf_pair_label.Hide()
        self.leafPairFrom.Hide()
        self.leaf_pair_from_label.Hide()
        self.leafPairTo.Hide()
        self.leaf_pair_to_label.Hide()
        self.leaf_relative.Hide()
        self.leaf_position.Hide()


    def on_check(self, event):
            if self.mlc_jaw.IsChecked():
                self.jaw_label.Hide()
                self.jaw.Hide()
                self.jaw_bank_label.Hide()
                self.jawBank.Hide()
                self.jaw_relative.Hide()
                self.jaw_position.Hide()

                self.leaf_bank_label.Show()
                self.leafBank.Show()
                self.leaf_pair_label.Show()
                self.leafPairFrom.Show()
                self.leaf_pair_from_label.Show()
                self.leafPairTo.Show()
                self.leaf_pair_to_label.Show()
                self.leaf_relative.Show()
                self.leaf_position.Show()
            else:
                self.jaw_label.Show()
                self.jaw.Show()
                self.jaw_bank_label.Show()
                self.jawBank.Show()
                self.jaw_relative.Show()
                self.jaw_position.Show()

                self.leaf_bank_label.Hide()
                self.leafBank.Hide()
                self.leaf_pair_label.Hide()
                self.leafPairFrom.Hide()
                self.leaf_pair_from_label.Hide()
                self.leafPairTo.Hide()
                self.leaf_pair_to_label.Hide()
                self.leaf_relative.Hide()
                self.leaf_position.Hide()
            
   
       
    def on_press(self, event):
        #script_path = mangle.__path__
        

        # In File
        inFile = self.pathname
        if not self.addedInFile:
            self.commandString = self.commandString + '"' + inFile + '"'
            self.addedInFile = True


        # Command string 
        #Filters
        beams = ''
        if self.beam.GetValue():
            beams = 'b' + self.beam.GetValue().split('-')[0]
        controlPoints = ''
        if self.controlPointsFrom.GetValue():
            if self.controlPointsTo.GetValue():
                controlPoints = 'cp' + self.controlPointsFrom.GetValue() + '-' + self.controlPointsTo.GetValue()
            else:
                controlPoints = 'cp' + self.controlPointsFrom.GetValue()

        jaw_or_mlc_command = ''
        if self.mlc_jaw.GetValue():
            if self.leafBank.GetValue():
                leafbank = 'lb' + self.leafBank.GetValue()
                leafpair = ''
                if self.leafPairFrom.GetValue():
                    if self.leafPairTo.GetValue():
                        leafpair = 'lp' + self.leafPairFrom.GetValue() + '-' + self.leafPairTo.GetValue()
                    else:
                        leafpair = 'lp' + self.leafPairFrom.GetValue()
                position = ''
                if self.leaf_relative.GetValue():
                    postion = 'pr=' + self.leaf_position.GetValue()
                else:
                    position = 'pa=' + self.leaf_position.GetValue()

                jaw_or_mlc_command = leafbank + ' ' + leafpair + ' ' + position
        else:
            if self.jaw.GetValue():
                jaw = 'j' + self.jaw.GetValue().split('-')[0]
                jawBank = 'jb' + self.jawBank.GetValue().split('-')[0]
                position = ''
                if self.jaw_relative.GetValue():
                    position = 'pr=' + self.jaw_position.GetValue()
                else:
                    position = 'pa=' + self.jaw_position.GetValue()
                jaw_or_mlc_command = jaw + ' ' + jawBank + ' ' + position
        print(jaw_or_mlc_command)

        mu = ''
        if self.MU.GetValue():
            mu = 'mu=' + self.MU.GetValue()
        machine =''
        if self.Machine.GetValue():
            machine = 'm=' + self.Machine.GetValue()
        gantry = ''
        if self.Gantry.GetValue():
            gantry = 'g=' + self.Gantry.GetValue()
        collimator = ''
        if self.Collimator.GetValue():
            collimator = 'c=' + self.Collimator.GetValue()


        #Options
        keepUID ='-k '
        verbose ='-v '

        if self.uid.GetValue():
            if not self.addedKeepUid:
                self.commandString = keepUID + self.commandString
                self.commandString = self.commandString.replace(' ""', '')
                self.addedKeepUid = True
        else:
            self.commandString = self.commandString.replace(keepUID, '')
            self.commandString = self.commandString.replace(' ""', '')
            self.addedKeepUid = False

        if  self.verbose.GetValue():
            if not self.addedVerbose:
                self.commandString = verbose + self.commandString
                self.commandString = self.commandString.replace(' ""', '')
                self.addedVerbose = True
        else:
            self.commandString = self.commandString.replace(verbose, '')
            self.commandString = self.commandString.replace(' ""', '')
            self.addedVerbose = False
 
        if self.outputFile.GetValue():
            self.outFile = self.directory + "\\" + self.outputFile.GetValue() + ".dcm"
            self.commandString = self.commandString + ' -o "' + self.directory + "\\" + self.outputFile.GetValue() + ".dcm" + '"'
        else:
            self.outFile = "out.dcm" 
          

        command = beams + ' ' + controlPoints + ' ' + jaw_or_mlc_command + ' ' + mu + ' ' + machine + ' ' + gantry + ' ' + collimator 
        command = ' '.join(command.split())

        self.commandString = self.commandString + ' "' + command + '"'
        self.commandString = self.commandString.replace(' ""', '')
        

        self.commandString_view.SetValue(self.commandString)

        self.beam.SetValue('')
        self.controlPointsFrom.SetValue('')
        self.controlPointsTo.SetValue('')
        # Checkbox to choose either jaw or Mlc to be modified.
        self.mlc_jaw.SetValue(wx.CHK_UNCHECKED)
        self.jaw.SetValue('')
        self.jawBank.SetValue('')
        self.leafBank.SetValue('')
        self.leafPairFrom.SetValue('')
        self.leafPairTo.SetValue('')
        # Checkbox to choose either postion absolute or position relative for jaw or MlC modifications.
        self.jaw_relative.SetValue(wx.CHK_UNCHECKED)
        self.jaw_position.SetValue('')
        self.leaf_relative.SetValue(wx.CHK_UNCHECKED)
        self.leaf_position.SetValue('')
        self.MU.SetValue('')
        self.Machine.SetValue('')
        self.Gantry.SetValue('')
        self.Collimator.SetValue('')


    def OnOpen(self, event):
        self.commandString = ''
        self.commandString_view.SetValue(self.commandString)
        with wx.FileDialog(self, "Open Dicom File", wildcard="Dicom (*.dcm)|*.dcm",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            self.pathname = fileDialog.GetPath()
            self.directory = fileDialog.GetDirectory()

            dicom = pydicom.dcmread(self.pathname)
            beams = dicom.BeamSequence
            allBeams = ''
            maxPairs = 0
            maxControlPoints = 0
            i = 0
            self.beam.Clear()
            for beam in beams:
                self.beam.Append(str(i) +'- ' + beam.BeamName)
                blds = beam.BeamLimitingDeviceSequence
                for bld in blds:
                    if bld.RTBeamLimitingDeviceType == "MLCX" or bld.RTBeamLimitingDeviceType == "MLCY":
                            if int(bld.NumberOfLeafJawPairs) > maxPairs:
                                maxPairs = bld.NumberOfLeafJawPairs
                if int(beam.NumberOfControlPoints) > maxControlPoints:
                    maxControlPoints = beam.NumberOfControlPoints
                allBeams = allBeams + str(i) + ','
                i += 1
            self.beam.Append(allBeams + '- ' + 'All Beams')
            listPairs = [str(x) for x in range(0, maxPairs)]
            self.leafPairFrom.Clear()
            self.leafPairFrom.Append(listPairs)
            self.leafPairTo.Clear()
            self.leafPairTo.Append(listPairs)

            listControlPoints = [str(x) for x in range(0, maxControlPoints)]
            self.controlPointsFrom.Clear()
            self.controlPointsFrom.Append(listControlPoints)
            self.controlPointsTo.Clear()
            self.controlPointsTo.Append(listControlPoints)

            jaws = beams[0].BeamLimitingDeviceSequence

    def onToggleDark(self, event):
        darkMode(self, self.dark_mode)
        if not self.dark_mode:
            self.dark_mode = True
        else:
            self.dark_mode = False

    def perform(self, event):
        if not self.commandString_view.GetValue():
            frame = PopUp('Command String is Blank, Please Add To Command String')
        else:
            script_path = 'mangle.py'
            command = 'python' + ' ' + script_path + ' ' + self.commandString_view.GetValue()
    
            subprocess.run(command)
            frame = PopUp('Output File Created At: ' + self.outFile)

    def OnJawChoice(self, event):
        if self.jaw.GetValue().split('-')[0] == '0':
            self.jawBank.Clear()
            self.jawBank.Append(['0- X1 Jaw', '1- X2 Jaw', '0,1- Both Jaws'])
        elif self.jaw.GetValue().split('-')[0] == '1':
            self.jawBank.Clear()
            self.jawBank.Append(['0- Y1 Jaw', '1- Y2 Jaw', '0,1- Both Jaws'])
        else:
            self.jawBank.Clear()
            self.jawBank.Append(['0- X1 & Y1 Jaws', '1- X2 & Y2 Jaws', '0,1- All Jaws'])

def getWidgets(parent):
    items = [parent]
    for item in parent.GetChildren():
        items.append(item)
        if hasattr(item, "GetChildren"):
            for child in item.GetChildren():
                items.append(child)
    return items

def darkMode(self, darkmode):
    dark_grey =  "#212121"
    widgets = getWidgets(self)
    for widget in widgets:
        if not darkmode:
            widget.SetBackgroundColour(dark_grey)
            widget.SetForegroundColour("White")
        else:
            widget.SetBackgroundColour(wx.NullColour)
            widget.SetForegroundColour("Black")
    self.Refresh()
    return True


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()