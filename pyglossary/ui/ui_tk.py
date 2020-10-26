# -*- coding: utf-8 -*-
# ui_tk.py
#
# Copyright © 2009-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from pyglossary import core
from pyglossary.core import homeDir, confDir, dataDir

from pyglossary.glossary import (
	Glossary,
	homePage,
)

from .base import (
	UIBase,
	logo,
	aboutText,
	authors,
	licenseText,
)

from pyglossary.text_utils import urlToPath
import os
from os.path import join, isfile, abspath
import logging
import traceback

import tkinter as tk
from tkinter import filedialog
from tkinter import tix
from tkinter import ttk
from tkinter import font as tkFont

log = logging.getLogger("pyglossary")

# startBold = "\x1b[1m"  # Start Bold #len=4
# startUnderline = "\x1b[4m"  # Start Underline #len=4
endFormat = "\x1b[0;0;0m"  # End Format #len=8
# redOnGray = "\x1b[0;1;31;47m"
startRed = "\x1b[31m"

resDir = join(dataDir, "res")

pluginByDesc = {
	plugin.description: plugin
	for plugin in Glossary.plugins.values()
}
readDesc = [
	plugin.description
	for plugin in Glossary.plugins.values()
	if plugin.canRead
]
writeDesc = [
	plugin.description
	for plugin in Glossary.plugins.values()
	if plugin.canWrite
]


def set_window_icon(window):
	window.iconphoto(
		True,
		tk.PhotoImage(file=logo),
	)


def decodeGeometry(gs):
	"""
		example for gs: "253x252+30+684"
		returns (x, y, w, h)
	"""
	p = gs.split("+")
	w, h = p[0].split("x")
	return (int(p[1]), int(p[2]), int(w), int(h))


def encodeGeometry(x, y, w, h):
	return f"{w}x{h}+{x}+{y}"


def encodeLocation(x, y):
	return f"+{x}+{y}"


def centerWindow(win):
	"""
	centers a tkinter window
	:param win: the root or Toplevel window to center
	"""
	win.update_idletasks()
	width = win.winfo_width()
	frm_width = win.winfo_rootx() - win.winfo_x()
	win_width = width + 2 * frm_width
	height = win.winfo_height()
	titlebar_height = win.winfo_rooty() - win.winfo_y()
	win_height = height + titlebar_height + frm_width
	x = win.winfo_screenwidth() // 2 - win_width // 2
	y = win.winfo_screenheight() // 2 - win_height // 2
	win.geometry(encodeGeometry(x, y, width, height))
	win.deiconify()


def newLabelWithImage(parent, file=""):
	image = tk.PhotoImage(file=file)
	label = ttk.Label(parent, image=image)
	label.image = image  # keep a reference!
	return label


def newReadOnlyText(
	parent,
	text="",
	borderwidth=10,
	font=None,
):
	height = len(text.strip().split("\n"))
	w = tk.Text(
		parent,
		height=height,
		borderwidth=borderwidth,
		font=font,
	)
	w.insert(1.0, text)
	w.pack()
	w.configure(state="disabled")
	# if tkinter is 8.5 or above you'll want the selection background
	# to appear like it does when the widget is activated
	# comment this out for older versions of Tkinter
	w.configure(
		inactiveselectbackground=w.cget("selectbackground"),
		bg=parent.cget('bg'),
		relief="flat",
	)
	return w


class TkTextLogHandler(logging.Handler):
	def __init__(self, tktext):
		logging.Handler.__init__(self)
		#####
		tktext.tag_config("CRITICAL", foreground="#ff0000")
		tktext.tag_config("ERROR", foreground="#ff0000")
		tktext.tag_config("WARNING", foreground="#ffff00")
		tktext.tag_config("INFO", foreground="#00ff00")
		tktext.tag_config("DEBUG", foreground="#ffffff")
		###
		self.tktext = tktext

	def emit(self, record):
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		###
		if record.exc_info:
			_type, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(_type, value, tback)
			)
			if msg:
				msg += "\n"
			msg += tback_text
		###
		self.tktext.insert(
			"end",
			msg + "\n",
			record.levelname,
		)


