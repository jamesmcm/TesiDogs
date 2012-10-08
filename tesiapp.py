#!/usr/bin/env python
#Abandon all hope, ye who enter here

#import subprocess
#import os
import matplotlib
matplotlib.use('GTK')
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg  
import numpy as np
import matplotlib.image as mpimg
from matplotlib.figure import Figure
from matplotlib import lines
import matplotlib.pyplot as plt
import sys
import math
import datetime
import pickle
import Image #test for PIL
import pygtk
import gtk

class TesiDogs:
	"""This is the application main class - there is only one class because socialists don't believe in the class system."""
    
	def __init__(self):
	    self.builder = gtk.Builder()
	    self.builder.add_from_file("tesidog.glade")
	    dic = {"mainwindowdestroy" : gtk.main_quit, "fwdbtnclicked" : self.LoadNextFrame, "backbtnclicked" : self.LoadPreviousFrame, "loadframesbtnclicked" : self.ShowFileDialog, "file1fileset":self.FileLoad, "cancelbtnclicked":self.CancelFileLoad, "zoomoutbtnclicked": self.ZoomOut, "zoominbtnclicked":self.ZoomIn, "panleftbtnclicked":self.PanLeft, "panrightbtnclicked":self.PanRight, "pandownbtnclicked":self.PanDown, "panupbtnclicked":self.PanUp, "mainwindowkeypress":self.GetKeyPress, "basebtnclicked":self.BaseButtonClicked, "tailbtnclicked":self.TailButtonClicked, "nolinebtnclicked":self.NoLineButtonClicked, "drawtailendbtnclicked":self.DrawTailEndButtonClicked, "autorunbtnclicked":self.AutorunButtonClicked, "pklchoosefileset":self.PickleFileSet}
	    self.builder.connect_signals(dic)

	    self.conid=self.builder.get_object("statusbar").get_context_id("maps")        
	    self.curid=None

	    filterplot = gtk.FileFilter()
	    filterplot.set_name("BMP")
	    filterplot.add_pattern("*.bmp")
	    filterplot.add_pattern("*.BMP")


	    filterplot2 = gtk.FileFilter()
	    filterplot2.set_name("PKL")
	    filterplot2.add_pattern("*.pkl")
	    filterplot2.add_pattern("*.PKL")
	    #filterplot.add_pattern("*.PNG")
	    #filterplot.add_pattern("*.png")

	    self.builder.get_object("filechoose").add_filter(filterplot)
	    self.builder.get_object("pklchoose").add_filter(filterplot2)
	    self.images=[]
	    self.clickstate="none"
            self.linewidth=3.
	    self.points=[]
	    self.currentbase1=None
	    self.currentbase2=None
	    self.currenttail1=None
	    self.baseline=None
	    self.hoverline=None
	    self.tailline=None
            self.paraline=None
            self.autorun=True
            self.datafile=None
            self.datastr=None
	    self.builder.get_object("autorunbtn").set_sensitive(0)
	    self.builder.get_object("toolbar1").set_sensitive(0)
	    self.builder.get_object("pklchoose").set_sensitive(0)
            self.origin="lower"
            now = datetime.datetime.now()
            self.timestr=now.strftime("%d_%m_%H%M")
            self.textbuffer=gtk.TextBuffer()
            self.builder.get_object("dataview").set_buffer(self.textbuffer)
	def ClearLines(self):
		self.axis.clear()
		self.hoverline=None
		self.tailline=None
	def ShowFileDialog(self, widget):
		self.builder.get_object("filechoose").set_visible(1)

	def CancelFileLoad(self, widget):
		self.builder.get_object("filechoose").set_visible(0)

	def FileLoad(self, widget):
	        self.points=[]
		self.filenames = self.builder.get_object("filechoose").get_filenames()
		self.filenames.sort()

                try:
                    self.datafilename=self.filenames[0].split("/")[-1].split("_")[0]+self.timestr+".dat"
                except:
                    self.datafilename=self.filenames[0].split("/")[-1].split(".")[0]+self.timestr+".dat"
                self.builder.get_object("filechoose").set_visible(0)
                self.builder.get_object("toolbar1").set_sensitive(1)
                if (self.filenames[0].split(".")[-1]=="bmp") or (self.filenames[0].split(".")[-1]=="BMP"):
                    self.origin="lower"
                else:
                    self.origin="upper"
        #Reset other data here - TODO
		for filen in self.filenames: #no faster
			self.images.append(mpimg.imread(filen))
		self.figure=Figure()
		self.axis=self.figure.add_subplot(111)
		img=mpimg.imread(self.filenames[0])
		self.frame=0
		self.points.append({"base1":None, "base2":None, "tail1":None, "tail2":None, "angle":None, "side":None, "topbottom":None, "length":None})
		self.axis.imshow(img, origin=self.origin)
		self.canvas=FigureCanvasGTKAgg(self.figure)
		self.canvas.show()
		self.canvas.mpl_connect('motion_notify_event', self.HoverOnImage)
		self.canvas.mpl_connect('button_release_event', self.CaptureClick)
		self.builder.get_object("npbox").pack_start(self.canvas, True, True)
                self.builder.get_object("pklchoose").set_sensitive(1)
		self.SetClickState("base1")
		self.UpdateInstructions("Zoom in and click two points along the dog's feet to draw the base line")
	def LoadNextFrame(self, widget):
		xlims=self.axis.get_xlim()
		ylims=self.axis.get_ylim()
        #Load next frame

		self.ClearLines()
		self.frame+=1

                if self.curid!=None:
                    self.builder.get_object("statusbar").remove_message(self.conid, self.curid)
                
                self.curid=self.builder.get_object("statusbar").push(self.conid, 'Click mode: "'+self.clickstate+'". Autorun: ' + str(self.autorun) + '. Frame: '+ str(self.frame+1) + "/" + str(len(self.filenames)) +".")



		if (self.frame >= len(self.points)): #if image unseen, prepare dictionary
			self.points.append({"base1":self.currentbase1, "base2":self.currentbase2, "tail1":self.currenttail1, "tail2":None, "angle":None, "side":None, "topbottom":None, "length":None})

		img=self.images[self.frame]
		self.axis.imshow(img, origin=self.origin)
		self.axis.set_xlim(left=xlims[0], right=xlims[1])
		self.axis.set_ylim(top=ylims[1], bottom=ylims[0])


		if self.points[self.frame]["base2"] != None: #if already line, draw that one
			self.baseline = lines.Line2D(np.array([self.points[self.frame]["base1"][0],self.points[self.frame]["base2"][0]]), np.array([self.points[self.frame]["base1"][1],self.points[self.frame]["base2"][1]]), lw=self.linewidth, color='r', alpha=0.9)
                        self.currentbase1=(self.points[self.frame]["base1"][0], self.points[self.frame]["base1"][1])
                        self.currentbase2=(self.points[self.frame]["base2"][0], self.points[self.frame]["base2"][1])
			self.axis.add_line(self.baseline)
                        self.DrawParallelLine()


		elif (self.points[self.frame]["base2"] == None) and (self.currentbase2!=None): #if not line, use previous one
			self.baseline = lines.Line2D(np.array([self.currentbase1[0],self.currentbase2[0]]), np.array([self.currentbase1[1],self.currentbase2[1]]), lw=self.linewidth, color='r', alpha=0.9)
			self.axis.add_line(self.baseline)
                        self.DrawParallelLine()

                if self.clickstate=="none":
                    self.UpdateInstructions("Browsing mode. Use toolbar buttons to edit points. Autorun disabled. Frame " + str(self.frame+1) + "/" + str(len(self.filenames)))
                    if self.points[self.frame]["tail2"] != None: #if already line, draw that one
			self.tailline = lines.Line2D(np.array([self.points[self.frame]["tail1"][0],self.points[self.frame]["tail2"][0]]), np.array([self.points[self.frame]["tail1"][1],self.points[self.frame]["tail2"][1]]), lw=self.linewidth, color='b', alpha=0.9)
			self.axis.add_line(self.tailline)
                        self.currenttail1=(self.points[self.frame]["tail1"][0], self.points[self.frame]["tail1"][1]) #bad hack to fix parallel line
                    if (self.frame-1>=0):
                        self.builder.get_object("backbtn").set_sensitive(1)
                    else:
                        self.builder.get_object("backbtn").set_sensitive(0)                            

                    if (len(self.filenames)<=self.frame+1):
                        self.builder.get_object("fwdbtn").set_sensitive(0)
                    else:
                        self.builder.get_object("fwdbtn").set_sensitive(1)     
                    

		self.canvas.draw()

        

	def LoadPreviousFrame(self, widget):
		xlims=self.axis.get_xlim()
		ylims=self.axis.get_ylim()
        #Load next frame


		self.ClearLines()
		self.frame-=1
		img=self.images[self.frame]
		self.axis.imshow(img, origin=self.origin)
		self.axis.set_xlim(left=xlims[0], right=xlims[1])
		self.axis.set_ylim(top=ylims[1], bottom=ylims[0])

                if self.curid!=None:
                    self.builder.get_object("statusbar").remove_message(self.conid, self.curid)
                
                self.curid=self.builder.get_object("statusbar").push(self.conid, 'Click mode: "'+self.clickstate+'". Autorun: ' + str(self.autorun) + '. Frame: '+ str(self.frame+1) + "/" + str(len(self.filenames)) +".")

                if self.points[self.frame]["base2"] != None: #if already line, draw that one
                    self.baseline = lines.Line2D(np.array([self.points[self.frame]["base1"][0],self.points[self.frame]["base2"][0]]), np.array([self.points[self.frame]["base1"][1],self.points[self.frame]["base2"][1]]), lw=self.linewidth, color='r', alpha=0.9)
                    self.axis.add_line(self.baseline)
                    self.currentbase1=(self.points[self.frame]["base1"][0], self.points[self.frame]["base1"][1])
                    self.currentbase2=(self.points[self.frame]["base2"][0], self.points[self.frame]["base2"][1])
                    self.DrawParallelLine()

                if self.clickstate=="none":
                    self.UpdateInstructions("Browsing mode. Use toolbar buttons to edit points. Autorun disabled. Frame " + str(self.frame+1) + "/" + str(len(self.filenames)))
                    if self.points[self.frame]["tail2"] != None: #if already line, draw that one
			self.tailline = lines.Line2D(np.array([self.points[self.frame]["tail1"][0],self.points[self.frame]["tail2"][0]]), np.array([self.points[self.frame]["tail1"][1],self.points[self.frame]["tail2"][1]]), lw=self.linewidth, color='b', alpha=0.9)
			self.axis.add_line(self.tailline)
                        self.currenttail1=(self.points[self.frame]["tail1"][0], self.points[self.frame]["tail1"][1]) #bad hack to fix parallel line

                    if (len(self.filenames)<=self.frame+1):
                        self.builder.get_object("fwdbtn").set_sensitive(0)
                    else:
                        self.builder.get_object("fwdbtn").set_sensitive(1)
	    
                    if (self.frame-1<0):
                        self.builder.get_object("backbtn").set_sensitive(0)
                    else:
                        self.builder.get_object("backbtn").set_sensitive(1)
                            
		self.canvas.draw()
        
	def HoverOnImage(self, event):
		if event.x!=None and event.y!=None and event.xdata!=None and event.ydata!=None:
			if self.curid!=None:
				self.builder.get_object("statusbar").remove_message(self.conid, self.curid)
                
			self.curid=self.builder.get_object("statusbar").push(self.conid, 'Click mode: "'+self.clickstate+'", Autorun: ' + str(self.autorun) + '. Frame: '+ str(self.frame+1) + "/" + str(len(self.filenames)) + '. x=%d, y=%d'%(int(round(event.xdata)), int(round(event.ydata))))
			if self.clickstate=="base2":
				if self.hoverline==None:
					self.hoverline = lines.Line2D(np.array([self.points[self.frame]["base1"][0],int(round(event.xdata))]), np.array([self.points[self.frame]["base1"][1],int(round(event.ydata))]), lw=self.linewidth, color='y', alpha=0.5)
					self.axis.add_line(self.hoverline)
				else:
					self.hoverline.set_data(np.array([self.points[self.frame]["base1"][0],int(round(event.xdata))]), np.array([self.points[self.frame]["base1"][1],int(round(event.ydata))]))
				self.canvas.draw()

			if self.clickstate=="tail2":
				if self.hoverline==None:
					self.hoverline = lines.Line2D(np.array([self.points[self.frame]["tail1"][0],int(round(event.xdata))]), np.array([self.points[self.frame]["tail1"][1],int(round(event.ydata))]), lw=self.linewidth, color='y', alpha=0.5)
					self.axis.add_line(self.hoverline)
				else:
					self.hoverline.set_data(np.array([self.points[self.frame]["tail1"][0],int(round(event.xdata))]), np.array([self.points[self.frame]["tail1"][1],int(round(event.ydata))]))
				self.canvas.draw()
        


	def ZoomIn(self, widget):
		xlims=self.axis.get_xlim()
		ylims=self.axis.get_ylim()
		xchange=abs(xlims[1]-xlims[0])*0.1
		ychange=abs(ylims[1]-ylims[0])*0.1
		self.axis.set_xlim(left=xlims[0]+xchange, right=xlims[1]-xchange)
		self.axis.set_ylim(top=ylims[1]-ychange, bottom=ylims[0]+ychange)
		self.builder.get_object("npbox").remove(self.canvas)
		self.builder.get_object("npbox").pack_start(self.canvas, True, True)
        
	def ZoomOut(self, widget):
		xlims=self.axis.get_xlim()
		ylims=self.axis.get_ylim()
		xchange=abs(xlims[1]-xlims[0])*0.111
		ychange=abs(ylims[1]-ylims[0])*0.111
		self.axis.set_xlim(left=xlims[0]-xchange, right=xlims[1]+xchange)
		self.axis.set_ylim(top=ylims[1]+ychange, bottom=ylims[0]-ychange)
		self.builder.get_object("npbox").remove(self.canvas)
		self.builder.get_object("npbox").pack_start(self.canvas, True, True)

	def PanLeft(self, widget):
		xlims=self.axis.get_xlim()
		xchange=abs(xlims[1]-xlims[0])*0.1
		self.axis.set_xlim(left=xlims[0]-xchange, right=xlims[1]-xchange)
		self.builder.get_object("npbox").remove(self.canvas)
		self.builder.get_object("npbox").pack_start(self.canvas, True, True)

	def PanRight(self, widget):
		xlims=self.axis.get_xlim()
		xchange=abs(xlims[1]-xlims[0])*0.1
		self.axis.set_xlim(left=xlims[0]+xchange, right=xlims[1]+xchange)
		self.builder.get_object("npbox").remove(self.canvas)
		self.builder.get_object("npbox").pack_start(self.canvas, True, True)

	def PanUp(self, widget):
		ylims=self.axis.get_ylim()
		ychange=abs(ylims[1]-ylims[0])*0.1
		self.axis.set_ylim(top=ylims[1]+ychange, bottom=ylims[0]+ychange)
		self.builder.get_object("npbox").remove(self.canvas)
		self.builder.get_object("npbox").pack_start(self.canvas, True, True)
	    
	def PanDown(self, widget):
		ylims=self.axis.get_ylim()
		ychange=abs(ylims[1]-ylims[0])*0.1
		self.axis.set_ylim(top=ylims[1]-ychange, bottom=ylims[0]-ychange)
		self.builder.get_object("npbox").remove(self.canvas)
		self.builder.get_object("npbox").pack_start(self.canvas, True, True)
	    
	def UpdateInstructions(self, message):
		self.builder.get_object("instructions").set_label(message)
		
	def CaptureClick(self, event):
		#self.clickstate can be "none", "base1", "base2", "tail1", "tail2"
		#Datastructure is list of dicts - one list for each frame
		#dict contains  base1 point, base2 point, tail1 point, tail2 point
		#base can be changed per frame but is assumed from previous frame by default
		if self.clickstate=="none":
			return 0
		elif self.clickstate=="base1":
			self.currentbase1=(int(round(event.xdata)), int(round(event.ydata)))
			self.points[self.frame]["base1"]=(int(round(event.xdata)), int(round(event.ydata)))
			self.SetClickState("base2")
			
		elif self.clickstate=="base2":
			self.currentbase2=(int(round(event.xdata)), int(round(event.ydata)))
			self.points[self.frame]["base2"]=(int(round(event.xdata)), int(round(event.ydata)))

			self.baseline = lines.Line2D(np.array([self.points[self.frame]["base1"][0],self.points[self.frame]["base2"][0]]), np.array([self.points[self.frame]["base1"][1],self.points[self.frame]["base2"][1]]), lw=self.linewidth, color='r', alpha=0.9)
			self.axis.add_line(self.baseline)
			self.canvas.draw()
                        if self.points[self.frame]["tail2"]!=None:
                            self.CalculateAngle()
                        if self.autorun==True:
                            self.SetClickState("tail1")
                        elif self.autorun==False:
                            self.SetClickState("none")                           

		elif self.clickstate=="tail1":
			self.currenttail1=(int(round(event.xdata)), int(round(event.ydata)))
			self.points[self.frame]["tail1"]=(int(round(event.xdata)), int(round(event.ydata)))
			self.SetClickState("tail2")
                        #Draw parallel line
                        self.DrawParallelLine()
		elif self.clickstate=="tail2":

			self.points[self.frame]["tail2"]=(int(round(event.xdata)), int(round(event.ydata)))
			self.tailline = lines.Line2D(np.array([self.points[self.frame]["tail1"][0],self.points[self.frame]["tail2"][0]]), np.array([self.points[self.frame]["tail1"][1],self.points[self.frame]["tail2"][1]]), lw=self.linewidth, color='b', alpha=0.9)
			self.axis.add_line(self.tailline)
			self.canvas.draw()
                        self.CalculateAngle()
			if (len(self.filenames)<=self.frame+1):
				self.SetClickState("none")
				self.UpdateInstructions("Finished")
			else:
                            if self.autorun==True:
				self.UpdateInstructions("Click the end of the tail. Frame " + str(self.frame+2) + "/" + str(len(self.filenames)))
				self.LoadNextFrame(None)
                            elif self.autorun==False:
                                self.SetClickState("none")


        def DrawParallelLine(self):
            basem=(float(self.currentbase2[1]-self.currentbase1[1]))/(float(self.currentbase2[0]-self.currentbase1[0]))
            c=self.currentbase2[1]-(basem*self.currentbase2[0])
            ydiff=self.currenttail1[1]-((basem*self.currenttail1[0])+c)
            self.paraline = lines.Line2D(np.array([self.currentbase1[0], self.currentbase2[0]]), np.array([self.currentbase1[1]+ydiff, self.currentbase2[1]+ydiff]), lw=self.linewidth, color='r', alpha=0.3)
            self.axis.add_line(self.paraline)
            self.canvas.draw()
            
        def GetKeyPress(self, widget, event):
            if event.keyval==65307: #ESC key pressed
                self.SetClickState("none")

        def SetClickState(self, clickstate):
            if clickstate=="none":
                self.UpdateInstructions("Browsing mode. Use toolbar buttons to edit points. Autorun disabled. Frame " + str(self.frame+1) + "/" + str(len(self.filenames)))
                if self.hoverline!=None: #Remove hover line
                    self.hoverline.set_data(np.array([0,0]),np.array([0,0]))
                    self.canvas.draw()
                    self.hoverline=None

                self.builder.get_object("nolinebtn").set_sensitive(0) #Make noline button insensitive
                self.builder.get_object("basebtn").set_sensitive(1) 
                self.builder.get_object("tailbtn").set_sensitive(1) 
                self.builder.get_object("tailendbtn").set_sensitive(1) 
                #Attempt to make next/prev buttons sensitive
                if (self.frame-1>=0):
                    self.builder.get_object("backbtn").set_sensitive(1)
                if (len(self.filenames)>self.frame+1):
                    self.builder.get_object("fwdbtn").set_sensitive(1)
                self.autorun=False
                self.builder.get_object("autorunbtn").set_sensitive(1)


            elif clickstate=="base1":
                self.UpdateInstructions("Click the first base point. Frame " + str(self.frame+1) + "/" + str(len(self.filenames)))
                if self.baseline!=None:
                    self.baseline.set_data(np.array([0,0]),np.array([0,0]))
                    self.canvas.draw()
                if self.paraline!=None:
                    self.paraline.set_data(np.array([0,0]),np.array([0,0]))
                    self.canvas.draw()
                self.builder.get_object("nolinebtn").set_sensitive(1) 
                self.builder.get_object("basebtn").set_sensitive(0) 
                self.builder.get_object("tailbtn").set_sensitive(0) 
                self.builder.get_object("tailendbtn").set_sensitive(0) 
                self.builder.get_object("backbtn").set_sensitive(0)
                self.builder.get_object("fwdbtn").set_sensitive(0)

            elif clickstate=="base2":
                self.UpdateInstructions("Click the second base point. Frame " + str(self.frame+1) + "/" + str(len(self.filenames)))


            elif clickstate=="tail1":
                self.UpdateInstructions("Click the base of the tail on the dog. Frame " + str(self.frame+1) + "/" + str(len(self.filenames)))
                self.builder.get_object("nolinebtn").set_sensitive(1) 
                self.builder.get_object("basebtn").set_sensitive(0) 
                self.builder.get_object("tailbtn").set_sensitive(0) 
                self.builder.get_object("tailendbtn").set_sensitive(0) 

                self.builder.get_object("backbtn").set_sensitive(0)
                self.builder.get_object("fwdbtn").set_sensitive(0)

            elif clickstate=="tail2":
                if self.points[self.frame]["tail1"]==None:
                    self.SetClickState("none")
                    if self.curid!=None:
                        self.builder.get_object("statusbar").remove_message(self.conid, self.curid)
                
                    self.curid=self.builder.get_object("statusbar").push(self.conid, "Error: First tail point not set!")
                    return None
                else:
                    self.UpdateInstructions("Click the end of the tail. Frame " + str(self.frame+1) + "/" + str(len(self.filenames)))
                    if self.tailline!=None:
                        self.tailline.set_data(np.array([0,0]),np.array([0,0]))
                        self.canvas.draw()

                    self.builder.get_object("nolinebtn").set_sensitive(1) 
                    self.builder.get_object("basebtn").set_sensitive(0) 
                    self.builder.get_object("tailbtn").set_sensitive(0) 
                    self.builder.get_object("tailendbtn").set_sensitive(0) 

                    self.builder.get_object("backbtn").set_sensitive(0)
                    self.builder.get_object("fwdbtn").set_sensitive(0)
                
            #Push changed message to statusbar
            self.clickstate=clickstate
            if self.curid!=None:
                self.builder.get_object("statusbar").remove_message(self.conid, self.curid)
                
            self.curid=self.builder.get_object("statusbar").push(self.conid, 'Changed click mode to "'+clickstate+'". Autorun: ' + str(self.autorun) + '. Frame: '+ str(self.frame+1) + "/" + str(len(self.filenames)) +".")

        def BaseButtonClicked(self, widget):
            self.SetClickState("base1")
        def TailButtonClicked(self, widget):
            self.SetClickState("tail1")
        def DrawTailEndButtonClicked(self, widget):
            self.SetClickState("tail2")
        def NoLineButtonClicked(self, widget):
            self.SetClickState("none")
        def AutorunButtonClicked(self, widget):
            self.autorun=True
	    self.builder.get_object("autorunbtn").set_sensitive(0)
        def CalculateAngle(self):
            #Angle always measured from normal, above and below
            #Find line between tail2 and tail1
            graderror=False
            try:
                tailm=(float(self.points[self.frame]["tail2"][1]-self.points[self.frame]["tail1"][1]))/(float(self.points[self.frame]["tail2"][0]-self.points[self.frame]["tail1"][0]))
                tailc=self.points[self.frame]["tail2"][1]-(tailm*self.points[self.frame]["tail2"][0])
            except:
                #Assume divide by zero error
                poix=self.points[self.frame]["tail2"][0]
                graderror=True

            try:
                basem=(float(self.points[self.frame]["base2"][1]-self.points[self.frame]["base1"][1]))/(float(self.points[self.frame]["base2"][0]-self.points[self.frame]["base1"][0]))
                basec=self.points[self.frame]["base2"][1]-(basem*self.points[self.frame]["base2"][0])

            except:
                poix=self.points[self.frame]["base2"][0]
                graderror=True
            if graderror==False:
                poix=((tailc-basec)/(basem-tailm))

            try:
                poiy=(basem*poix)+basec
            except:
                poiy=(tailm*poix)+tailc
                #if both fail then divergent

            self.points[self.frame]["angle"]=abs(90-math.degrees(math.acos((((self.points[self.frame]["tail2"][0] - poix)*(self.points[self.frame]["base1"][0] - poix)) + ((self.points[self.frame]["tail2"][1] - poiy)*(self.points[self.frame]["base1"][1] - poiy)))/(math.sqrt( ((math.pow(self.points[self.frame]["tail2"][0] - poix,2)) + (math.pow(self.points[self.frame]["tail2"][1] - poiy,2))) * ( ((math.pow(self.points[self.frame]["base1"][0] - poix,2)) + (math.pow(self.points[self.frame]["base1"][1] - poiy,2))))) ))))

            if ((self.points[self.frame]["tail2"][0]-self.points[self.frame]["tail1"][0])>=0):
                self.points[self.frame]["side"]="R"
            else:
                self.points[self.frame]["side"]="L"
            if ((self.points[self.frame]["tail2"][1]-self.points[self.frame]["tail1"][1])>=0):
                self.points[self.frame]["topbottom"]="T"
            else:
                self.points[self.frame]["topbottom"]="B"
            self.points[self.frame]["length"]=math.sqrt(pow(self.points[self.frame]["tail2"][1]-self.points[self.frame]["tail1"][1],2) + pow(self.points[self.frame]["tail2"][0]-self.points[self.frame]["tail1"][0],2) )

            self.SaveData()
        def SaveData(self):
            #get datastr from dictionary
            #save that, pickle dictionary
            base1xlist=[]
            base1ylist=[]
            base2xlist=[]
            base2ylist=[]
            tail1xlist=[]
            tail1ylist=[]
            tail2xlist=[]
            tail2ylist=[]
            anglelist=[]
            sidelist=[]
            topbottomlist=[]
            lengthlist=[]
            
            for item in self.points:
                try:
                    base1xlist.append(item["base1"][0])
                except:
                     base1xlist.append("NA")                   
                try:
                    base1ylist.append(item["base1"][1])
                except:
                    base1ylist.append("NA")
                try:
                    base2xlist.append(item["base2"][0])
                except:
                    base2xlist.append("NA")
                try:
                    base2ylist.append(item["base2"][1])
                except:
                    base2ylist.append("NA")
                try: 
                    tail1xlist.append(item["tail1"][0])
                except:
                    tail1xlist.append("NA")
                try:
                    tail1ylist.append(item["tail1"][1])
                except:
                    tail1ylist.append("NA")
                try:
                    tail2xlist.append(item["tail2"][0])
                except:
                    tail2xlist.append("NA")
                try:
                    tail2ylist.append(item["tail2"][1])
                except:
                    tail2ylist.append("NA")
                try:
                    anglelist.append(item["angle"])
                except:
                    anglelist.append("NA")
                try:
                    sidelist.append(item["side"])
                except:
                    sidelist.append("NA")
                try:
                    topbottomlist.append(item["topbottom"])
                except:
                    topbottomlist.append("NA")
                try:
                    lengthlist.append(item["length"])
                except:
                    lengthlist.append("NA")

            for i in range(len(self.filenames)-len(self.points)):
                base1xlist.append("NA")
                base1ylist.append("NA")
                base2xlist.append("NA")
                base2ylist.append("NA")
                tail1xlist.append("NA")
                tail1ylist.append("NA")
                tail2xlist.append("NA")
                tail2ylist.append("NA")
                anglelist.append("NA")
                sidelist.append("NA")
                topbottomlist.append("NA")
                lengthlist.append("NA")

            self.datastr="id,base1x,base1y,base2x,base2y,tail1x,tail1y,tail2x,tail2y,angle,length,side,topbottom\n"
            for i in range(len(base1xlist)):
                self.datastr+=str(i+1) +","+str(base1xlist[i])+ ","+str(base1ylist[i]) + "," +str(base2xlist[i]) +"," +str(base2ylist[i]) + "," + str(tail1xlist[i]) + "," + str(tail1ylist[i]) + "," + str(tail2xlist[i]) + "," + str(tail2ylist[i]) + "," + str(anglelist[i]) + "," + str(lengthlist[i]) + "," + str(sidelist[i]) + "," + str(topbottomlist[i]) +"\n"
            
            self.textbuffer.set_text(self.datastr)
            self.datafile=open(self.datafilename, "w")
            self.datafile.write(self.datastr)
            self.datafile.close()
            picklefile=open(self.datafilename[:-3]+"pkl", "w")
            pickle.dump(self.points,picklefile)
            picklefile.close()

        def PickleFileSet(self, widget):
            self.SetClickState("none")
            pklfilename=widget.get_filenames()[0]
            picklefile=open(pklfilename, "r")
            self.points=pickle.load(picklefile)
            picklefile.close()
            self.datafilename=pklfilename[:-3]+"dat"
            #redraw canvas, load data
            self.frame=self.frame-1
            self.LoadNextFrame(None)
            self.SaveData()
            self.SetClickState("none")

if __name__ == "__main__":
	tesi = TesiDogs()
	mainloop=gtk.main()
