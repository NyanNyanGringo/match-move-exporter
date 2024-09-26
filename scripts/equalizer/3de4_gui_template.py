#
# 3DE4.script.name:	MatchMove Exporter
#
# 3DE4.script.version:	v1.0
#
# 3DE4.script.gui:	Main Window::MMExporter
#
# 3DE4.script.comment:	Easy and Fast Export for work.
#


import logging
import os
import re
import sys

import tde4

from lib.utilities.cmd_utilities import run_terminal_command, correct_path_to_console_path, execute_nuke_script
from lib.utilities.nuke_utilities import generate_and_get_nuke_python_script_path


# TODO: донастроить логирование
# log_file = os.path.join(os.getenv("MATCH_MOVE_EXPORTER_PATH"), "logs", "3de4.log")
# os.makedirs(os.path.dirname(log_file), exist_ok=True)
#
# logging.basicConfig(
#     filename=log_file,
#     level=logging.DEBUG if os.getenv("DEV") else logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
#
# # Создаем обработчик для вывода в консоль (stdout)
# console_handler = logging.StreamHandler(sys.stdout)
#
# # Настраиваем формат для консольного вывода (можно использовать тот же формат, что и для файла)
# console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(console_formatter)
#
# # Добавляем консольный обработчик к текущему логгеру
# logger = logging.getLogger()  # Получаем корневой логгер
# logger.addHandler(console_handler)
#
# # Пример логирования
# logger.debug("Это сообщение для отладки.")
# logger.info("Это информационное сообщение.")
# logger.warning("Это предупреждение.")
# logger.error("Это ошибка.")
# logger.critical("Это критическая ошибка.")


NUKE_SCRIPT = r"C:\Users\user\github\MatchMoveExporter\test_files\sh020\v001\sh020_track_v001.nk"
NUKE_EXECUTABLE = os.getenv("NUKE_EXECUTABLE_PATH")


def check_nuke_executable_path() -> bool:
	if not os.path.exists(NUKE_EXECUTABLE):
		message = f"Nuke path doesn't exists: {NUKE_EXECUTABLE}"
		tde4.postQuestionRequester("Message", message, "OK")
		return False

	if not re.fullmatch(r"^Nuke[0-9]+.[0-9]\.exe$", os.path.basename(NUKE_EXECUTABLE)):
		message = f"Incorrect Nuke executable path: {NUKE_EXECUTABLE}"
		message += f"\nExample of correct path: C:\\Program Files\\Nuke14.0v7\\Nuke14.0.exe"
		tde4.postQuestionRequester("Message", message, "OK")
		return False

	return True


def button_clicked_callback(requester, widget, action) -> None:
	print ("New callback from widget ",widget," received, action: ", action)
	print ("Put your code here...")

	if not check_nuke_executable_path():
		return

	# TODO: stopped there
	execute_nuke_script(nuke_exec_path=NUKE_EXECUTABLE,
						nuke_script_path=NUKE_SCRIPT,
						py_script_path=generate_and_get_nuke_python_script_path())


def label_changed_callback(requester, widget, action) -> None:
	print ("New callback from widget ",widget," received, action: ",action)
	print ("Put your code here...")
	return


def _MatchMoveExporterUpdate(requester) -> None:
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
