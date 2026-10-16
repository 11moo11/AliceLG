# ##### BEGIN GPL LICENSE BLOCK #####
#
#  Copyright © 2021 Christian Stolze
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# MODULE DESCRIPTION:
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This includes everything that is related to the add-on preferences,
# installation of requirements, etc.

# ------------------ INTERNAL MODULES --------------------
from .globals import *

# ------------------- EXTERNAL MODULES -------------------
import bpy
from bpy.types import AddonPreferences

# ---------------- GLOBAL ADDON LOGGER -------------------
import logging
LookingGlassAddonLogger = logging.getLogger('Alice/LG')

# ------------- DEFINE ADDON PREFERENCES ----------------
# an operator that installs the python dependencies
class LOOKINGGLASS_OT_install_dependencies(bpy.types.Operator):
	bl_idname = "lookingglass.install_dependencies"
	bl_label = "Install Dependencies"
	bl_description = "Install all Python dependencies required by this add-on to the add-on directory."
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):

		# if dependencies are missing
		if not LookingGlassAddon.check_dependecies():

			import platform, subprocess
			import datetime

			# path to python
			python_path = bpy.path.abspath(sys.executable)

			# generate logfile
			logfile = open(bpy.path.abspath(LookingGlassAddon.logpath + 'side-packages-install.log'), 'a')
			LookingGlassAddonLogger.info("Installing missing side-packages. See '%s' for details." % (LookingGlassAddon.logpath + 'side-packages-install.log',))

			# ensure that pip is installed
			# NOTE: This should not be required, but a Linux user reported that
			#		on Blender 2.93 PIP was not bundled
			if platform.system() == 'Linux': subprocess.call([python_path, '-m', 'ensurepip'], stdout=logfile)

			# install the dependencies to the add-on's library path
			for module in LookingGlassAddon.external_dependecies:
				if not LookingGlassAddon.is_installed(module):

					# This is a workaround:
					# - pynng is currently not maintained anymore
					# - we compiled wheels ourselves and include them with Alice/LG
					# - pynng will be obsolete in newer versions of Alice/LG
					if module[1] == 'pynng':

						subprocess.call([python_path, '-m', 'pip', 'download', module[1], '--dest=' + os.path.join(LookingGlassAddon.libpath, 'wheels'), '--no-cache'], stdout=logfile)
						subprocess.call([python_path, '-m', 'pip', 'install', '--find-links=' + os.path.join(LookingGlassAddon.libpath, 'wheels'), module[1], '--target', LookingGlassAddon.libpath, '--no-cache', '--no-index'] + module[3], stdout=logfile)

					else:

						subprocess.call([python_path, '-m', 'pip', 'install', '--ignore-installed', module[1], '--target', LookingGlassAddon.libpath, '--no-cache'] + module[3], stdout=logfile)

			logfile.write("###################################" + '\n')
			logfile.write("Installer finished: " + str(datetime.datetime.now()) + '\n')
			logfile.write("###################################" + '\n')

			# close logfile
			logfile.close()

		return {'FINISHED'}

# Preferences pane for this Addon in the Blender preferences
class LOOKINGGLASS_PT_install_dependencies(AddonPreferences):
	bl_idname = __package__

	# render mode
	render_mode: bpy.props.EnumProperty(
									items = [('0', 'Single Camera Mode', 'The quilt is rendered using a single moving camera.'),
											 ('1', 'Multiview Camera Mode', 'The quilt is rendered using Blenders multiview mechanism.')],
									default='0',
									name="Render Mode",
									)

	# logger level
	logger_level: bpy.props.EnumProperty(
									items = [('0', 'Debug messages', 'All messages are written to the log file. This is for detailed debugging and extended bug reports'),
											 ('1', 'Info, Warnings, and Errors', 'All info, warning, and error messages are written to the log file. This is for standard bug reports'),
											 ('2', 'Only Errors', 'Only error messages are written to the log file. This is for less verbose console outputs')],
									default='1',
									name="Logging Mode",
									update=LookingGlassAddon.update_logger_levels,
									)
	console_output: bpy.props.BoolProperty(
									default=False,
									name="Log to console",
									description="Additionally log outputs to std out for debugging",
									update=LookingGlassAddon.update_logger_levels,
									)

	# need this here, since the actual logger level property is not initialized
	# before the dependencies are installed. but we want to log all details
	logger_level = 0
	console_output = False

	# draw function
	def draw(self, context):

		# Notify the user and provide an option to install
		layout = self.layout
		layout.alert = True

		# draw an Button for Installation of python dependencies
		if not LookingGlassAddon.check_dependecies():

			row = layout.row()
			row.alignment = 'EXPAND'
			row.scale_y = 0.5
			row.label(text="Some Python dependencies are missing for Alice/LG to work. These modules are")
			row = layout.row(align=True)
			row.alignment = 'EXPAND'
			row.scale_y = 0.5
			row.label(text="required to communicate with Looking Glass Bridge. If you click the button below,")
			row = layout.row(align=True)
			row.alignment = 'EXPAND'
			row.scale_y = 0.5
			row.label(text="the required modules will be installed to the addon's path. This may take a few")
			row = layout.row(align=True)
			row.alignment = 'EXPAND'
			row.scale_y = 0.5
			row.label(text="minutes, during which the Blender user interface will be unresponsive.")
			row = layout.row(align=True)
			row.alignment = 'EXPAND'
			row.operator("lookingglass.install_dependencies", icon='PLUS')

		else:

			row = layout.row()
			row.label(text="All required Python modules were installed.")
			row = layout.row()
			row.label(text="Please restart Blender to activate the changes!", icon='ERROR')


