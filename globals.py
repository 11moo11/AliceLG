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
# This includes all global variables that need to be accessable from all files

# ------------------- EXTERNAL MODULES -------------------
import bpy
import sys, os, json
from bpy.props import FloatProperty, PointerProperty
from bpy.app.handlers import persistent

# ---------------- GLOBAL ADDON LOGGER -------------------
import logging
LookingGlassAddonLogger = logging.getLogger('Alice/LG')


# ------------ GLOBAL VARIABLES ---------------
# CLASS USED FOR THE IMPORTANT GLOBAL VARIABLES AND LISTS IN THIS ADDON
class LookingGlassAddon:

	# this is only for debugging purposes
	debugging_use_dummy_device = False

	# console output: if set to true, the Alice/LG and pyLightIO logger messages
	# of all levels are printed to the console. If set to falls, only warnings and
	# errors are printed to console.
	debugging_print_pylio_logger_all = False
	debugging_print_internal_logger_all = False

	# addon name
	name = None

	# path to the addon directory
	path = bpy.path.abspath(os.path.dirname(os.path.realpath(__file__)))
	tmp_path = bpy.path.abspath(path + "/tmp/")
	libpath = bpy.path.abspath(path + "/lib/")
	logpath = bpy.path.abspath(path + "/logs/")
	presetpath = bpy.path.abspath(path + "/presets/")

	# external python dependencies of the add-on
	# NOTE: The tuple has the form (import name, install name, install version, install options)
	external_dependecies = [
							('pynng', 'pynng', '', []),
							('cv2', 'opencv-python', '', ['--no-deps']),
							('pylightio', 'pylightio', '', []),
							]
	external_dependecies_installer = False

	# Blender arguments
	blender_arguments = ""
	addon_arguments = ""
	background = False

	# the pyLightIO service for display communication
	service = None

	# Lockfile
	has_lockfile = False

	# Was the frustum drawer initialized?
	FrustumInitialized = False
	FrustumRenderer = None

	# Was the hologram preview drawer initialized?
	ImageBlockRenderer = None
	ViewportBlockRenderer = None

	# The active Window and Viewport the user is currently working in
	BlenderWindow = None
	BlenderViewport = None

	# Rendering status
	RenderInvoked = False
	RenderAnimation = None

	# keymaps and mouse position
	keymap_view_3d = None
	keymap_items_view_3d_1 = None
	keymap_items_view_3d_2 = None
	keymap_image_editor = None
	keymap_items_image_editor_1 = None
	keymap_items_image_editor_2 = None
	mouse_window_x = 0
	mouse_window_y = 0
	mouse_region_x = 0
	mouse_region_y = 0


	# EXTEND PATH
	# +++++++++++++++++++++++++++++++++++++++

	# append the add-on's path to Blender's python PATH
	sys.path.insert(0, libpath)



	# ADDON CHECKS
	# +++++++++++++++++++++++++++++++++++++++
	# check if the specified module can be found in the "lib" directory
	@classmethod
	def is_installed(cls, module, debug=False):
		import importlib.machinery
		import sys
		if sys.version_info.major >= 3 or (sys.version_info.major == 3 and sys.version_info.minor >= 8):
		    from importlib.metadata import version
		else:
		    from importlib_metadata import version

		# extract info
		module_name, install_name, install_version, install_options = module

		# Try importing the module to ensure it's compatible with the current python version
		try:
			__import__(module_name)
		except ImportError as e:
			if debug: LookingGlassAddonLogger.info(" [#] Could not import module '%s' (might be for different python version): %s" % (module_name, e))
			return False

		# try to find the module in the "lib" directory
		module_spec = (importlib.machinery.PathFinder().find_spec(module_name, [cls.libpath]))
		if module_spec:
			if install_version:

				# check if the installed module version fits
				version_comparison = [ a >= b for a,b in zip(list(map(int, version(install_name).split('.'))), list(map(int, install_version.split('.'))))]
				if all(version_comparison):
					if debug: LookingGlassAddonLogger.info(" [#] Found module '%s' v.%s." % (module_name, version(install_name)))
					return True

				else:
					if debug: LookingGlassAddonLogger.info(" [#] Found module '%s' v.%s, but require version %s." % (module_name, version(install_name), install_version))
					return False
			else:
				if debug: LookingGlassAddonLogger.info(" [#] Found module '%s' v.%s." % (module_name, version(install_name)))
				return True

		if debug: LookingGlassAddonLogger.info(" [#] Could not find module '%s'." % module_name)
		return False

	# check if all defined dependencies can be found in the "lib" directory
	@classmethod
	def check_dependecies(cls, debug=False):

		# status
		found_all = True

		# are all modules in the packages list available in the "lib" directory?
		for module in cls.external_dependecies:
			if not cls.is_installed(module, debug):
				found_all = False

		return found_all

	# unload all dependencies
	@classmethod
	def unload_dependecies(cls):

		# if the addon is not in installer mode
		if not LookingGlassAddon.external_dependecies_installer:

			# are all modules in the packages list available in the "lib" directory?
			for module in cls.external_dependecies:

				# get names
				module_name, install_name, install_version, install_options = module

				# unload the module
				# NOTE: pyLightIO is pure python, so its submodules must be unloaded too.
				#		Otherwise re-enabling the add-on in the same session (e.g., after
				#		installing an update) fails with "module 'pylightio' has no
				#		attribute 'lookingglass'".
				if module_name == 'pylightio':
					for name in [n for n in sys.modules if n.startswith('pylightio.')]: del sys.modules[name]
				sys.modules.pop(module_name, None)
				#del module_name



	# memory used by this Blender process in MB (for debugging memory problems)
	@staticmethod
	def process_memory_mb():
		try:
			if sys.platform == 'win32':
				import ctypes
				from ctypes import wintypes

				class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
					_fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
								("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
								("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
								("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
								("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

				counters = PROCESS_MEMORY_COUNTERS()
				counters.cb = ctypes.sizeof(counters)
				ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
				ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
				ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
				return counters.WorkingSetSize / 1048576

			with open('/proc/self/statm') as f:
				return int(f.read().split()[1]) * os.sysconf('SC_PAGE_SIZE') / 1048576

		except Exception:
			return -1

	# move a file to the recycle bin / trash (so that it can be restored)
	# returns True, if the file was moved
	# rotation that turns a camera, which was moved sideways for a view, back towards the focal plane
	# NOTE: Panoramic cameras ignore the lens shift, which is used to converge the views of perspective and
	#		orthographic cameras. For them, the camera is rotated (toe-in) instead.
	@staticmethod
	def view_toe_in(camera_data, offset_angle):
		from mathutils import Matrix
		if camera_data.type == 'PANO': return Matrix.Rotation(-offset_angle, 4, 'Y')
		return Matrix.Identity(4)

	# lens shift for the view, relative to the shift of the original camera (none for panoramic cameras)
	@staticmethod
	def view_shift(camera_data, offset, camera_size):
		if camera_data.type == 'PANO': return 0.0
		return 0.5 * offset / camera_size

	# shut the computer down after a short delay, so that the user can still abort it
	# NOTE: Programs with unsaved changes are closed without asking (otherwise they could block the shutdown).
	@staticmethod
	def shutdown_computer(delay = 60):
		import subprocess
		try:
			if sys.platform == 'win32':

				# a console window counts down and shuts the computer down by itself. Pressing a key aborts it.
				# NOTE: The built-in countdown dialog of Windows is not used, because it can wait for the user.
				countdown = '''
import sys, time, subprocess, msvcrt
end = time.time() + int(sys.argv[1])
print('Alice/LG: the render is finished.')
while time.time() < end:
	if msvcrt.kbhit():
		msvcrt.getwch()
		print()
		print('Shutdown aborted.')
		time.sleep(3)
		sys.exit()
	print('\\rThe computer shuts down in %2i seconds. Press any key to cancel.  ' % (end - time.time()), end = '', flush = True)
	time.sleep(0.2)
print()
subprocess.call(['shutdown', '/s', '/f', '/t', '0'])
'''
				subprocess.Popen([sys.executable, '-c', countdown, str(delay)], creationflags = subprocess.CREATE_NEW_CONSOLE, close_fds = True)
			elif sys.platform == 'darwin':
				subprocess.Popen(['osascript', '-e', 'tell application "System Events" to shut down'])
			else:
				subprocess.Popen(['shutdown', '-h', '+%i' % max(1, delay // 60)])
			LookingGlassAddonLogger.info("The computer is shut down in %i seconds." % delay)
			print("Alice/LG: The render is finished. The computer shuts down in %i seconds (abort: %s)." % (delay, 'press any key in the countdown window' if sys.platform == 'win32' else 'shutdown -c'), flush = True)
			return True
		except Exception as e:
			LookingGlassAddonLogger.warning("Could not shut down the computer: %s" % e)
			return False

	@staticmethod
	def move_to_trash(path):
		import subprocess, shutil
		path = os.path.abspath(path)

		try:
			if sys.platform == 'win32':
				import ctypes
				from ctypes import wintypes

				class SHFILEOPSTRUCTW(ctypes.Structure):
					_fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR), ("pTo", wintypes.LPCWSTR),
								("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL), ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]

				# FO_DELETE with FOF_ALLOWUNDO sends the file to the recycle bin (silent, no confirmation)
				operation = SHFILEOPSTRUCTW()
				operation.wFunc = 3
				operation.pFrom = path + "\0"
				operation.fFlags = 0x40 | 0x10 | 0x400 | 0x4
				result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
				return result == 0 and not operation.fAnyOperationsAborted

			elif sys.platform == 'darwin':
				subprocess.run(['osascript', '-e', 'tell application "Finder" to delete POSIX file "%s"' % path.replace('"', '\\"')], check = True, capture_output = True)
				return True

			else:
				try:
					subprocess.run(['gio', 'trash', path], check = True, capture_output = True)
					return True
				except Exception:
					pass

				# the trash folder of the freedesktop.org specification
				trash = os.path.join(os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')), 'Trash', 'files')
				os.makedirs(trash, exist_ok = True)
				target = os.path.join(trash, os.path.basename(path))
				if os.path.exists(target): target = os.path.join(trash, "%s_%i" % (os.path.basename(path), int(time.time())))
				shutil.move(path, target)
				return True

		except Exception as e:
			LookingGlassAddonLogger.warning("Could not move '%s' to the trash: %s" % (path, e))

		return False

	# render engines for which the material preview and rendered viewport shading cannot be cast
	# NOTE: Casting these views is not supported and can crash Blender.
	eevee_engines = ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT')

	# the engines for which Material Preview / Rendered cannot be cast
	# NOTE: Eevee is drawn with a shared offscreen (see the lightfield viewport). Cycles cannot be cast.
	@staticmethod
	def blocked_cast_engines():
		return ('CYCLES',)

	# is the scene cast with a viewport shading that is not supported for the current render engine?
	@staticmethod
	def cast_shading_unsupported(context):
		try:
			if context.scene.render.engine not in LookingGlassAddon.blocked_cast_engines(): return False
			if int(context.window_manager.addon_settings.renderMode) != 0: return False

			# the shading of the mirrored Blender viewport ("Viewport")
			if context.scene.addon_settings.viewportMode == 'BLENDER':
				space = LookingGlassAddon.BlenderViewport
				return space is not None and space.shading.type in ('MATERIAL', 'RENDERED')

			# NOTE: Experimental Eevee cast. A scene without a World is not drawn: a crash in the sphere probe code of
			#		Eevee (SphereProbeModule::ensure_atlas) was reported for such a scene, and Eevee has issues without a world color.
			if context.scene.render.engine in LookingGlassAddon.eevee_engines and context.scene.world is None:
				return context.scene.addon_settings.shadingMode in ('MATERIAL', 'RENDERED')

		except Exception:
			pass

		return False

	# a black (minimum resolution) light field that is shown when there is nothing else to show
	_black_lightfield = None

	@classmethod
	def get_black_lightfield(cls):
		if cls._black_lightfield is None:
			try:
				import numpy as np
				import pylightio as pylio

				# the last preset is the minimum resolution preset
				preset = int(list(pylio.LookingGlassQuilt.formats.get().keys())[-1])
				quilt = pylio.LookingGlassQuilt.formats.get(preset)
				image = pylio.LightfieldImage.new(pylio.LookingGlassQuilt, id=preset, colormode='RGBA')
				image.set_views([pylio.LightfieldView(np.zeros((quilt["view_height"], quilt["view_width"], 4), dtype=np.uint8), pylio.LightfieldView.formats.numpyarray) for view in range(0, quilt["total_views"])], pylio.LightfieldView.formats.numpyarray)
				cls._black_lightfield = image
			except Exception as e:
				LookingGlassAddonLogger.warning("Could not create the black light field: %s" % e)

		return cls._black_lightfield

	# the quilt preset that is selected by default (as the string of the preset id)
	# use_preference: True = the preset chosen in the add-on preferences has priority
	#				  False = the default quilt of the given device has priority
	@staticmethod
	def default_quilt_preset_id(device = None, use_preference = True):
		import pylightio as pylio
		formats = pylio.LookingGlassQuilt.formats

		# the preference ('AUTO' means: use the default quilt of the connected device)
		preference = 'AUTO'
		if use_preference:
			try: preference = bpy.context.preferences.addons[__package__].preferences.default_quilt_preset
			except Exception: preference = 'AUTO'
			if preference != 'AUTO' and preference.isdigit() and int(preference) in formats.get(): return preference

		# the default quilt of the device
		if device:
			try:
				preset = formats.find(device.default_quilt_width, device.default_quilt_height, device.default_quilt_rows, device.default_quilt_columns)
				if preset: return str(preset)
			except Exception: pass

		# fallback: Looking Glass Portrait (48 views)
		return "4" if 4 in formats.get() else str(list(formats.get().keys())[0])

	# apply the default cast settings of the add-on preferences to the current window manager
	@staticmethod
	def apply_default_settings(context = None):
		try:
			context = context or bpy.context
			prefs = context.preferences.addons[__package__].preferences
			settings = context.window_manager.addon_settings
			settings.lightfieldMode = prefs.default_refresh_mode
			settings.lightfield_preview_mode = prefs.default_preview_quality
			settings.full_quality_delay = prefs.default_full_quality_delay
			settings.patient_mode = prefs.default_patient_mode
		except Exception as e:
			LookingGlassAddonLogger.debug("Could not apply the default cast settings: %s" % e)

	# LOOKING GLASS QUILT PRESETS
	# +++++++++++++++++++++++++++++++++++++++
	# set up quilt settings
	@classmethod
	def setupQuiltPresets(cls):

		# TODO: Would be better, if from .lib import pylightio could be called,
		#		but for some reason that does not import all modules and throws
		#		"AliceLG.lib.pylio has no attribute 'lookingglass"
		import pylightio as pylio

		# read the user-defined quilt presets from the add-on directory
		# and add them to the pylio quilt presets
		for file_name in sorted(os.listdir(cls.presetpath)):
			if file_name.endswith('.preset'):
				with open(cls.presetpath + file_name) as preset_file:
					pylio.LookingGlassQuilt.formats.add(json.load(preset_file))

		# Low-resolution preview for faster live-view rendering
		# NOTE: Some code parts assume, that this is the last preset in the list.
		pylio.LookingGlassQuilt.formats.add({'description': "Low-resolution Preview", 'quilt_width': 1024, 'quilt_height': 1024, 'view_width': 256, 'view_height': 128, 'columns': 4, 'rows': 8, 'total_views': 32, 'hidden': True})

		# NOTE: This must stay the LAST preset: it is the one used by "Preview Quality: Minimum"
		pylio.LookingGlassQuilt.formats.add({'description': "Minimum-resolution Preview", 'quilt_width': 512, 'quilt_height': 512, 'view_width': 128, 'view_height': 64, 'columns': 4, 'rows': 8, 'total_views': 32, 'hidden': True})


	# GLOBAL LIGHTFIELD VIEWPORT DATA
	# +++++++++++++++++++++++++++++++++++++++
	# the timeout value that determines when after the last depsgraph update
	# the lightfield window is updated with the selected higher resolution
	# quilt preset
	low_resolution_preview_timout = 0.4


	# GLOBAL QUILT VIEWER DATA
	# +++++++++++++++++++++++++++++++++++++++
	quiltPixels = None
	quiltViewerLightfieldImage = None
	# TODO: Is there a better way to check for color management setting changes?
	quiltViewAsRender = None
	quiltImageColorSpaceSetting = None



	# GLOBAL ADDON FUNCTIONS
	# +++++++++++++++++++++++++++++++++++++++
	# update the logger level
	@staticmethod
	def update_logger_levels(self, context):

		# update global variables for console output
		LookingGlassAddon.debugging_print_pylio_logger_all = bpy.context.preferences.addons[__package__].preferences.console_output
		LookingGlassAddon.debugging_print_internal_logger_all = bpy.context.preferences.addons[__package__].preferences.console_output

		# set logger levels according to the add-on preferences
		loggers_list = [logging.getLogger('pyLightIO'), logging.getLogger('Alice/LG')]
		for logger in loggers_list:
			for handler in logger.handlers:

				# if this is the TimedRotatingFileHandler
				if type(handler) == logging.handlers.TimedRotatingFileHandler:

					# if the level is DEBUG
					if bpy.context.preferences.addons[__package__].preferences.logger_level == '0':
						handler.setLevel(logging.DEBUG)

					# if the level is INFO
					elif bpy.context.preferences.addons[__package__].preferences.logger_level == '1':
						handler.setLevel(logging.INFO)

					# if the level is ERROR
					elif bpy.context.preferences.addons[__package__].preferences.logger_level == '2':
						handler.setLevel(logging.ERROR)


				# if this is the StreamHandler
				elif type(handler) == logging.StreamHandler:

					# update logger levels
					if bpy.context.preferences.addons[__package__].preferences.console_output:

						# if the level is DEBUG
						if bpy.context.preferences.addons[__package__].preferences.logger_level == '0':
							handler.setLevel(logging.DEBUG)

						# if the level is INFO
						elif bpy.context.preferences.addons[__package__].preferences.logger_level == '1':
							handler.setLevel(logging.INFO)

						# if the level is ERROR
						elif bpy.context.preferences.addons[__package__].preferences.logger_level == '2':
							handler.setLevel(logging.ERROR)

					else:

						# deactivate console output
						handler.setLevel(logging.CRITICAL + 1)

	# update the lightfield window to display a lightfield on the device
	@staticmethod
	def update_lightfield_window(window_mode, lightfield_image, flip_views=None, invert=None):
		''' update the lightfield image that is displayed on the current device '''
		''' window_mode = 0: Lightfield Viewport, window_mode = 1: Quilt Viewer, window_mode = -1: demo quilt '''

		# append the add-on's path to Blender's python PATH
		# NOTE: Only if it is not already in there. Otherwise sys.path grows with every update.
		if LookingGlassAddon.path not in sys.path: sys.path.insert(0, LookingGlassAddon.path)
		if LookingGlassAddon.libpath not in sys.path: sys.path.insert(0, LookingGlassAddon.libpath)

		# TODO: Would be better, if from .lib import pylightio could be called,
		#		but for some reason that does not import all modules and throws
		#		"AliceLG.lib.pylio has no attribute 'lookingglass"
		import pylightio as pylio

		# update the variable for the current Looking Glass device
		device = pylio.DeviceManager.get_active()

		# if a valid device is connected
		if device:

			# if a LightfieldImage was given
			if lightfield_image:

				# VIEWPORT MODE
				##################################################################
				if window_mode == 0:

					if flip_views is None: flip_views = False
					if invert is None: invert = False

					# let the device display the image
					if device.service:

						device.display(lightfield_image, flip_views=flip_views, invert=invert)

				# QUILT VIEWER MODE
				##################################################################
				# if the quilt view mode is active AND an image is loaded
				elif window_mode == 1:

					if flip_views is None: flip_views = True
					if invert is None: invert = False

					# let the device display the image
					if device.service: device.display(lightfield_image, flip_views=flip_views, invert=invert)

			# if the demo quilt was requested
			elif lightfield_image is None:

				# nothing to show: display a black screen
				if device.service:
					black = LookingGlassAddon.get_black_lightfield()
					if black is not None: device.display(black, flip_views=False, invert=False)
					else: device.display(None)

			else:
				LookingGlassAddonLogger.error("Could not update the lightfield window. No LightfieldImage was given.")


	# Internal string cache as workaround for UnicodeDecodeError reported in issue #114
	# see: https://blender.stackexchange.com/questions/299978/how-to-fix-unicodedecodeerror
	#
	# NOTE: https://blender.stackexchange.com/a/245145
	# 		"The downside is the strings in STRING_CACHE will never be GCed (sort of the opposite of the original problem).
	# 		 For most people though, I doubt the cache will grow large enough for it to become an issue."
	_enum_string_cache = {}

	@classmethod
	def enum_string_cache_items(cls, items):
		def intern_string(s):

			if not isinstance(s, str):
				return s
			
			if s not in cls._enum_string_cache:
				cls._enum_string_cache[s] = s

			return cls._enum_string_cache[s]
		
		return [tuple(intern_string(s) for s in item) for item in items]
