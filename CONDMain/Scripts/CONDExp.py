modules = [['psychopy', ['gui', 'monitors', 'core']],
['psychopy.visual', ['TextStim', 'ImageStim', 'Rect', 'Window']],
['psychopy.event', ['getKeys', 'waitKeys']],
['pygame'],
['numpy', ['mean']],
['pandas'],
['PyQt5']
]

import os, sys, subprocess, warnings, csv
from random import *
from time import strftime
from datetime import datetime
from math import ceil, trunc

for library in modules:
	try:
		if len(library) > 1:
			for x in library[1]:
				exec("from {module} import {submodule}".format(module=library[0], submodule=x))
		elif len(library) == 1:
			exec("import {module}".format(module=library[0]))
	except Exception as e:
		try:
			subprocess.check_call([sys.executable, "-m", "pip", "install", library[0]])
		except:
			try:
				subprocess.check_call([sys.executable, "-m", "pip3", "install", library[0]])
			except:
				print("Cannot pip install %s library. Check pip before continuing. Remember, you cannot install libraries via pip within the PsychoPy app." % library[0])

warnings.filterwarnings("ignore")

MONITOR_WIDTH = 50
MONITOR_DIST = 55
MONITOR_SIZE = [1280,800]
MONITOR_UNITS = 'norm'
WINDOW_SIZE = (1200,900)

COLOR_BLACK = [0,0,0]
COLOR_WHITE = [1,1,1]

FIXATION_SIZE = .25
FIXATION_COLOR = COLOR_WHITE
INSTRUCT_SIZE = .075
INSTRUCT_COLOR = COLOR_WHITE
LINE_SEP = .05
CS_SIZE = .4
US_SIZE = .4
CS_POS = (0,-.4)
US_POS = (0,.4)

PARTIAL_PERCENT = 0.5

END_TIME = 3

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

RESPOND_KEY = 'space'
QUIT_KEY = 'q'

DATA_FOLDER = os.path.join('..','Data_CONDexp/')
DATA_SUBFOLDER = 'ANL_%s/'
RESOURCE_FOLDER = os.path.join('..','Resources_CONDexp/')
US_PRESENT_FOLDER = "US_PRESENT_IMAGES/"
US_ABSENT_FOLDER = "US_ABSENT_IMAGES/"
CS_FOLDER = "CS_IMAGES/"
CUSTOM_RUN_FOLDER = "CUSTOM_RUNLISTS/"
CS_POS_NAME = 'CS_POS.png'
CS_NEG_NAME = 'CS_NEG.png'
SAVE_NAME = 'ANL_%s-CONDData%s'

def generateRange(n, r, s): #n = number, r = range, s = sum
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

