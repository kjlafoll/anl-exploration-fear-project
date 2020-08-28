from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty, ObservableList
from kivy.graphics import Line
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp
from functools import partial

import os
import sys
import _locale
from numpy import mean
import csv
from random import *
from time import strftime
from datetime import datetime
from math import ceil, trunc

COLOR_BLACK = [0,0,0]
COLOR_WHITE = [1,1,1]

FIXATION_SIZE = 40
FIXATION_COLOR = COLOR_WHITE
INSTRUCT_SIZE = 20
INSTRUCT_COLOR = COLOR_WHITE
LINE_SEP = .025
CS_SIZE = 0.25
US_SIZE = 0.25
CS_POS = {'center_x': 0.25, 'center_y': 0.5}
US_POS = {'center_x': 0.75, 'center_y': 0.5}

PARTIAL_PERCENT = 0.5

END_TIME = 3
POSTUS_TIME = 0.2
STAGEF_TIME = 1

DELAY_TIMES = {
	"CS_MIN": 8,
	"CS_MAX": 12,
	"US_MIN": 4,
	"US_MAX": 4,
	"TI_MIN": 0,
	"TI_MAX": 0,
	"ITI_MIN": 5.5,
	"ITI_MAX": 10.5,
}

TRACE_TIMES = {
	"CS_MIN": 6,
	"CS_MAX": 6,
	"US_MIN": 4,
	"US_MAX": 4,
	"TI_MIN": 1,
	"TI_MAX": 4,
	"ITI_MIN": 3,
	"ITI_MAX": 8,
}

RESPOND_KEY = 'spacebar'
QUIT_KEY = 'q'

DATA_FOLDER = "Data_CONDexp/"
DATA_SUBFOLDER = 'ANL_%s/'
RESOURCE_FOLDER = "Resources_CONDexp/"
US_PRESENT_FOLDER = "US_PRESENT_IMAGES/"
US_ABSENT_FOLDER = "US_ABSENT_IMAGES/"
CS_FOLDER = "CS_IMAGES/"
CUSTOM_RUN_FOLDER = "CUSTOM_RUNLISTS/"
CS_POS_NAME = 'CS_POS.png'
CS_NEG_NAME = 'CS_NEG.png'
SAVE_NAME = 'ANL_%s-CONDData%s'


textlist = []
imglist = []
response = None
data = {}

class Actions():
	def add_choice(self, key, value):
	    if value and (len(value) > 0 or type(value) == ObservableList):
	        data[key] = value
	    else:
	        if key in data:
	            del data[key]

	def next_dlg(self, slideid):
		print(data)
		self.error_message = ""
		if slideid == 'Start':
			if all(elem in list(data.keys())  for elem in ['subject_input', 'design_input']):
				print(self.parent)
				self.parent.current = data['design_input']
				if data['design_input'] == 'Preset':
					del data['design_input']
			else:
				self.error_message = "[color=ff7400][b][size=25]You filled in the form incorrectly[/size][/b][/color]\n"
		elif slideid == 'Preset':
			if all(elem in list(data.keys())  for elem in ['schedule_input', 'trials_input', 'design_input', 'habit_input']):
				ExperimentApp.game = LocalGame()
			else:
				self.error_message = "[color=ff7400][b][size=25]You filled in the form incorrectly[/size][/b][/color]\n"
		elif slideid == 'Custom':
			if all(elem in list(data.keys())  for elem in ['custom_input']):
				ExperimentApp.game = LocalGame()
			else:
				self.error_message = "[color=ff7400][b][size=25]You filled in the form incorrectly[/size][/b][/color]\n"
		if self.error_message != "":
			if 'subject_input' not in list(data.keys()) and slideid == 'Start':
				self.error_message += "\n[b]You did not enter a Participant ID[/b]\n" \
				"[b]Please enter a Participant ID[/b]\n"
			if 'design_input' not in list(data.keys()) and (slideid == 'Start' or slideid == 'Preset'):
				self.error_message += "\n[b]You did not select a Design[/b]\n" \
				"[b]Please select a Design[/b]\n"
			if 'schedule_input' not in list(data.keys()) and slideid == 'Preset':
				self.error_message += "\n[b]You did not select a Schedule[/b]\n" \
				"[b]Please select a Schedule[/b]\n"
			if 'trials_input' not in list(data.keys()) and slideid == 'Preset':
				self.error_message += "\n[b]You did not select a Trial Number[/b]\n" \
				"[b]Please select a Trial Number[/b]\n"
			if 'habit_input' not in list(data.keys()) and slideid == 'Preset':
				self.error_message += "\n[b]You did not select a Habituation Number[/b]\n" \
				"[b]Please select a Habituation Number[/b]\n"
			content = WarningPopUp(cancel=self.dismiss_popup, errors_text=self.error_message)
			self.popup = Popup(title="", separator_height=0, content=content, size_hint=(None, None), size=(400,400))
			self.popup.open()

	def dismiss_popup(self):
		self.popup.dismiss()

