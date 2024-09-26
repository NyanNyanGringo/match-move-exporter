#
# 3DE4.script.name:	MatchMove Exporter
#
# 3DE4.script.version:	v1.0
#
# 3DE4.script.gui:	Main Window::MMExporter
#
# 3DE4.script.comment:	Easy and Fast Export for work.
#

import tde4


def button_clicked_callback(requester,widget,action):
	print ("New callback from widget ",widget," received, action: ",action)
	print ("Put your code here...")
	return


def label_changed_callback(requester,widget,action):
	print ("New callback from widget ",widget," received, action: ",action)
	print ("Put your code here...")
	return


def _MatchMoveExporterUpdate(requester):
	print ("New update callback received, put your code here...")
	return


#
# DO NOT ADD ANY CUSTOM CODE BEYOND THIS POINT!
#

try:
	requester	= _MatchMoveExporter_requester
except (ValueError,NameError,TypeError):
	requester = tde4.createCustomRequester()
	tde4.addButtonWidget(requester,"button_export","EXPORT")
	tde4.setWidgetOffsets(requester,"button_export",60,60,30,0)
	tde4.setWidgetAttachModes(requester,"button_export","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_WIDGET","ATTACH_NONE")
	tde4.setWidgetSize(requester,"button_export",80,30)
	tde4.setWidgetCallbackFunction(requester,"button_export","button_clicked_callback")
	tde4.addTextFieldWidget(requester,"textfield_name","NAME:","sh000_00_track_v001")
	tde4.setWidgetOffsets(requester,"textfield_name",60,60,30,0)
	tde4.setWidgetAttachModes(requester,"textfield_name","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_NONE")
	tde4.setWidgetSize(requester,"textfield_name",200,20)
	tde4.setWidgetCallbackFunction(requester,"textfield_name","label_changed_callback")
	tde4.addLabelWidget(requester,"label_pattern","[seq_name]_sh<shot_number>_<task_number>_track_v000_[definition]","ALIGN_LABEL_LEFT")
	tde4.setWidgetOffsets(requester,"label_pattern",60,60,15,0)
	tde4.setWidgetAttachModes(requester,"label_pattern","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_WIDGET","ATTACH_NONE")
	tde4.setWidgetSize(requester,"label_pattern",200,20)
	tde4.setWidgetLinks(requester,"button_export","","","label_pattern","")
	tde4.setWidgetLinks(requester,"textfield_name","","","","")
	tde4.setWidgetLinks(requester,"label_pattern","","","textfield_name","")
	_MatchMoveExporter_requester = requester

#
# DO NOT ADD ANY CUSTOM CODE UP TO THIS POINT!
#

if tde4.isCustomRequesterPosted(_MatchMoveExporter_requester)=="REQUESTER_UNPOSTED":
	if tde4.getCurrentScriptCallHint()=="CALL_GUI_CONFIG_MENU":
		tde4.postCustomRequesterAndContinue(_MatchMoveExporter_requester,"MatchMove Exporter",0,0,"_MatchMoveExporterUpdate")
	else:
		tde4.postCustomRequesterAndContinue(_MatchMoveExporter_requester,"MatchMove Exporter v1.0",800,600,"_MatchMoveExporterUpdate")
else:	tde4.postQuestionRequester("MatchMove Exporter","Window/Pane is already posted, close manually first!","Ok")