class LocalGame:

	action = None
	sound = None
	slidenum = None
	slideons = None

	def __init__(self):
		self.generateDLG()
		self.localGraphics = GameGraphics()
		self.state = Interact()
		self.saveLoc = DATA_FOLDER+DATA_SUBFOLDER+SAVE_NAME
		self.APPEND = ''
		self.start()

	def start(self):
		self.saveTemplate()
		if self.design_input != 'Custom':
			self.generateTimeBank()
			self.generateUSBank()
			self.generateTrialBank()
			self.shuffleTrialBank()
			self.generateSchedules()
			self.generateHabituationTrials()
		else:
			self.loadCustom()

	def generateDLG(self):
		dlg = gui.Dlg(title="CONDexp")
		dlg.addText("Experiment Parameters")
		dlg.addField("Participant ID")
		dlg.addField("Design", choices=['Preset', 'Custom'])
		input_data = dlg.show()
		if dlg.OK == False:
			core.quit()
		self.subject_input = input_data[0]
		self.design_input = input_data[1]
		if self.design_input == 'Preset':
			dlg = gui.Dlg(title="CONDexp")
			dlg.addText("Experiment Parameters")
			dlg.addField("Schedule", choices=["Continuous", "Partial", "Continuous-Partial", "Partial-Continuous"])
			dlg.addField("Trials", choices=["10", "20", "40"])
			dlg.addField("Design", choices=["Delay", "Trace"])
			dlg.addField("Habit", choices=["4", "8", "None"]) #number of trials for the habituation phase
			input_data = dlg.show()
			if dlg.OK == False:
				core.quit()
			self.schedule_input = input_data[0]
			self.trials_input = input_data[1]
			self.design_input = input_data[2]
			self.habit_input = input_data[3]
			if self.design_input == "Delay":
				self.overlap = "True"
			elif self.design_input == "Trace":
				self.overlap = "False"
		else:
			dlg = gui.Dlg(title="CONDexp")
			dlg.addText("Experiment Parameters")
			dlg.addField("Enter full filename of custom runlist located in %s. \nMust be csv and include .csv in filename" % (RESOURCE_FOLDER+CUSTOM_RUN_FOLDER))
			input_data = dlg.show()
			if dlg.OK == False:
				core.quit()
			self.custom_input = input_data[0]

	def generateTimeBank(self):
		self.cs_time = []
		self.us_time = []
		self.ti_time = []
		self.iti_time = []
		if self.design_input == "Delay":
			timedict = DELAY_TIMES
		elif self.design_input == "Trace":
			timedict = TRACE_TIMES
		for x in range(trunc(int(self.trials_input)/4)):
			self.cs_time.append(uniform(timedict["CS_MIN"], timedict["CS_MAX"]))
			self.us_time.append(uniform(timedict["US_MIN"], timedict["US_MAX"]))
			self.ti_time.append(uniform(timedict["TI_MIN"], timedict["TI_MAX"]))
			self.iti_time.append(uniform(timedict["ITI_MIN"], timedict["ITI_MAX"]))
		cs_sum = mean([timedict["CS_MIN"], timedict["CS_MAX"]])*int(self.trials_input)/2 - sum(self.cs_time)
		us_sum = mean([timedict["US_MIN"], timedict["US_MAX"]])*int(self.trials_input)/2 - sum(self.us_time)
		ti_sum = mean([timedict["TI_MIN"], timedict["TI_MAX"]])*int(self.trials_input)/2 - sum(self.ti_time)
		iti_sum = mean([timedict["ITI_MIN"], timedict["ITI_MAX"]])*int(self.trials_input)/2 - sum(self.iti_time)
		self.cs_time = self.cs_time + generateRange(ceil(int(self.trials_input)/4), [timedict["CS_MIN"], timedict["CS_MAX"]], cs_sum)
		self.us_time = self.us_time + generateRange(ceil(int(self.trials_input)/4), [timedict["US_MIN"], timedict["US_MAX"]], us_sum)
		self.ti_time = self.ti_time + generateRange(ceil(int(self.trials_input)/4), [timedict["TI_MIN"], timedict["TI_MAX"]], ti_sum)
		self.iti_time = self.iti_time + generateRange(ceil(int(self.trials_input)/4), [timedict["ITI_MIN"], timedict["ITI_MAX"]], iti_sum)
		shuffle(self.cs_time)
		shuffle(self.us_time)
		shuffle(self.ti_time)
		shuffle(self.iti_time)

	def generateUSBank(self):
		us_present_pool = [x for x in os.listdir(RESOURCE_FOLDER+US_PRESENT_FOLDER)]
		us_absent_pool = [x for x in os.listdir(RESOURCE_FOLDER+US_ABSENT_FOLDER)]
		us_present_runs = trunc((int(self.trials_input)/2) / len(us_present_pool))
		us_absent_runs = trunc((int(self.trials_input)/2) / len(us_absent_pool))
		us_present_remainder = int(self.trials_input)/2 - us_present_runs*len(us_present_pool)
		us_absent_remainder = int(self.trials_input)/2 - us_absent_runs*len(us_absent_pool)
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
			for y in range(int(int(self.trials_input)/2)):
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
		self.trial_bank = []
		self.utrial_bank = self.ktrial_bank
		while len(self.utrial_bank) > 0:
			ind = randint(0,len(self.utrial_bank)-1)
			chosen = self.utrial_bank[ind]
			if len(self.trial_bank) == 0:
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
					continue
				else:
					self.trial_bank.append(chosen)
					self.utrial_bank.pop(ind)	

	def generateSchedules(self):
		num_reinforced = PARTIAL_PERCENT*(int(self.trials_input)/2)
		num_partial = (1-PARTIAL_PERCENT)*(int(self.trials_input)/2)
		if self.schedule_input == "Continuous":
			for i, x in enumerate(self.trial_bank):
				self.trial_bank[i]['reinforced'] = 'True'
		elif self.schedule_input == "Partial":
			rlist = ['True']*(num_reinforced-2) + ['False']*num_partial
			shuffle(rlist)
			rlist = ['True'] + rlist + ['True']
			for i, x in enumerate(self.trial_bank):
				if x['cs_type'] == "CS+":
					self.trial_bank[i]['reinforced'] = rlist[0]
					rlist.pop(0)
				else:
					self.trial_bank[i]['reinforced'] = 'True'
		elif self.schedule_input == "Continuous-Partial":
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
		elif self.schedule_input == "Partial-Continuous":
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
		if self.habit_input != "None":
			habitlist = ['CS+']*int(int(self.habit_input)/2) + ['CS-']*int(int(self.habit_input)/2)
			rhabitlist = [self.trial_bank[1]['cs_type'], self.trial_bank[0]['cs_type']]
			while len(habitlist) > 0:
				ind = randint(0,len(habitlist)-1)
				chosen = habitlist[ind]
				if chosen == rhabitlist[-1] and chosen == rhabitlist[-2]:
					if habitlist.count(chosen) == len(habitlist):
						habitlist = ['CS+']*int(int(self.habit_input)/2) + ['CS-']*int(int(self.habit_input)/2)
						rhabitlist = [self.trial_bank[1]['cs_type'], self.trial_bank[0]['cs_type']]
					continue
				else:
					rhabitlist.append(chosen)
					habitlist.pop(ind)
			rhabitlist = rhabitlist[2:]
			if self.design_input == "Delay":
				timedict = DELAY_TIMES
			elif self.design_input == "Trace":
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
		customdf = pandas.read_csv(RESOURCE_FOLDER+CUSTOM_RUN_FOLDER+self.custom_input, delimiter=',', index_col=False)
		self.trial_bank = []
		for i, x in customdf.iterrows():
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
		self.localGraphics.clearDisplay()
		numt = [x['us_duration'] for x in self.trial_bank].count("NA - Habituation")
		textlist = ["You will now see %s images of simple shapes." % numt, "", "Please keep your eyes fixed on all images presented."]
		self.localGraphics.instructScreen(textlist)
		self.state.actionCont()
		return

	def runCondInst(self):
		self.localGraphics.clearDisplay()
		numt = [1 if x['us_duration'] != "NA - Habituation" else 0 for x in self.trial_bank].count(1)
		textlist = ["For the next %s trials, you will see pictures of images above pictures of shapes" % str(numt),
		"", "These images will appear shortly after the shapes.", "",
		"Your job is to press the %s button as soon as you see the new image." % RESPOND_KEY, "",
		"Please only press once. A box will appear around the image once you do.", "",
		"A few moments after you respond, the pictures will dissapear.", "",
		"Try not to press the %s button when the new images are not present. We record all responses.", "",
		"Too many false starts will disqualify your participation.", "",
		"Please attend to all images and try to respond as quickly as possible."]
		self.localGraphics.instructScreen(textlist)
		self.state.actionCont()
		return

	def runFixation(self, trial):
		if trial == 1 and self.trial_bank[trial-1]['us_duration'] == "NA - Habituation":
			self.runHabitInst()
		elif trial == 1 and self.trial_bank[trial-1]['us_duration'] != "NA - Habituation":
			self.runCondInst()
			self.starttime = datetime.now()
		elif self.trial_bank[trial-1]['us_duration'] != "NA - Habituation" and self.trial_bank[trial-2]['us_duration'] == "NA - Habituation":
			self.runCondInst()
		self.localGraphics.clearDisplay()
		self.trial_bank[trial-1]['fs_response_time'] = []
		textlist = [{'text':"+", 'height':FIXATION_SIZE, 'color':FIXATION_COLOR, 'pos':(0,0)}]
		self.localGraphics.textScreen(textlist)
		self.trial_bank[trial-1]['fs_response_time'].append(self.state.actionWait(self.trial_bank[trial-1]['iti_duration']))
		return

	def runCS(self, trial):
		self.localGraphics.clearDisplay()
		csstim = {'CS+': CS_POS_NAME, 'CS-': CS_NEG_NAME}
		cslist = [{'folder':CS_FOLDER, 'name':csstim[self.trial_bank[trial-1]['cs_type']], 'size':CS_SIZE, 'pos':CS_POS}]
		self.localGraphics.stimScreen(cslist, False)
		self.trial_bank[trial-1]['cs_onset'] = (datetime.now() - self.starttime).total_seconds()
		if self.trial_bank[trial-1]['overlap'] == "True":
			waitdur = self.trial_bank[trial-1]['cs_duration'] - self.trial_bank[trial-1]['us_duration']
		else:
			waitdur = self.trial_bank[trial-1]['cs_duration']
		self.trial_bank[trial-1]['fs_response_time'].append(self.state.actionWait(waitdur))
		return

	def runTI(self, trial):
		if self.trial_bank[trial-1]['overlap'] == "False":
			self.localGraphics.clearDisplay()
			self.trial_bank[trial-1]['cs_offset'] = (datetime.now() - self.starttime).total_seconds()
			self.trial_bank[trial-1]['fs_response_time'].append(self.state.actionWait(self.trial_bank[trial-1]['traceinterval_duration']))
		return

	def runUS(self, trial):
		usexist = True
		csstim = {'CS+': CS_POS_NAME, 'CS-': CS_NEG_NAME}
		if self.trial_bank[trial-1]['cs_type'] == "CS+" and self.trial_bank[trial-1]['reinforced'] == 'True':
			uslist = [{'folder':US_PRESENT_FOLDER, 'name':self.trial_bank[trial-1]['us_stimulus_name'], 'size':US_SIZE, 'pos':US_POS}]
		else:
			try:
				int(self.trial_bank[trial-1]['us_duration'])
				uslist = [{'folder':US_ABSENT_FOLDER, 'name':self.trial_bank[trial-1]['us_stimulus_name'], 'size':US_SIZE, 'pos':US_POS}]
			except:
				usexist = False
		if usexist == True:
			if self.trial_bank[trial-1]['overlap'] == "True":
				uslist.append({'folder':CS_FOLDER, 'name':csstim[self.trial_bank[trial-1]['cs_type']], 'size':CS_SIZE, 'pos':CS_POS})
			self.localGraphics.stimScreen(uslist, False)
			self.trial_bank[trial-1]['us_onset'] = (datetime.now() - self.starttime).total_seconds()
			self.trial_bank[trial-1]['us_rt'] = self.state.actionRespond(self.trial_bank[trial-1]['us_duration'], uslist)
			stoptime = (datetime.now() - self.starttime).total_seconds()
			self.trial_bank[trial-1]['us_offset'] = stoptime
			if self.trial_bank[trial-1]['overlap'] == "True":
				self.trial_bank[trial-1]['cs_offset'] = stoptime
		else:
			self.trial_bank[trial-1]['us_onset'] = "NA - Habituation"
			self.trial_bank[trial-1]['us_rt'] = "NA - Habituation"
			self.trial_bank[trial-1]['us_offset'] = "NA - Habituation"
		self.trial_bank[trial-1]['fs_response_time'] = [item for sublist in self.trial_bank[trial-1]['fs_response_time'] for item in sublist]
		return

	def runStageE(self): #END SCREEN
		self.localGraphics.clearDisplay()
		textlist = [{'text':"END OF TASK", 'height':FIXATION_SIZE, 'color':FIXATION_COLOR, 'pos':(0,0)}]
		self.localGraphics.textScreen(textlist)
		self.state.actionWait(END_TIME)
		return

	def saveData(self, trial):
		if not os.path.exists(DATA_FOLDER+DATA_SUBFOLDER % self.subject_input):
			os.mkdir(DATA_FOLDER+DATA_SUBFOLDER % self.subject_input)
		saveFrame = []
		titleFrame = []
		self.trial_bank[trial-1]['trial'] = trial
		self.trial_bank[trial-1]['id'] = self.subject_input
		for x in list(self.trial_bank[trial-1].keys()):
			saveFrame.append(self.trial_bank[trial-1][x])
			if trial == 1:
				titleFrame.append(x)
		for i, x in enumerate(saveFrame):
			saveFrame[i] = str(x)
		with open(self.saveLoc % (self.subject_input, self.subject_input, '_temp.txt'), 'a') as file:
			if trial == 1:
				file.write('\t'.join(titleFrame[0:]) + '\n')
			file.write('\t'.join(saveFrame[0:]) + '\n')

	def finalSave(self, endcap):
		finaltime = strftime('%H_%M_%S')
		try:
			os.rename(self.saveLoc % (self.subject_input, self.subject_input, '_temp.txt'),
				self.saveLoc % (self.subject_input, self.subject_input, '_' + finaltime + endcap + '.txt'))
		except:
			pass