# Monkey-patch Tkinter
# http://stackoverflow.com/questions/5191830/python-exception-logging
def CallWrapper__call__(self, *args):
	"""
		Apply first function SUBST to arguments, than FUNC.
	"""
	if self.subst:
		args = self.subst(*args)
	try:
		return self.func(*args)
	except Exception:
		log.exception("Exception in Tkinter callback:")


tk.CallWrapper.__call__ = CallWrapper__call__


class ProgressBar(tix.Frame):
	"""
	This comes from John Grayson's book "Python and Tkinter programming"
	Edited by Saeed Rasooli
	"""
	def __init__(
		self,
		rootWin=None,
		orientation="horizontal",
		min_=0,
		max_=100,
		width=100,
		height=18,
		appearance="sunken",
		fillColor="blue",
		background="gray",
		labelColor="yellow",
		labelFont="Verdana",
		labelFormat="%d%%",
		value=0,
		bd=2,
	):
		# preserve various values
		self.rootWin = rootWin
		self.orientation = orientation
		self.min = min_
		self.max = max_
		self.width = width
		self.height = height
		self.fillColor = fillColor
		self.labelFont = labelFont
		self.labelColor = labelColor
		self.background = background
		self.labelFormat = labelFormat
		self.value = value
		tix.Frame.__init__(self, rootWin, relief=appearance, bd=bd)
		self.canvas = tix.Canvas(
			self,
			height=height,
			width=width,
			bd=0,
			highlightthickness=0,
			background=background,
		)
		self.scale = self.canvas.create_rectangle(
			0,
			0,
			width,
			height,
			fill=fillColor,
		)
		self.label = self.canvas.create_text(
			width / 2,
			height / 2,
			text="",
			anchor="c",
			fill=labelColor,
			font=self.labelFont,
		)
		self.update()
		self.bind("<Configure>", self.update)
		self.canvas.pack(side="top", fill="x", expand="no")

	def updateProgress(self, newVal, newMax=None, text=""):
		if newMax:
			self.max = newMax
		self.value = newVal
		self.update(None, text)

	def update(self, event=None, labelText=""):
		# Trim the values to be between min and max
		value = self.value
		if value > self.max:
			value = self.max
		if value < self.min:
			value = self.min
		# Adjust the rectangle
		width = int(self.winfo_width())
		# width = self.width
		ratio = float(value) / self.max
		if self.orientation == "horizontal":
			self.canvas.coords(
				self.scale,
				0,
				0,
				width * ratio,
				self.height,
			)
		else:
			self.canvas.coords(
				self.scale,
				0,
				self.height * (1 - ratio),
				width,
				self.height,
			)
		# Now update the colors
		self.canvas.itemconfig(self.scale, fill=self.fillColor)
		self.canvas.itemconfig(self.label, fill=self.labelColor)
		# And update the label
		if not labelText:
			labelText = self.labelFormat % int(ratio * 100)
		self.canvas.itemconfig(self.label, text=labelText)
		# FIXME: resizing window causes problem in progressbar
		# self.canvas.move(self.label, width/2, self.height/2)
		# self.canvas.scale(self.label, 0, 0, float(width)/self.width, 1)
		self.canvas.update_idletasks()