## GUI Classes ##
class StartScreen(Screen, Actions):
	pass

class PresetScreen(Screen, Actions):
	pass

class CustomScreen(Screen, Actions):
	labeltext = "Enter full filename of custom runlist located in %s. \nMust be csv and include .csv in filename" % (RESOURCE_FOLDER+CUSTOM_RUN_FOLDER)

class WarningPopUp(Screen):
	cancel = ObjectProperty(None)
	errors_text = StringProperty("")

## Game State Classes ##
class InstructScreen(Screen, Actions):
	pass

class StimScreen(Screen, Actions):
	pass

class LocalGame(Screen, Actions):

	action = None
	sound = None
	slidenum = None
	slideons = None

	def __init__(self):
		self.customsuccess = True
		self.pressactive = False
		self.trialnum = 1
		self.saveLoc = DATA_FOLDER+DATA_SUBFOLDER+SAVE_NAME
		self.APPEND = ''
		self.data = data
		if self.data['design_input'] == "Delay":
			self.overlap = True
		elif self.data['design_input'] == "Trace":
			self.overlap = False
		self.start()

	def start(self):
		self.saveTemplate()
		if self.data['design_input'] != 'Custom':
			self.generateTimeBank()
			self.generateUSBank()
			self.generateTrialBank()
			self.shuffleTrialBank()
			self.generateSchedules()
			self.generateHabituationTrials()
		else:
			self.loadCustom()
		if self.customsuccess == True:
			if self.trial_bank[0]['us_duration'] == "NA - Habituation":
				self.runHabitInst()
			elif self.trial_bank[0]['us_duration'] != "NA - Habituation":
				self.runCondInst()

	def generateRange(self, n, r, s): #n = number, r = range, s = sum
		sum_n = s
		rest = []
		for x in range(n):
			restRange = [y*(n-x-1) for y in r]
			myRange = [sum_n-restRange[1], sum_n-restRange[0], r[0], r[1]]
			myRange.sort()
			myRange = [myRange[1], myRange[2]]
			myNumber = uniform(myRange[0], myRange[1])
			rest.append(myNumber)
			sum_n -= myNumber
		return(rest)

	def generateTimeBank(self):
		self.cs_time = []
		self.us_time = []
		self.ti_time = []
		self.iti_time = []
		if self.data['design_input'] == "Delay":
			timedict = DELAY_TIMES
		elif self.data['design_input'] == "Trace":
			timedict = TRACE_TIMES
		for x in range(trunc(int(self.data['trials_input'])/4)):
			self.cs_time.append(uniform(timedict["CS_MIN"], timedict["CS_MAX"]))
			self.us_time.append(uniform(timedict["US_MIN"], timedict["US_MAX"]))
			self.ti_time.append(uniform(timedict["TI_MIN"], timedict["TI_MAX"]))
			self.iti_time.append(uniform(timedict["ITI_MIN"], timedict["ITI_MAX"]))
		cs_sum = mean([timedict["CS_MIN"], timedict["CS_MAX"]])*int(self.data['trials_input'])/2 - sum(self.cs_time)
		us_sum = mean([timedict["US_MIN"], timedict["US_MAX"]])*int(self.data['trials_input'])/2 - sum(self.us_time)
		ti_sum = mean([timedict["TI_MIN"], timedict["TI_MAX"]])*int(self.data['trials_input'])/2 - sum(self.ti_time)
		iti_sum = mean([timedict["ITI_MIN"], timedict["ITI_MAX"]])*int(self.data['trials_input'])/2 - sum(self.iti_time)
		self.cs_time = self.cs_time + self.generateRange(ceil(int(self.data['trials_input'])/4), [timedict["CS_MIN"], timedict["CS_MAX"]], cs_sum)
		self.us_time = self.us_time + self.generateRange(ceil(int(self.data['trials_input'])/4), [timedict["US_MIN"], timedict["US_MAX"]], us_sum)
		self.ti_time = self.ti_time + self.generateRange(ceil(int(self.data['trials_input'])/4), [timedict["TI_MIN"], timedict["TI_MAX"]], ti_sum)
		self.iti_time = self.iti_time + self.generateRange(ceil(int(self.data['trials_input'])/4), [timedict["ITI_MIN"], timedict["ITI_MAX"]], iti_sum)
		shuffle(self.cs_time)
		shuffle(self.us_time)
		shuffle(self.ti_time)
		shuffle(self.iti_time)

	def generateUSBank(self):
		us_present_pool = [x for x in os.listdir(RESOURCE_FOLDER+US_PRESENT_FOLDER)]
		us_absent_pool = [x for x in os.listdir(RESOURCE_FOLDER+US_ABSENT_FOLDER)]
		us_present_runs = trunc((int(self.data['trials_input'])/2) / len(us_present_pool))
		us_absent_runs = trunc((int(self.data['trials_input'])/2) / len(us_absent_pool))
		us_present_remainder = int(self.data['trials_input'])/2 - us_present_runs*len(us_present_pool)
		us_absent_remainder = int(self.data['trials_input'])/2 - us_absent_runs*len(us_absent_pool)
		self.us_present_image = []
		self.us_absent_image = []
		for x in range(us_present_runs):
			self.us_present_image.append(sample(us_present_pool, k=len(us_present_pool)))
		self.us_present_image.append(sample(us_present_pool, k=int(us_present_remainder)))
		self.us_present_image = [item for sublist in self.us_present_image for item in sublist]
		for x in range(us_absent_runs):
			self.us_absent_image.append(sample(us_absent_pool, k=len(us_absent_pool)))
		self.us_absent_image.append(sample(us_absent_pool, k=int(us_absent_remainder)))
		self.us_absent_image = [item for sublist in self.us_absent_image for item in sublist]

	def generateTrialBank(self):
		self.ktrial_bank = []
		for x in ["CS+", "CS-"]:
			if x == "CS+":
				usbank = self.us_present_image
			elif x == "CS-":
				usbank = self.us_absent_image
			for y in range(int(int(self.data['trials_input'])/2)):
				self.ktrial_bank.append({
					"cs_duration": self.cs_time[y],
					"us_duration": self.us_time[y],
					"traceinterval_duration": self.ti_time[y],
					"iti_duration": self.iti_time[y],
					"cs_type": x,
					"us_stimulus_name": usbank[y],
					"overlap": self.overlap
					})

	def shuffleTrialBank(self):
		attempt = 0
		self.trial_bank = []
		self.utrial_bank = self.ktrial_bank
		while len(self.utrial_bank) > 0:
			ind = randint(0,len(self.utrial_bank)-1)
			chosen = self.utrial_bank[ind]
			if len(self.trial_bank) == 0:
				attempt +=1
				if chosen['cs_type'] == "CS+":
					continue
				else:
					self.trial_bank.append(chosen)
					self.utrial_bank.pop(ind)
			elif len(self.trial_bank) == 1:
				self.trial_bank.append(chosen)
				self.utrial_bank.pop(ind)
			else:
				if chosen['cs_type'] == self.trial_bank[-1]['cs_type'] and chosen['cs_type'] == self.trial_bank[-2]['cs_type']:
					cur_utrial_bank = [x['cs_type'] for x in self.utrial_bank]
					if all(x == cur_utrial_bank[0] for x in cur_utrial_bank):
						self.utrial_bank = self.ktrial_bank
						self.trial_bank = []
						print('redo')
						print(self.ktrial_bank)
						if attempt > 10:
							break
					continue
				else:
					self.trial_bank.append(chosen)
					self.utrial_bank.pop(ind)	
		if attempt > 10:
			self.start()

	def generateSchedules(self):
		num_reinforced = ceil(PARTIAL_PERCENT*(int(self.data['trials_input'])/2))
		num_partial = trunc((1-PARTIAL_PERCENT)*(int(self.data['trials_input'])/2))
		if self.data['schedule_input'] == "Continuous":
			for i, x in enumerate(self.trial_bank):
				self.trial_bank[i]['reinforced'] = 'True'
		elif self.data['schedule_input'] == "Partial":
			rlist = ['True']*int(num_reinforced-2) + ['False']*int(num_partial)
			shuffle(rlist)
			rlist = ['True'] + rlist + ['True']
			for i, x in enumerate(self.trial_bank):
				if x['cs_type'] == "CS+":
					self.trial_bank[i]['reinforced'] = rlist[0]
					rlist.pop(0)
				else:
					self.trial_bank[i]['reinforced'] = 'True'
		elif self.data['schedule_input'] == "Continuous-Partial":
			num_reinforced = int(num_reinforced/2)
			num_partial = int(num_partial/2)
			rlist = ['True']*(num_reinforced-1) + ['False']*num_partial
			shuffle(rlist)
			rlist = ['True'] + rlist
			for i, x in enumerate(reversed(self.trial_bank)):
				if x['cs_type'] == "CS+" and len(rlist)>0:
					self.trial_bank[i]['reinforced'] = rlist[0]
					rlist.pop(0)
				else:
					self.trial_bank[i]['reinforced'] = 'True'
		elif self.data['schedule_input'] == "Partial-Continuous":
			num_reinforced = int(num_reinforced/2)
			num_partial = int(num_partial/2)
			rlist = ['True']*(num_reinforced-1) + ['False']*num_partial
			shuffle(rlist)
			rlist = ['True'] + rlist
			for i, x in enumerate(self.trial_bank):
				if x['cs_type'] == "CS+" and len(rlist)>0:
					self.trial_bank[i]['reinforced'] = rlist[0]
					rlist.pop(0)
				else:
					self.trial_bank[i]['reinforced'] = 'True'
		us_absent_pool = [x for x in os.listdir(RESOURCE_FOLDER+US_ABSENT_FOLDER)]
		us_absent_runs = trunc(([x['reinforced'] for x in self.trial_bank].count('False')) / len(us_absent_pool))
		us_absent_remainder = [x['reinforced'] for x in self.trial_bank].count('False') - us_absent_runs*len(us_absent_pool)
		us_absent_image = []
		for x in range(us_absent_runs):
			us_absent_image.append(sample(us_absent_pool, k=len(us_absent_pool)))
		us_absent_image.append(sample(us_absent_pool, k=int(us_absent_remainder)))
		us_absent_image = [item for sublist in us_absent_image for item in sublist]
		for i, x in enumerate(self.trial_bank):
			if x['reinforced'] == 'False':
				self.trial_bank[i]['us_stimulus_name'] = us_absent_image[0]
				us_absent_image.pop(0)

	def generateHabituationTrials(self):
		if self.data['habit_input'] != "None":
			habitlist = ['CS+']*int(int(self.data['habit_input'])/2) + ['CS-']*int(int(self.data['habit_input'])/2)
			rhabitlist = [self.trial_bank[1]['cs_type'], self.trial_bank[0]['cs_type']]
			while len(habitlist) > 0:
				ind = randint(0,len(habitlist)-1)
				chosen = habitlist[ind]
				if chosen == rhabitlist[-1] and chosen == rhabitlist[-2]:
					if habitlist.count(chosen) == len(habitlist):
						habitlist = ['CS+']*int(int(self.data['habit_input'])/2) + ['CS-']*int(int(self.data['habit_input'])/2)
						rhabitlist = [self.trial_bank[1]['cs_type'], self.trial_bank[0]['cs_type']]
					continue
				else:
					rhabitlist.append(chosen)
					habitlist.pop(ind)
			rhabitlist = rhabitlist[2:]
			if self.data['design_input'] == "Delay":
				timedict = DELAY_TIMES
			elif self.data['design_input'] == "Trace":
				timedict = TRACE_TIMES
			for x in rhabitlist:
				self.trial_bank.insert(0, {
					"cs_duration": mean([timedict['CS_MIN'], timedict['CS_MAX']]),
					"us_duration": "NA - Habituation",
					"traceinterval_duration": mean([timedict['TI_MIN'], timedict['TI_MAX']]),
					"iti_duration": mean([timedict['ITI_MIN'], timedict['ITI_MAX']]),
					"cs_type": x,
					"us_stimulus_name": "NA - Habituation",
					"reinforced": "NA - Habituation",
					"overlap": "NA - Habituation"
					})

	def loadCustom(self):
		try:
			self.trial_bank = []
			with open(RESOURCE_FOLDER+CUSTOM_RUN_FOLDER+self.data['custom_input'], newline='') as csvfile:
				reader = csv.DictReader(csvfile)
				for i, x in enumerate(reader):
					try:
						usdur = int(x['us_duration'])
					except:
						usdur = x['us_duration']
					self.trial_bank.append({
						"cs_duration": x['cs_duration'],
						"us_duration": usdur,
						"traceinterval_duration": x['traceinterval_duration'],
						"iti_duration": x['iti_duration'],
						"cs_type": x['cs_type'],
						"us_stimulus_name": x['us_stimulus_name'],
						"reinforced": x['reinforced'],
						"overlap": x['overlap']
						})
		except:
			self.customsuccess = False
			self.error_message = "[color=ff7400][b][size=25]You filled in the form incorrectly[/size][/b][/color]\n"
			self.error_message+="\n[b]Cannot find %s[/b]\n" % self.data['custom_input']
			content = WarningPopUp(cancel=self.dismiss_popup, errors_text=self.error_message)
			self.popup = Popup(title="", separator_height=0, content=content, size_hint=(None, None), size=(400,400))
			self.popup.open()

	def saveTemplate(self):
		data = {'cs_duration': [8, 11, 9, 12, 6, 6, 6, 6],
		'us_duration': ['NA - Habituation', 'NA - Habituation', 4, 4, 4, 4, 4, 4],
		'traceinterval_duration': [0, 0, 0, 0, 2, 2.5, 1.5, 2],
		'iti_duration': [6, 6, 6, 6, 4, 4, 4, 4],
		'cs_type': ['CS+', 'CS-', 'CS-', 'CS+', 'CS-', 'CS+', 'CS-', 'CS+'],
		'us_stimulus_name': ['NA - Habituation', 'NA - Habituation', 'ns.png', 'us.png', 'ns.png', 'us.png', 'ns.png', 'us.png'],
		'reinforced': ['NA - Habituation', 'NA - Habituation', 'True', 'True', 'True', 'False', 'True', 'True'],
		'overlap': ['NA - Habituation', 'NA - Habituation', 'True', 'True', 'False', 'False', 'False', 'False']
		}
		with open(RESOURCE_FOLDER+CUSTOM_RUN_FOLDER+'runlist_template.csv', 'w') as f:
			writer = csv.writer(f)
			writer.writerow(data.keys())
			writer.writerows(zip(*data.values()))

	def runHabitInst(self):
		numt = [x['us_duration'] for x in self.trial_bank].count("NA - Habituation")
		textlist = ["You will now see %s simple shapes." % numt, "", "Please attend to all images presented."]
		textStim = {}
		for i, x in enumerate(textlist):
			textStim["inst_%s" % str(i+1)] = Label(text=x, font_size=INSTRUCT_SIZE, pos_hint = {'center_x': 0.5, 'center_y': 0.5+LINE_SEP*((len(textlist)-1)/2)-LINE_SEP*i})
		sm.transition = NoTransition()
		sm.current = "Instruct"
		for x in list(textStim.keys()):
			sm.current_screen.add_widget(textStim[x])
		self.state = 'HabInst'
		self.pressactive = True
		ExperimentApp.keyboard(ExperimentApp)
		return

	def runCondInst(self):
		numt = [1 if x['us_duration'] != "NA - Habituation" else 0 for x in self.trial_bank].count(1)
		textlist = ["For the next %s trials, you will see shapes and pictures" % str(numt),
		"", "The pictures will appear shortly after the shapes.", "",
		"Your job is to press %s when you see the picture." % RESPOND_KEY, "",
		"A few moments after you respond, the picture will dissapear.", "",
		"Try not to press %s when the picture is not present." % RESPOND_KEY, "",
		"If you make too many false starts, you will not be able to participate.", "",
		"Please attend to all images presented."]
		textStim = {}
		for i, x in enumerate(textlist):
			textStim["inst_%s" % str(i+1)] = Label(text=x, font_size=INSTRUCT_SIZE, pos_hint = {'center_x': 0.5, 'center_y': 0.5+LINE_SEP*((len(textlist)-1)/2)-LINE_SEP*i})
		sm.transition = NoTransition()
		sm.current = "Instruct"
		sm.current_screen.clear_widgets()
		for x in list(textStim.keys()):
			sm.current_screen.add_widget(textStim[x])
		self.state = 'CondInst'
		self.pressactive = True
		if self.trialnum == 1:
			ExperimentApp.keyboard(ExperimentApp)
		return

	def runFixation(self, trial):
		self.trial_bank[trial-1]['fs_response_time'] = []
		if self.trial_bank[trial-1]['overlap'] == "True":
			self.trial_bank[trial-1]['overlap'] = True
		if self.trial_bank[trial-1]['overlap'] == "False":
			self.trial_bank[trial-1]['overlap'] = False
		textlist = ["+"]
		textStim = {}
		for i, x in enumerate(textlist):
			textStim["inst_%s" % str(i+1)] = Label(text=x, font_size=FIXATION_SIZE)
		sm.transition = NoTransition()
		sm.current = "Instruct"
		sm.current_screen.clear_widgets()
		for x in list(textStim.keys()):
			sm.current_screen.add_widget(textStim[x])
		self.state = 'runFixation'
		trigger = Clock.schedule_once(partial(self.runCS, trial), float(self.trial_bank[trial-1]['iti_duration']))
		return

	def runCS(self, trial, *largs):
		csstim = {'CS+': CS_POS_NAME, 'CS-': CS_NEG_NAME}
		imglist = [{'folder':CS_FOLDER, 'name':csstim[self.trial_bank[trial-1]['cs_type']], 'height':CS_SIZE, 'pos':CS_POS}]
		response = False
		self.trial_bank[trial-1]['cs_onset'] = (datetime.now() - self.starttime).total_seconds()
		if self.trial_bank[trial-1]['overlap'] == True:
			waitdur = float(self.trial_bank[trial-1]['cs_duration']) - float(self.trial_bank[trial-1]['us_duration'])
		else:
			waitdur = self.trial_bank[trial-1]['cs_duration']
		self.imgStim = {}
		for i, x in enumerate(imglist):
			self.imgStim['img_%s' % str(i+1)] = Image(source="%s" % RESOURCE_FOLDER+x['folder']+x['name'], size_hint_y=x['height'], pos_hint=x['pos'], allow_stretch=True, keep_ratio=True)
		sm.transition = NoTransition()
		sm.current = "Stim"
		sm.current_screen.clear_widgets()
		for x in list(self.imgStim.keys()):
			sm.current_screen.add_widget(self.imgStim[x])
		self.state = 'runCS'
		print(self.trial_bank[trial-1]['overlap'])
		if self.trial_bank[trial-1]['overlap'] == True or self.trial_bank[trial-1]['overlap'] == "NA - Habituation":
			trigger = Clock.schedule_once(partial(self.runUS, trial), float(waitdur))
		elif self.trial_bank[trial-1]['overlap'] == False:
			trigger = Clock.schedule_once(partial(self.runTI, trial), float(waitdur))
		print(trigger)
		return

	def runTI(self, trial, *largs):
		self.trial_bank[trial-1]['cs_offset'] = (datetime.now() - self.starttime).total_seconds()
		sm.transition = NoTransition()
		sm.current = "Stim"
		sm.current_screen.clear_widgets()
		self.state = 'runTI'
		trigger = Clock.schedule_once(partial(self.runUS, trial), float(self.trial_bank[trial-1]['traceinterval_duration']))
		return

	def runUS(self, trial, *largs):
		usexist = True
		csstim = {'CS+': CS_POS_NAME, 'CS-': CS_NEG_NAME}
		if self.trial_bank[trial-1]['cs_type'] == "CS+" and self.trial_bank[trial-1]['reinforced'] == 'True':
			imglist = [{'folder':US_PRESENT_FOLDER, 'name':self.trial_bank[trial-1]['us_stimulus_name'], 'height':US_SIZE, 'pos':US_POS}]
		else:
			try:
				int(self.trial_bank[trial-1]['us_duration'])
				imglist = [{'folder':US_ABSENT_FOLDER, 'name':self.trial_bank[trial-1]['us_stimulus_name'], 'height':US_SIZE, 'pos':US_POS}]
			except:
				usexist = False
		if usexist == True:
			if self.trial_bank[trial-1]['overlap'] == True:
				imglist.append({'folder':CS_FOLDER, 'name':csstim[self.trial_bank[trial-1]['cs_type']], 'height':CS_SIZE, 'pos':CS_POS})
			response = False
			self.imgStim = {}
			for i, x in enumerate(imglist):
				self.imgStim['img_%s' % str(i+1)] = Image(source="%s" % RESOURCE_FOLDER+x['folder']+x['name'], size_hint_y=x['height'], pos_hint=x['pos'])
			sm.transition = NoTransition()
			sm.current = "Stim"
			sm.current_screen.clear_widgets()
			for x in list(self.imgStim.keys()):
				sm.current_screen.add_widget(self.imgStim[x])
			self.state = 'runUS'
			self.pressactive = True
			self.trial_bank[trial-1]['us_onset'] = (datetime.now() - self.starttime).total_seconds()
			self.latetrigger = Clock.schedule_once(partial(self.runPostUS, trial, self.imgStim), float(self.trial_bank[trial-1]['us_duration']))
		else:
			self.trial_bank[trial-1]['us_onset'] = "NA - Habituation"
			self.trial_bank[trial-1]['us_rt'] = "NA - Habituation"
			self.trial_bank[trial-1]['us_offset'] = "NA - Habituation"
			self.saveData(trial)
		return

	def runPostUS(self, trial, imgStim, *largs):
		if self.pressactive == False:
			stoptime = (datetime.now() - self.starttime).total_seconds()
			self.trial_bank[trial-1]['us_rt'] = int((stoptime-self.trial_bank[trial-1]['us_onset'])*1000)
			# imgStim['response'] = Line(rectangle=(0,0,50,50), width=2)
			# sm.current_screen.canvas.add(imgStim['response'])
			trigger = Clock.schedule_once(partial(self.runStageF, trial), POSTUS_TIME)
		else:
			self.trial_bank[trial-1]['us_rt'] = 'NR'
			self.runStageF(trial)
		return

	def runStageF(self, trial, *largs):
		if self.trial_bank[trial-1]['us_rt'] != 'NR':
			textlist = ["GOOD"]
		else:
			textlist = ['NO RESPONSE']
		if len(self.trial_bank[trial-1]['fs_response_time']) > 0:
			textlist.append('')
			textlist.append("FALSE START DETECTED EARLIER")
		textStim = {}
		for i, x in enumerate(textlist):
			textStim["inst_%s" % str(i+1)] = Label(text=x, font_size=FIXATION_SIZE, pos_hint = {'center_x': 0.5, 'center_y': 0.5+LINE_SEP*((len(textlist)-1)/2)-LINE_SEP*i})
		sm.transition = NoTransition()
		sm.current = "Instruct"
		sm.current_screen.clear_widgets()
		for x in list(textStim.keys()):
			sm.current_screen.add_widget(textStim[x])
		trigger = Clock.schedule_once(partial(self.saveData, trial), STAGEF_TIME)
		return

	def runStageE(self): #END SCREEN
		textlist = ["END OF TASK"]
		self.experiment.current = "instruct"
		self.state.actionWait(END_TIME)
		return

	def saveData(self, trial, *largs):
		sm.current_screen.clear_widgets()
		stoptime = (datetime.now() - self.starttime).total_seconds()
		self.trial_bank[trial-1]['us_offset'] = stoptime
		if self.trial_bank[trial-1]['overlap'] == True:
			self.trial_bank[trial-1]['cs_offset'] = stoptime
		if not os.path.exists(DATA_FOLDER+DATA_SUBFOLDER % self.data['subject_input']):
			os.mkdir(DATA_FOLDER+DATA_SUBFOLDER % self.data['subject_input'])
		saveFrame = []
		titleFrame = []
		self.trial_bank[trial-1]['trial'] = trial
		self.trial_bank[trial-1]['id'] = self.data['subject_input']
		for x in list(self.trial_bank[trial-1].keys()):
			saveFrame.append(self.trial_bank[trial-1][x])
			if trial == 1:
				titleFrame.append(x)
		for i, x in enumerate(saveFrame):
			saveFrame[i] = str(x)
		with open(self.saveLoc % (self.data['subject_input'], self.data['subject_input'], '_temp.txt'), 'a') as file:
			if trial == 1:
				file.write('\t'.join(titleFrame[0:]) + '\n')
			file.write('\t'.join(saveFrame[0:]) + '\n')
		if trial == len(self.trial_bank):
			self.finalSave(self.APPEND)
			self.runStageE()
		elif self.trial_bank[trial]['us_duration'] != "NA - Habituation" and self.trial_bank[trial-1]['us_duration'] == "NA - Habituation":
			self.trialnum += 1
			self.runCondInst()
		else:
			self.trialnum += 1
			self.runFixation(self.trialnum)


	def finalSave(self, endcap):
		finaltime = strftime('%H_%M_%S')
		try:
			os.rename(self.saveLoc % (self.data['subject_input'], self.data['subject_input'], '_temp.txt'),
				self.saveLoc % (self.data['subject_input'], self.data['subject_input'], '_' + finaltime + endcap + '.txt'))
		except:
			pass