class GameGraphics:

	def __init__(self):
		self.monitor = monitors.Monitor('expMonitor', width = MONITOR_WIDTH, distance = MONITOR_DIST)
		self.monitor.setSizePix(MONITOR_SIZE)
		self.monitor.saveMon()
		self.win = Window(winType='pygame', size=WINDOW_SIZE, fullscr=False, screen=0, allowGUI=False, allowStencil=False, monitor='expMonitor', color=COLOR_BLACK, colorSpace='rgb255', blendMode='avg', useFBO=True, units=MONITOR_UNITS)
		self.win.mouseVisible = False

	def instructScreen(self, textlist):
		textStim = {}
		for i, x in enumerate(textlist):
			textStim["inst_%s" % str(i+1)] = TextStim(self.win, text=x, pos=(0, LINE_SEP*((len(textlist)-1)/2)-LINE_SEP*i), height=INSTRUCT_SIZE, color=INSTRUCT_COLOR, colorSpace='rgb')
		for x in list(textStim.keys()):
			textStim[x].draw()
		self.win.update()

	def stimScreen(self, imglist, responded):
		imgStim = {}
		for i, x in enumerate(imglist):
			imgStim['img_%s' % str(i+1)] = ImageStim(self.win, image="%s" % RESOURCE_FOLDER+x['folder']+x['name'], size=x['size'], pos=x['pos'], colorSpace='rgb')
		if responded == True:
			imgStim['response'] = Rect(self.win, size=imgStim['img_1'].size+.45, pos=US_POS, lineColorSpace='rgb')
		for x in list(imgStim.keys()):
			imgStim[x].draw()
		self.win.update()

	def textScreen(self, textlist):
		textStim = {}
		for i, x in enumerate(textlist):
			textStim['text_%s' % str(i+1)] = TextStim(self.win, text=x['text'], height=x['height'], color=x['color'], pos=x['pos'], colorSpace='rgb')
		for x in list(textStim.keys()):
			textStim[x].draw()
		self.win.update()

	def clearDisplay(self):
		self.win.flip()