class FormatOptionsButton(ttk.Button):
	def __init__(
		self,
		kind: "Literal['Read', 'Write']",
		values: "Dict",
		formatVar: tk.StringVar,
		master=None,
	):
		ttk.Button.__init__(
			self,
			master=master,
			text="Options",
			command=self.buttonClicked,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		self.kind = kind
		self.kindFormatsOptions = {
			"Read": Glossary.formatsReadOptions,
			"Write": Glossary.formatsWriteOptions,
		}
		self.values = values
		self.formatVar = formatVar
		self.menu = None

	def setOptionsValues(self, values):
		self.values = values

	def valueMenuItemCustomSelected(self, treev, format, optName, menu=None):
		if menu:
			menu.destroy()
			self.menu = None

		value = treev.set(optName, self.valueCol)

		dialog = tix.Toplevel(master=treev)  # bg="#0f0" does not work
		dialog.resizable(width=True, height=True)
		dialog.title(optName)
		set_window_icon(dialog)
		dialog.bind('<Escape>', lambda e: dialog.destroy())

		px, py, pw, ph = decodeGeometry(treev.winfo_toplevel().geometry())
		w = 300
		h = 100
		dialog.geometry(encodeGeometry(
			px + pw // 2 - w // 2,
			py + ph // 2 - h // 2,
			w,
			h,
		))

		frame = tix.Frame(master=dialog)

		label = ttk.Label(master=frame, text="Value for " + optName)
		label.pack()

		entry = ttk.Entry(master=frame)
		entry.insert(0, value)
		entry.pack(fill="x")

		prop = Glossary.plugins[format].optionsProp[optName]

		def okClicked(event=None):
			rawValue = entry.get()
			if not prop.validateRaw(rawValue):
				log.error(f"invalid {prop.typ} value: {optName} = {rawValue!r}")
				return
			treev.set(optName, self.valueCol, rawValue)
			treev.set(optName, "#1", "1")  # enable it
			col_w = tkFont.Font().measure(rawValue)
			if treev.column("Value", width=None) < col_w:
				treev.column("Value", width=col_w)
			dialog.destroy()

		entry.bind("<Return>", okClicked)

		label = ttk.Label(master=frame)
		label.pack(fill="x")

		button = ttk.Button(
			frame,
			text="Ok",
			command=okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		button.pack(side="right")
		###
		frame.pack(fill="x")
		dialog.focus()

	def buttonClicked(self):
		formatD = self.formatVar.get()
		if not formatD:
			return
		format = pluginByDesc[formatD].name
		options = self.kindFormatsOptions[self.kind][format]
		optionsProp = Glossary.plugins[format].optionsProp

		dialog = tix.Toplevel()  # bg="#0f0" does not work
		dialog.resizable(width=True, height=True)
		dialog.title(self.kind + " Options")
		set_window_icon(dialog)
		dialog.bind('<Escape>', lambda e: dialog.destroy())
		###
		self.valueCol = "#3"
		cols = [
			"Enable",  # bool
			"Name",  # str
			"Value",  # str
			"Comment",  # str
		]
		treev = ttk.Treeview(
			master=dialog,
			columns=cols,
			show="headings",
		)
		for col in cols:
			treev.heading(
				col,
				text=col,
				#command=lambda c=col: sortby(treev, c, 0),
			)
			# adjust the column's width to the header string
			treev.column(
				col,
				width=tkFont.Font().measure(col.title()),
			)
		###

		def valueMenuItemSelected(optName, menu, value):
			treev.set(optName, self.valueCol, value)
			treev.set(optName, "#1", "1")  # enable it
			col_w = tkFont.Font().measure(value)
			if treev.column("Value", width=None) < col_w:
				treev.column("Value", width=col_w)
			menu.destroy()
			self.menu = None

		def valueCellClicked(event, optName):
			if not optName:
				return
			prop = optionsProp[optName]
			propValues = prop.values
			if not propValues:
				if prop.customValue:
					self.valueMenuItemCustomSelected(treev, format, optName, None)
				else:
					log.error(
						f"invalid option {optName}, values={propValues}"
						f", customValue={prop.customValue}"
					)
				return
			if prop.typ == "bool":
				rawValue = treev.set(optName, self.valueCol)
				if rawValue == "":
					value = False
				else:
					value, isValid = prop.evaluate(rawValue)
					if not isValid:
						log.error(f"invalid {optName} = {rawValue!r}")
						value = False
				treev.set(optName, self.valueCol, str(not value))
				treev.set(optName, "#1", "1")  # enable it
				return
			menu = tk.Menu(
				master=treev,
				title=optName,
				tearoff=False,
			)
			self.menu = menu  # to destroy it later
			if prop.customValue:
				menu.add_command(
					label="[Custom Value]",
					command=lambda: self.valueMenuItemCustomSelected(
						treev,
						format,
						optName,
						menu,
					),
				)
			groupedValues = None
			if len(propValues) > 10:
				groupedValues = prop.groupValues()
			maxItemW = 0
			if groupedValues:
				for groupName, subValues in groupedValues.items():
					if subValues is None:
						menu.add_command(
							label=str(value),
							command=lambda value=value: valueMenuItemSelected(optName, menu, value),
						)
						maxItemW = max(maxItemW, tkFont.Font().measure(str(value)))
					else:
						subMenu = tk.Menu(tearoff=False)
						for subValue in subValues:
							subMenu.add_command(
								label=str(subValue),
								command=lambda value=subValue: valueMenuItemSelected(
									optName,
									menu,
									value,
								),
							)
						menu.add_cascade(label=groupName, menu=subMenu)
						maxItemW = max(maxItemW, tkFont.Font().measure(groupName))
			else:
				for value in propValues:
					value = str(value)
					menu.add_command(
						label=value,
						command=lambda value=value: valueMenuItemSelected(optName, menu, value),
					)

			def close():
				menu.destroy()
				self.menu = None

			menu.add_command(
				label="[Close]",
				command=close,
			)
			try:
				menu.tk_popup(
					event.x_root,
					event.y_root,
				)
				# do not pass the third argument (entry), so that the menu
				# apears where the pointer is on its top-left corner
			finally:
				# make sure to release the grab (Tk 8.0a1 only)
				menu.grab_release()

		def treeClicked(event):
			if self.menu:
				self.menu.destroy()
				self.menu = None
				return
			optName = treev.identify_row(event.y)  # optName is rowId
			if not optName:
				return
			col = treev.identify_column(event.x)  # "#1" to self.valueCol
			if col == "#1":
				value = treev.set(optName, col)
				treev.set(optName, col, 1 - int(value))
				return
			if col == self.valueCol:
				valueCellClicked(event, optName)

		treev.bind(
			"<Button-1>",
			# "<<TreeviewSelect>>", # event.x and event.y are zero
			treeClicked,
		)
		treev.pack(fill="x", expand=True)
		###
		for optName in options:
			prop = optionsProp[optName]
			comment = prop.typ
			if prop.comment:
				comment += ", " + prop.comment
			row = [
				int(optName in self.values),
				optName,
				str(self.values.get(optName, "")),
				comment,
			]
			treev.insert("", "end", values=row, iid=optName)  # iid should be rowId
			# adjust column's width if necessary to fit each value
			for col_i, value in enumerate(row):
				value = str(value)
				if col_i == 3:
					value = value.zfill(20)
					# to reserve window width, because it's hard to resize it later
				col_w = tkFont.Font().measure(value)
				if treev.column(cols[col_i], width=None) < col_w:
					treev.column(cols[col_i], width=col_w)
		###########
		frame = tix.Frame(dialog)
		###

		def okClicked():
			for optName in options:
				enable = bool(int(treev.set(optName, "#1")))
				if not enable:
					if optName in self.values:
						del self.values[optName]
					continue
				rawValue = treev.set(optName, self.valueCol)
				prop = optionsProp[optName]
				value, isValid = prop.evaluate(rawValue)
				if not isValid:
					log.error(f"invalid option value {optName} = {rawValue}")
					continue
				self.values[optName] = value
			dialog.destroy()

		button = ttk.Button(
			frame,
			text="OK",
			command=okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		button.pack(side="right")
		###
		frame.pack(fill="x")
		###
		# x, y, w, h = decodeGeometry(dialog.geometry())
		w, h = 380, 250
		# w and h are rough estimated width and height of `dialog`
		px, py, pw, ph = decodeGeometry(self.winfo_toplevel().geometry())
		# move dialog without changing the size
		dialog.geometry(encodeLocation(
			px + pw // 2 - w // 2,
			py + ph // 2 - h // 2,
		))
		dialog.focus()


class UI(tix.Frame, UIBase):
	fcd_dir_save_path = join(confDir, "ui-tk-fcd-dir")

	def __init__(self, path=""):
		rootWin = self.rootWin = tix.Tk()
		# a hack that hides the window until we move it to the center of screen
		if os.sep == "\\":  # Windows
			rootWin.attributes('-alpha', 0.0)
		else:  # Linux
			rootWin.withdraw()
		tix.Frame.__init__(self, rootWin)
		rootWin.title("PyGlossary (Tkinter)")
		rootWin.resizable(True, False)
		########
		set_window_icon(rootWin)
		rootWin.bind('<Escape>', lambda e: rootWin.quit())
		########
		self.pack(fill="x")
		# rootWin.bind("<Configure>", self.resized)
		######################
		self.config = {}
		self.glos = Glossary(ui=self)
		self._convertOptions = {}
		self.pathI = ""
		self.pathO = ""
		fcd_dir = join(homeDir, "Desktop")
		if isfile(self.fcd_dir_save_path):
			try:
				with open(self.fcd_dir_save_path, encoding="utf-8") as fp:
					fcd_dir = fp.read().strip("\n")
			except Exception:
				log.exception("")
		self.fcd_dir = fcd_dir
		######################
		notebook = tix.NoteBook(self)
		notebook.add("tabConvert", label="Convert", underline=0)
		# notebook.add("tabReverse", label="Reverse", underline=0)
		notebook.add("tabAbout", label="About", underline=0)
		convertFrame = tix.Frame(notebook.tabConvert)
		aboutFrame = tix.Frame(notebook.tabAbout)
		convertVpaned = ttk.PanedWindow(convertFrame, orient=tk.VERTICAL)
		######################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="Read from format")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			frame,
			comboVar,
			None,  # default
			*readDesc,
		)
		combo.pack(side="left")
		comboVar.trace("w", self.inputComboChanged)
		self.formatVarInputConvert = comboVar
		##
		self.readOptions = {}  # type: Dict[str, Any]
		self.writeOptions = {}  # type: Dict[str, Any]
		##
		self.readOptionsButton = FormatOptionsButton(
			"Read",
			self.readOptions,
			self.formatVarInputConvert,
			master=frame,
		)
		##
		frame.pack(fill="x")
		###################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="  Path:")
		label.pack(side="left")
		##
		entry = tix.Entry(frame)
		entry.pack(side="left", fill="x", expand=True)
		entry.bind_all("<KeyPress>", self.anyEntryChanged)
		self.entryInputConvert = entry
		##
		button = ttk.Button(
			frame,
			text="Browse",
			command=self.browseInputConvert,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.pack(side="left")
		##
		frame.pack(fill="x")
		######################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="Write to format    ")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			frame,
			comboVar,
			None,  # default
			*writeDesc,
		)
		combo.pack(side="left")
		comboVar.trace("w", self.outputComboChanged)
		self.formatVarOutputConvert = comboVar
		##
		self.writeOptionsButton = FormatOptionsButton(
			"Write",
			self.writeOptions,
			self.formatVarOutputConvert,
			master=frame,
		)
		##
		frame.pack(fill="x")
		###################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="  Path:")
		label.pack(side="left")
		##
		entry = tix.Entry(frame)
		entry.pack(side="left", fill="x", expand=True)
		entry.bind_all("<KeyPress>", self.anyEntryChanged)
		self.entryOutputConvert = entry
		##
		button = ttk.Button(
			frame,
			text="Browse",
			command=self.browseOutputConvert,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.pack(side="left")
		##
		frame.pack(fill="x")
		#######
		frame = tix.Frame(convertFrame)
		label = ttk.Label(frame, text=" " * 15)
		label.pack(
			side="left",
			fill="x",
			expand=True,
		)
		button = ttk.Button(
			frame,
			text="Convert",
			command=self.convert,
			# bg="#00e000",
			# activebackground="#22f022",
		)
		button.pack(
			side="left",
			fill="x",
			expand=True,
		)
		###
		frame.pack(fill="x")
		convertVpaned.add(frame)
		######
		convertFrame.pack(fill="x")
		#################
		console = tix.Text(convertVpaned, height=15, background="#000000")
		# self.consoleH = 15
		# sbar = Tix.Scrollbar(
		#	convertVpaned,
		#	orien=Tix.VERTICAL,
		#	command=console.yview
		# )
		# sbar.grid ( row=0, column=1)
		# console["yscrollcommand"] = sbar.set
		# console.grid()
		console.pack(fill="both", expand=True)
		log.addHandler(
			TkTextLogHandler(console),
		)
		console.insert("end", "Console:\n")
		####
		convertVpaned.add(console)
		convertVpaned.pack(fill="both", expand=True)
		self.console = console
		##################
		# convertVpaned.grid()
		# bottomFrame.grid()
		# self.grid()
		#####################
		# lbox = Tix.Listbox(convertFrame)
		# lbox.insert(0, "aaaaaaaa", "bbbbbbbbbbbbbbbbbbbb")
		# lbox.pack(fill="x")
		##############
		# __________________________ Reverse Tab __________________________ #
		# revFrame = tix.Frame(notebook.tabReverse)
		# revFrame.pack(fill="x")
		# ######################
		# frame = tix.Frame(revFrame)
		# ##
		# label = ttk.Label(frame, text="Read from format")
		# label.pack(side="left")
		# ##
		# comboVar = tk.StringVar()
		# combo = ttk.OptionMenu(
		# 	frame,
		# 	comboVar,
		# 	None, # default
		# 	*readDesc,
		# )
		# combo.pack(side="left")
		# self.combobox_r_i = comboVar
		# ##
		# frame.pack(fill="x")
		# ###################
		# frame = tix.Frame(revFrame)
		# ##
		# label = ttk.Label(frame, text="  Path:")
		# label.pack(side="left")
		# ##
		# entry = tix.Entry(frame)
		# entry.pack(side="left", fill="x", expand=True)
		# # entry.bind_all("<KeyPress>", self.entry_r_i_changed)
		# self.entry_r_i = entry
		# ##
		# button = ttk.Button(
		# 	frame,
		# 	text="Browse",
		# 	command=self.reverseBrowseInput,
		# 	# bg="#f0f000",
		# 	# activebackground="#f6f622",
		# )
		# button.pack(side="left")
		# ##
		# button = ttk.Button(
		# 	frame,
		# 	text="Load",
		# 	command=self.reverseLoad,
		# 	# bg="#7777ff",
		# )
		# button.pack(side="left")
		# ###
		# frame.pack(fill="x")
		# ###################
		# frame = tix.Frame(revFrame)
		# ##
		# label = ttk.Label(frame, text="Output Tabfile")
		# label.pack(side="left")
		# ###
		# entry = tix.Entry(frame)
		# entry.pack(side="left", fill="x", expand=True)
		# # entry.bind_all("<KeyPress>", self.entry_r_i_changed)
		# self.entry_r_o = entry
		# ##
		# button = ttk.Button(
		# 	frame,
		# 	text="Browse",
		# 	command=self.reverseBrowseOutput,
		# 	# bg="#f0f000",
		# 	# activebackground="#f6f622",
		# )
		# button.pack(side="left")
		# ##
		# frame.pack(fill="x")
		# _________________________________________________________________ #

		aboutFrame2 = tix.Frame(aboutFrame)
		##
		label = newLabelWithImage(aboutFrame2, file=logo)
		label.pack(side="left")
		##
		##
		label = ttk.Label(aboutFrame2, text=f"PyGlossary\nVersion {core.VERSION}")
		label.pack(side="left")
		##
		aboutFrame2.pack(side="top", fill="x")
		##
		style = ttk.Style(self)
		style.configure("TNotebook", tabposition="wn")
		# ws => to the left (west) and to the bottom (south)
		# wn => to the left (west) and at top
		aboutNotebook = ttk.Notebook(aboutFrame, style="TNotebook")

		aboutFrame3 = tk.Frame(aboutNotebook)
		authorsFrame = tk.Frame(aboutNotebook)
		licenseFrame = tk.Frame(aboutNotebook)

		# tabImg = tk.PhotoImage(file=join(resDir, "dialog-information-22.png"))
		# tabImg = tk.PhotoImage(file=join(resDir, "author-22.png"))

		aboutNotebook.add(
			aboutFrame3,
			text="\n About  \n",
			# image=tabImg, # not working
			# compound=tk.TOP,
			# padding=50, # not working
		)
		aboutNotebook.add(
			authorsFrame,
			text="\nAuthors\n",
		)
		aboutNotebook.add(
			licenseFrame,
			text="\nLicense\n",
		)

		label = newReadOnlyText(
			aboutFrame3,
			text=f"{aboutText}\nHome page: {homePage}",
			font=("DejaVu Sans", 11, ""),
		)
		label.pack(fill="x")

		authorsText = "\n".join(authors)
		authorsText = authorsText.replace("\t", "    ")
		label = newReadOnlyText(
			authorsFrame,
			text=authorsText,
			font=("DejaVu Sans", 11, ""),
		)
		label.pack(fill="x")

		label = newReadOnlyText(
			licenseFrame,
			text=licenseText,
			font=("DejaVu Sans", 11, ""),
		)
		label.pack(fill="x")

		aboutNotebook.pack(fill="x")

		aboutFrame.pack(fill="x")
		# _________________________________________________________________ #

		notebook.pack(fill="both", expand=True)

		# _________________________________________________________________ #

		statusBarframe = tix.Frame(self)
		clearB = ttk.Button(
			statusBarframe,
			text="Clear",
			command=self.console_clear,
			# bg="black",
			# fg="#ffff00",
			# activebackground="#333333",
			# activeforeground="#ffff00",
		)
		clearB.pack(side="left")
		####
		label = ttk.Label(statusBarframe, text="Verbosity")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			statusBarframe,
			comboVar,
			log.getVerbosity(),  # default
			0, 1, 2, 3, 4,
		)
		comboVar.trace("w", self.verbosityChanged)
		combo.pack(side="left")
		self.verbosityCombo = comboVar
		#####
		pbar = ProgressBar(statusBarframe, width=400)
		pbar.pack(side="left", fill="x", expand=True)
		self.pbar = pbar
		statusBarframe.pack(fill="x")
		self.progressTitle = ""
		# _________________________________________________________________ #
		frame3 = tix.Frame(self)
		closeB = ttk.Button(
			frame3,
			text="Close",
			command=rootWin.quit,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		closeB.pack(side="right")
		frame3.pack(fill="x")
		# _________________________________________________________________ #

		centerWindow(rootWin)
		# show the window
		if os.sep == "\\":  # Windows
			rootWin.attributes('-alpha', 1.0)
		else:  # Linux
			rootWin.deiconify()
		if path:
			self.entryInputConvert.insert(0, path)
			self.inputEntryChanged()
			self.outputEntryChanged()
			self.load()

	def verbosityChanged(self, index, value, op):
		log.setVerbosity(
			int(self.verbosityCombo.get())
		)

	def resized(self, event):
		dh = self.rootWin.winfo_height() - self.winfo_height()
		# log.debug(dh, self.consoleH)
		# if dh > 20:
		#	self.consoleH += 1
		#	self.console["height"] = self.consoleH
		#	self.console["width"] = int(self.console["width"]) + 1
		#	self.console.grid()
		# for x in dir(self):
		#	if "info" in x:
		#		log.debug(x)

	def inputComboChanged(self, *args):
		formatDesc = self.formatVarInputConvert.get()
		if not formatDesc:
			return
		self.readOptions.clear()  # reset the options, DO NOT re-assign
		format = pluginByDesc[formatDesc].name
		options = Glossary.formatsReadOptions[format]
		if options:
			self.readOptionsButton.pack(side="right")
		else:
			self.readOptionsButton.pack_forget()

	def outputComboChanged(self, *args):
		# log.debug(self.formatVarOutputConvert.get())
		formatDesc = self.formatVarOutputConvert.get()
		if not formatDesc:
			return
		self.writeOptions.clear()  # reset the options, DO NOT re-assign
		format = pluginByDesc[formatDesc].name
		options = Glossary.formatsWriteOptions[format]
		if options:
			self.writeOptionsButton.pack(side="right")
		else:
			self.writeOptionsButton.pack_forget()

	def anyEntryChanged(self, event=None):
		self.inputEntryChanged()
		self.outputEntryChanged()

	def inputEntryChanged(self, event=None):
		# char = event.keysym
		pathI = self.entryInputConvert.get()
		if self.pathI != pathI:
			if pathI.startswith("file://"):
				pathI = urlToPath(pathI)
				self.entryInputConvert.delete(0, "end")
				self.entryInputConvert.insert(0, pathI)
			if self.config["ui_autoSetFormat"]:
				formatDesc = self.formatVarInputConvert.get()
				if not formatDesc:
					inputArgs = Glossary.detectInputFormat(pathI, quiet=True)
					if inputArgs:
						format = inputArgs[1]
						plugin = Glossary.plugins.get(format)
						if plugin:
							self.formatVarInputConvert.set(plugin.description)
			self.pathI = pathI

	def outputEntryChanged(self, event=None):
		pathO = self.entryOutputConvert.get()
		if self.pathO != pathO:
			if pathO.startswith("file://"):
				pathO = urlToPath(pathO)
				self.entryOutputConvert.delete(0, "end")
				self.entryOutputConvert.insert(0, pathO)
			if self.config["ui_autoSetFormat"]:
				formatDesc = self.formatVarOutputConvert.get()
				if not formatDesc:
					outputArgs = Glossary.detectOutputFormat(
						filename=pathO,
						inputFilename=self.entryInputConvert.get(),
						quiet=True,
					)
					if outputArgs:
						outputFormat = outputArgs[1]
						self.formatVarOutputConvert.set(
							Glossary.plugins[outputFormat].description
						)
			self.pathO = pathO

	def save_fcd_dir(self):
		if not self.fcd_dir:
			return
		with open(self.fcd_dir_save_path, mode="w", encoding="utf-8") as fp:
			fp.write(self.fcd_dir)

	def browseInputConvert(self):
		path = filedialog.askopenfilename(initialdir=self.fcd_dir)
		if path:
			self.entryInputConvert.delete(0, "end")
			self.entryInputConvert.insert(0, path)
			self.inputEntryChanged()
			self.fcd_dir = os.path.dirname(path)
			self.save_fcd_dir()

	def browseOutputConvert(self):
		path = filedialog.asksaveasfilename()
		if path:
			self.entryOutputConvert.delete(0, "end")
			self.entryOutputConvert.insert(0, path)
			self.outputEntryChanged()
			self.fcd_dir = os.path.dirname(path)
			self.save_fcd_dir()

	def convert(self):
		inPath = self.entryInputConvert.get()
		if not inPath:
			log.critical("Input file path is empty!")
			return
		inFormatDesc = self.formatVarInputConvert.get()
		if not inFormatDesc:
			# log.critical("Input format is empty!");return
			inFormat = ""
		else:
			inFormat = pluginByDesc[inFormatDesc].name

		outPath = self.entryOutputConvert.get()
		if not outPath:
			log.critical("Output file path is empty!")
			return
		outFormatDesc = self.formatVarOutputConvert.get()
		if not outFormatDesc:
			log.critical("Output format is empty!")
			return
		outFormat = pluginByDesc[outFormatDesc].name

		finalOutputFile = self.glos.convert(
			inPath,
			inputFormat=inFormat,
			outputFilename=outPath,
			outputFormat=outFormat,
			readOptions=self.readOptions,
			writeOptions=self.writeOptions,
			**self._convertOptions
		)
		# if finalOutputFile:
		# 	self.status("Convert finished")
		# else:
		# 	self.status("Convert failed")
		return bool(finalOutputFile)

	def run(
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		configOptions: "Optional[Dict]" = None,
		readOptions: "Optional[Dict]" = None,
		writeOptions: "Optional[Dict]" = None,
		convertOptions: "Optional[Dict]" = None,
	):
		if inputFilename:
			self.entryInputConvert.insert(0, abspath(inputFilename))
		if outputFilename:
			self.entryOutputConvert.insert(0, abspath(outputFilename))
		
		if inputFormat:
			self.formatVarInputConvert.set(Glossary.plugins[inputFormat].description)
		if outputFormat:
			self.formatVarOutputConvert.set(Glossary.plugins[outputFormat].description)

		if reverse:
			log.error(f"Tkinter interface does not support Reverse feature")

		self.loadConfig(**configOptions)

		# must be before setting self.readOptions and self.writeOptions
		self.anyEntryChanged()

		if readOptions:
			self.readOptionsButton.setOptionsValues(readOptions)
			self.readOptions = readOptions

		if writeOptions:
			self.writeOptionsButton.setOptionsValues(writeOptions)
			self.writeOptions = writeOptions

		self._convertOptions = convertOptions
		if convertOptions:
			log.info(f"Using convertOptions={convertOptions}")

		# inputFilename and readOptions are for DB Editor
		# which is not implemented
		self.mainloop()

	def progressInit(self, title):
		self.progressTitle = title

	def progress(self, rat, text=""):
		if not text:
			text = "%" + str(int(rat * 100))
		text += " - " + self.progressTitle
		self.pbar.updateProgress(rat * 100, None, text)
		# self.pbar.value = rat * 100
		# self.pbar.update()
		self.rootWin.update()

	def console_clear(self, event=None):
		self.console.delete("1.0", "end")
		self.console.insert("end", "Console:\n")

	# def reverseBrowseInput(self):
	# 	pass

	# def reverseBrowseOutput(self):
	# 	pass

	# def reverseLoad(self):
	# 	pass


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		path = sys.argv[1]
	else:
		path = ""
	ui = UI(path)
	ui.run()