# Preferences pane for this Addon in the Blender preferences
class LOOKINGGLASS_PT_preferences(AddonPreferences):
	bl_idname = __package__
	bl_label = "Alice/LG Preferences"

	# render mode
	render_mode: bpy.props.EnumProperty(
									items = [('0', 'Current Blender instance', 'The quilt is rendered in the current Blender instance.'),
											 ('1', 'Multiple background instances', 'The quilt is rendered in multiple Blender instances running in the background.')],
									default='0',
									name="Render Mode",
									)
	# camera mode for rendering
	camera_mode: bpy.props.EnumProperty(
									items = [('0', 'Single Camera Mode', 'The quilt is rendered using a single moving camera.'),
											 ('1', 'Multiview Camera Mode', 'The quilt is rendered using Blenders multiview mechanism.')],
									default='0',
									name="Camera Mode",
									)

	# logger level
	logger_level: bpy.props.EnumProperty(
									items = [('0', 'Debug messages', 'All messages are written to the log file. This is for detailed debugging and extended bug reports'),
											 ('1', 'Info, Warnings, and Errors', 'All info, warning, and error messages are written to the log file. This is for standard bug reports'),
											 ('2', 'Only Errors', 'Only error messages are written to the log file. This is for less verbose console outputs')],
									default='1',
									name="Logging Mode",
									update=LookingGlassAddon.update_logger_levels,
									)

	console_output: bpy.props.BoolProperty(
									default=False,
									name="Log to console",
									description="Additionally log outputs to std out for debugging",
									update=LookingGlassAddon.update_logger_levels,
									)

	# experimental: use the quilt cache of Looking Glass Bridge
	bridge_cache_mode: bpy.props.BoolProperty(
									default=False,
									name="Experimental: update Looking Glass Bridge via its quilt cache",
									description="Send light fields as one named, replaced quilt in the cache of Looking Glass Bridge instead of as new images. This may reduce the memory that Bridge uses. If Bridge does not accept it, the add-on falls back to the normal way",
									)

	# default cast settings: they are used for all Blender files
	default_refresh_mode: bpy.props.EnumProperty(
									items = [('0', 'Automatic', 'Automatically refresh the light field when something changes'),
											 ('1', 'Manual', 'Refresh the light field manually')],
									default='0',
									name="Refresh Mode",
									description="Default refresh mode for casting a scene",
									update=lambda self, context: LookingGlassAddon.apply_default_settings(context),
									)
	default_preview_quality: bpy.props.EnumProperty(
									items = [('6', 'Minimum', 'Minimum-resolution preview during interactions (512x512 quilt, 32 views). Sends the least data to Looking Glass Bridge'),
											 ('1', 'Lowest', 'Low-resolution preview during interactions (1024x1024 quilt, 32 views)'),
											 ('5', 'Low', 'Skip five out of six views during interactions'),
											 ('3', 'Medium', 'Skip two out of three views during interactions'),
											 ('2', 'Best', 'Skip every second view during interactions')],
									default='6',
									name="Preview Quality",
									description="Default quality of the preview while something is changing",
									update=lambda self, context: LookingGlassAddon.apply_default_settings(context),
									)
	default_full_quality_delay: bpy.props.FloatProperty(
									default=0.7,
									min=0.2,
									max=10.0,
									step=10,
									precision=1,
									unit='TIME',
									name="Full-quality refresh",
									description="Default number of seconds without changes after which the full-quality light field is sent",
									update=lambda self, context: LookingGlassAddon.apply_default_settings(context),
									)
	default_patient_mode: bpy.props.BoolProperty(
									default=False,
									name="Patient Mode",
									description="Default for Patient Mode: wait with updating the light field until the current operator has finished",
									update=lambda self, context: LookingGlassAddon.apply_default_settings(context),
									)

	# automatic update check
	check_updates_on_startup: bpy.props.BoolProperty(
									default=True,
									name="Check for updates on startup",
									description="Check the GitHub repository for a newer version when Blender starts",
									)
	# need this here, since the actual logger level property is not initialized
	# before the dependencies are installed. but we want to log all details
	logger_level = 0
	console_output = False

	# draw function
	def draw(self, context):
		layout = self.layout

		# updater
		from .updater import draw_update_ui
		layout.prop(self, "check_updates_on_startup")
		draw_update_ui(layout)
		layout.prop(self, "bridge_cache_mode")

		# default cast settings
		box = layout.box()
		box.label(text="Default Cast Settings (for all Blender files):")
		box.prop(self, "default_refresh_mode")
		box.prop(self, "default_preview_quality")
		box.prop(self, "default_full_quality_delay")
		box.prop(self, "default_patient_mode")

		# # render mode
		# row_render_mode = layout.row()
		# column_1 = row_render_mode.column()
		# column_1.label(text="Render Mode:")
		# column_1.scale_x = 0.2
		# column_2 = row_render_mode.column()
		# column_2.prop(self, "render_mode", text="")
		# column_2.scale_x = 0.8

		# camera mode for rendering
		row_camera_mode = layout.row()
		column_1 = row_camera_mode.column()
		column_1.label(text="Camera Mode:")
		column_1.scale_x = 0.2
		column_2 = row_camera_mode.column()
		column_2.prop(self, "camera_mode", text="")
		column_2.scale_x = 0.8

		# logger level
		row_logger = layout.row()
		column_1 = row_logger.column()
		column_1.label(text="Logging Mode:")
		column_1.scale_x = 0.2
		column_2 = row_logger.column()
		column_2.prop(self, "logger_level", text="")
		column_2.scale_x = 0.55
		column_3 = row_logger.column()
		column_3.prop(self, "console_output")
		column_3.scale_x = 0.25