Builder.load_file("experiment.kv")
sm = ScreenManager()
sm.add_widget(StartScreen())
sm.add_widget(PresetScreen())
sm.add_widget(CustomScreen())
sm.add_widget(InstructScreen())
sm.add_widget(StimScreen())
sm.add_widget(WarningPopUp())
sm.current = "Start"

class ExperimentApp(App):
    """
    Main Application Class
    """
    held = False
    def __init__(self, **kwargs):
    	super(ExperimentApp, self).__init__(**kwargs)
    	self.game = None

    def keyboard(self):
    	self._keyboard = Window.request_keyboard(self.closed, None)
    	self._keyboard.bind(on_key_down=self.press, on_key_up=self.release)

    def closed(self):
    	self._keyboard.unbind(on_key_down=self.press)
    	self._keyboard = None

    def press(self, keyboard, keycode, text):
    	if ExperimentApp.held == False:
    		ExperimentApp.held = True
	    	if keyboard[1] == RESPOND_KEY and ExperimentApp.game.pressactive == True:
	    		ExperimentApp.game.pressactive = False
	    		if ExperimentApp.game.state == 'HabInst':
	    			ExperimentApp.game.starttime = datetime.now()
	    			ExperimentApp.game.runFixation(ExperimentApp.game.trialnum)
	    		elif ExperimentApp.game.state == 'CondInst':
	    			ExperimentApp.game.starttime = datetime.now()
	    			ExperimentApp.game.runFixation(ExperimentApp.game.trialnum)
	    		elif ExperimentApp.game.state in 'runUS':
	    			ExperimentApp.game.latetrigger.cancel()
	    			ExperimentApp.game.runPostUS(ExperimentApp.game.trialnum, ExperimentApp.game.imgStim)
	    	elif keyboard[1] == RESPOND_KEY and ExperimentApp.game.pressactive == False:
	    		ExperimentApp.game.trial_bank[ExperimentApp.game.trialnum-1]['fs_response_time'].append((datetime.now() - ExperimentApp.game.starttime).total_seconds())

    def release(self, keyboard):
    	if keyboard[1] == RESPOND_KEY:
    		ExperimentApp.held = False


    def build(self):
    	return sm

if __name__ == '__main__':
    ExperimentApp().run()