class Interact:

	def __init__(self):
		pygame.init()
		pygame.event.set_blocked(pygame.MOUSEMOTION)
		pygame.event.set_blocked(pygame.MOUSEBUTTONUP)
		pygame.event.set_blocked(pygame.MOUSEBUTTONDOWN)
		self.choice = None

	def actionCont(self):
		self.choice = waitKeys(keyList = [RESPOND_KEY, QUIT_KEY])
		if self.choice[0] == QUIT_KEY:
			game.finalSave(game.APPEND + '_QUIT')
			game.localGraphics.win.close()
			core.quit()

	def actionWait(self, time):
		then = datetime.now(); now = datetime.now(); diff = now-then
		interrupt = []
		while diff.total_seconds() < time:
			now = datetime.now()
			diff = now-then
			key = getKeys(keyList = [RESPOND_KEY, QUIT_KEY], timeStamped = True)
			if len(key) > 0:
				if key[-1][0] == QUIT_KEY:
					game.finalSave(game.APPEND + '_QUIT')
					game.localGraphics.win.close()
					core.quit()
				if key[-1][0] == RESPOND_KEY:
					interrupt.append((datetime.now() - game.starttime).total_seconds())
		return(interrupt)
					
	def actionRespond(self, time, images):
		rtlist = []
		then = datetime.now(); now = datetime.now(); diff = now-then
		responded = False
		while diff.total_seconds() < time:
			key = getKeys(keyList = [RESPOND_KEY, QUIT_KEY], timeStamped = True)
			if len(key) > 0:
				rt = int((now-then).total_seconds()*1000)
				if key[-1][0] == RESPOND_KEY:
					rtlist.append(rt)
					responded = True
					game.localGraphics.stimScreen(images, True)
				elif key[-1][0] == QUIT_KEY:
					game.finalSave(game.APPEND + '_QUIT')
					game.localGraphics.win.close()
					core.quit()
				else:
					pass
			if responded == True and time == 'inf':
				break
			now = datetime.now()
			diff = now-then
		if len(rtlist) == 1:
			rtlist = rtlist[0]
		if responded == False:
			rtlist = 'NR'
		return(rtlist)

if __name__ == "__main__":

	game = LocalGame()
	for i, x in enumerate(game.trial_bank):
		game.runFixation(i+1)
		game.runCS(i+1)
		game.runTI(i+1)
		game.runUS(i+1)
		game.saveData(i+1)
	game.finalSave(game.APPEND)
	game.runStageE()