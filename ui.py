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
# This includes everything that is related the user interface

# ------------------ INTERNAL MODULES --------------------
from .globals import *

# ------------------- EXTERNAL MODULES -------------------
import sys, os, json
import time
from math import *

import bpy
from bpy.props import FloatProperty, PointerProperty
from bpy.types import PropertyGroup

import numpy as np

# append the add-on's path to Blender's python PATH
sys.path.insert(0, LookingGlassAddon.path)
sys.path.insert(0, LookingGlassAddon.libpath)

# TODO: Would be better, if from .lib import pylightio could be called,
#		but for some reason that does not import all modules and throws
#		"AliceLG.lib.pylio has no attribute 'lookingglass"
import pylightio as pylio

# ---------------- GLOBAL ADDON LOGGER -------------------
import logging
LookingGlassAddonLogger = logging.getLogger('Alice/LG')



# ------------- Add-on UI -------------
# Class that contains all functions relevant for the UI
class LookingGlassAddonUI:

	# This callback is required to be able to update the list of connected Looking Glass devices
	def connected_device_list_callback(self, context):

		# prepare a item list with entries of the form "identifier, name, description"
		items = []

		# if at least one Looking Glass is connected OR debug mode is activated
		if pylio.DeviceManager.count() > 0 or LookingGlassAddon.debugging_use_dummy_device:

			# then for each display in the device list
			for idx, device in enumerate(sorted(pylio.DeviceManager.to_list(), key=lambda device_type: device_type.index)):

				# if this device is a real one OR the debug mode is active
				if (not device.emulated or LookingGlassAddon.debugging_use_dummy_device):

					# add an entry in the item list
					items.append((str(device.id), 'Display ' + str(device.index) + ': ' + device.name, 'Use this Looking Glass for light field preview rendering.'))

			# FOR DEBUGGING ONLY
			if LookingGlassAddon.debugging_use_dummy_device:

				# then for each display in the device list
				for idx, device in enumerate(pylio.DeviceManager.to_list(None, True)):

					# if this device is a real one OR the debug mode is active
					if (not device.emulated or LookingGlassAddon.debugging_use_dummy_device):

						# add an entry in the item list
						items.append((str(device.id), 'Display ' + str(device.index) + ': ' + device.name, 'Use this Looking Glass for light field preview rendering.'))

		else:

			# add an entry to notify the user about the missing Looking Glass
			items.append(('-1', 'No Looking Glass Found', 'Please connect a Looking Glass.'))



		# return the item list
		return LookingGlassAddon.enum_string_cache_items(items)


	# This callback is required to be able to update the list of emulated Looking Glass devices
	def emulated_device_list_callback(self, context):

		# prepare a item list with entries of the form "identifier, name, description"
		items = []

		# if at least one emulated Looking Glass exists
		if pylio.DeviceManager.count(False, True) > 0:

			# the order and the names of the device types in the list
			# NOTE: Device types that are not listed here are appended with their own name.
			order = ["go_p", "portrait", "32_gen3_l", "32_gen3_p", "16_gen3_l", "16_gen3_p", "65_gen2", "8k_gen2", "4k_gen2", "standard", "large", "pro", "8k"]
			names = {
				"go_p": "Looking Glass Go",
				"portrait": "Looking Glass Portrait",
				"32_gen3_l": "(Gen3) \u2014 Looking Glass 32\" [Landscape]",
				"32_gen3_p": "(Gen3) \u2014 Looking Glass 32\" [Portrait]",
				"16_gen3_l": "(Gen3) \u2014 Looking Glass 16\" [Landscape]",
				"16_gen3_p": "(Gen3) \u2014 Looking Glass 16\" [Portrait]",
				"65_gen2": "(Gen2) \u2014 Looking Glass 65\"",
				"8k_gen2": "(Gen2) \u2014 Looking Glass 32\"",
				"4k_gen2": "(Gen2) \u2014 Looking Glass 16\"",
				"standard": "(Gen1) \u2014 Looking Glass 8.9\"",
				"large": "(Gen1) \u2014 Looking Glass 15.6\"",
				"pro": "(Gen1) \u2014 Looking Glass Pro 15.6\"",
				"8k": "(Gen1) \u2014 Looking Glass 8K",
			}
			sort_key = lambda device_type: (order.index(device_type.type) if device_type.type in order else len(order), -device_type.index)

			# then for each emulated device type
			for device in sorted(pylio.DeviceManager.to_list(False, True), key=sort_key):

				# if this device is an emulated one
				if device.emulated:

					# add an entry in the item list
					items.append((str(device.index), names.get(device.type, device.name), 'Use this Looking Glass type for light field rendering.'))

		else:

			# add an entry to notify the user about the missing Looking Glass
			items.append(('-1', 'No Emulated Devices Found', 'Please connect a Looking Glass.'))



		# return the item list
		return LookingGlassAddon.enum_string_cache_items(items)

	# the quilt presets that belong to a device type: a matching word in the description of the preset
	# NOTE: Devices that are not listed here (and custom presets without a match) are not restricted.
	DEVICE_QUILT_FILTER = {
		"go_p":      lambda d: d.startswith("Go,"),
		"portrait":  lambda d: d.startswith("Portrait"),
		"16_gen3_l": lambda d: d.startswith("16 Landscape"),
		"16_gen3_p": lambda d: d.startswith("16 Portrait"),
		"32_gen3_l": lambda d: d.startswith("32 Landscape"),
		"32_gen3_p": lambda d: d.startswith("32 Portrait"),
		"65_gen2":   lambda d: d.startswith("65,"),
		"4k_gen2":   lambda d: d[:2] in ("2k", "4k", "8k"),
		"8k_gen2":   lambda d: d[:2] in ("2k", "4k", "8k"),
		"standard":  lambda d: d[:2] in ("2k", "4k", "8k"),
		"large":     lambda d: d[:2] in ("2k", "4k", "8k"),
		"pro":       lambda d: d[:2] in ("2k", "4k", "8k"),
		"8k":        lambda d: d[:2] in ("2k", "4k", "8k"),
	}

	# This callback is required to be able to update the list of presets
	def quilt_preset_list_callback(self, context):

		# prepare a item list with entries of the form "identifier, name, description"
		items = []

		# then for each display in the device list
		for idx, preset in pylio.LookingGlassQuilt.formats.get().items():

			# if this preset is not marked as hidden
			if not pylio.LookingGlassQuilt.formats.is_hidden(id=idx):

				# add an entry in the item list
				items.append((str(idx), preset['description'], 'Sets the resolution for light field preview.'))


		# return the item list
		return LookingGlassAddon.enum_string_cache_items(items)

	# short name of a quilt preset for the Quilt Creation panel: the device name is already shown in the
	# "Device" dropdown, so only the number of views (and, if needed, the resolution) is shown
	# NOTE: Examples: "Portrait, 48 Views" -> "48 views",  "4k Quilt, 45 Views" -> "4k, 45 views",
	#		"Portrait (View Only), 24 Views (2x > 48)" -> "24 views (2x > 48), view only"
	def quilt_preset_label(description, device_known = True):
		import re
		if not device_known: return description
		match = re.search(r"(\d+)\s*views?(.*)$", description, re.IGNORECASE)
		if not match: return description
		label = "%s views%s" % (match.group(1), match.group(2).rstrip())
		if re.match(r"^\d+k\b", description): label = description[:2] + ", " + label
		if "view only" in description.lower(): label += ", view only"
		return label

	# the quilt presets of the Quilt Creation panel: only those that fit to the device
	def render_quilt_preset_list_callback(self, context):

		items = []
		try:

			# the device that is used for rendering (see update_render_setting_without_preset)
			device = None
			if self.render_use_device == True and pylio.DeviceManager.get_active() is not None: device = pylio.DeviceManager.get_active()
			else: device = pylio.DeviceManager.get_device(key='index', value=int(self.render_device_type))

			fits = LookingGlassAddonUI.DEVICE_QUILT_FILTER.get(getattr(device, "type", None))
			for idx, preset in pylio.LookingGlassQuilt.formats.get().items():
				if not pylio.LookingGlassQuilt.formats.is_hidden(id=idx) and (fits is None or fits(preset['description'])):
					items.append((str(idx), LookingGlassAddonUI.quilt_preset_label(preset['description'], fits is not None), 'Sets the resolution of the rendered quilt.'))
		except Exception:
			items = []

		# never return an empty list: fall back to all presets
		if not items: return LookingGlassAddonUI.quilt_preset_list_callback(self, context)
		return LookingGlassAddon.enum_string_cache_items(items)

	# poll function for the Looking Glass camera selection
	# this prevents that an object is picked or listed, which is no camera
	def camera_selection_poll(self, object):

		# the object has to be a Camera of the current view layer
		return (object.type == 'CAMERA' and (object in [o for o in bpy.context.view_layer.objects]))


	# update function for the workspace selection
	def update_workspace_selection(self, context):

		if context != None:

			# if the settings shall be taken from the current viewport
			if context.scene.addon_settings.viewportMode == 'BLENDER':

				# status variable
				success = False

				# find the correct SpaceView3D object
				for screen in bpy.data.workspaces[context.scene.addon_settings.blender_workspace].screens:
					for area in screen.areas:
						for space in area.spaces:

							# if this is the correct space
							if str(space) == str(context.scene.addon_settings.blender_view3d):

								# save the space object in the global variable
								LookingGlassAddon.BlenderViewport = space
								success = True
								break

				# if the current space was not found in the chosen workspace
				if success == False:

					# find and use the first SpaceView3D object of the workspace
					for screen in bpy.data.workspaces[context.scene.addon_settings.blender_workspace].screens:
						for area in screen.areas:
							for space in area.spaces:
								if space.type == 'VIEW_3D':

									# save the space object in the global variable
									LookingGlassAddon.BlenderViewport = space
									success = True
									break

				# if there is no 3D View in this workspace, use the active 3D View instead
				if success == False:

					# update the viewport selection
					context.scene.addon_settings.blender_view3d = "None"

					# fall back to the use of the custom settings
					LookingGlassAddon.BlenderViewport = None

		return None


	# update function for the viewport selection
	def update_viewport_selection(self, context):

		if context != None:

			# if the settings shall be taken from the current viewport
			if context.scene.addon_settings.viewportMode == 'BLENDER':

				# if a viewport is chosen
				if str(context.scene.addon_settings.blender_view3d) != "None":

					# find the correct SpaceView3D object
					for screen in bpy.data.workspaces[context.scene.addon_settings.blender_workspace].screens:
						for area in screen.areas:
							for space in area.spaces:

								# if this is the correct space
								if str(space) == str(context.scene.addon_settings.blender_view3d):

									# save the space object in the global variable
									LookingGlassAddon.BlenderViewport = space
									break

				else:

					# fall back to the use of the custom settings
					LookingGlassAddon.BlenderViewport = None

		return None


	# update function for property updates concerning render settings
	def update_render_setting_with_preset(self, context):

		# perform all updates
		LookingGlassAddonUI.update_render_setting_without_preset(self, context)

		# if a device is selected by the user
		if int(context.window_manager.addon_settings.activeDisplay) != -1: pylio.DeviceManager.set_active(int(context.window_manager.addon_settings.activeDisplay))
		else: 						 	  pylio.DeviceManager.reset_active()

		# set device variable
		device = None

		# if a camera is selected
		if context.scene.addon_settings.lookingglassCamera != None:

			# GET DEVICE INFORMATION
			# +++++++++++++++++++++++++++++++++++++++++++++++++++++
			# if the settings are to be taken from device selection AND a device is active
			if context.scene.addon_settings.render_use_device == True and pylio.DeviceManager.get_active() is not None:

				# currently selected device
				device = pylio.DeviceManager.get_active()

			else:

				# make the emulated device the active device, if one was found
				device = pylio.DeviceManager.get_device(key='index', value=int(context.scene.addon_settings.render_device_type))

			# UPDATE DROPDOWNS
			# if the loaded file does not have a lockfile
			if not LookingGlassAddon.has_lockfile:

				# the default quilt preset of the device (fallback: Looking Glass Portrait, 48 views)
				preset = LookingGlassAddon.default_quilt_preset_id(device, use_preference = False)
				if bpy.context.scene.addon_settings.render_quilt_preset != preset:
					bpy.context.scene.addon_settings.render_quilt_preset = preset

		return None

	# update function for property updates concerning render settings (WITHOUT quilt preset)
	def update_render_setting_without_preset(self, context):

		# if a device is selected by the user
		if int(context.window_manager.addon_settings.activeDisplay) != -1:	pylio.DeviceManager.set_active(int(context.window_manager.addon_settings.activeDisplay))
		else:						 										pylio.DeviceManager.reset_active()

		# set device variable
		device = None

		# if a camera is selected
		if context.scene.addon_settings.lookingglassCamera != None:

			# GET DEVICE INFORMATION
			# +++++++++++++++++++++++++++++++++++++++++++++++++++++
			# if the settings are to be taken from device selection AND a device is active
			if context.scene.addon_settings.render_use_device == True and pylio.DeviceManager.get_active() is not None:

				# currently selected device
				device = pylio.DeviceManager.get_active()

			else:

				# make the emulated device the active device, if one was found
				device = pylio.DeviceManager.get_device(key='index', value=int(context.scene.addon_settings.render_device_type))


			# APPLY RENDER SETTINGS
			# +++++++++++++++++++++++++++++++++++++++++++++++++++++
			# apply render settings for the scene to get the correct rendering frustum
			context.scene.render.resolution_x = pylio.LookingGlassQuilt.formats.get()[int(context.scene.addon_settings.render_quilt_preset)]["view_width"]
			context.scene.render.resolution_y = pylio.LookingGlassQuilt.formats.get()[int(context.scene.addon_settings.render_quilt_preset)]["view_height"]

			# for landscape formatted devices
			if (context.scene.render.resolution_x / context.scene.render.resolution_y) / device.aspect > 1:

				# apply the correct aspect ratio
				context.scene.render.pixel_aspect_x = 1.0
				context.scene.render.pixel_aspect_y = context.scene.render.resolution_x / (context.scene.render.resolution_y * device.aspect)

			# for portrait formatted devices
			else:

				# apply the correct aspect ratio
				context.scene.render.pixel_aspect_x = (context.scene.render.resolution_y * device.aspect) / context.scene.render.resolution_x
				context.scene.render.pixel_aspect_y = 1.0

            # BLOCK RENDERER
			if LookingGlassAddon.ViewportBlockRenderer:
				block = LookingGlassAddon.ViewportBlockRenderer.get_viewport_block()
			else:
				block = None

			if block and device and context.region:

				# update state variables
				block.set_active(False)
				if context.scene.addon_settings.render_use_device == True: block.set_preset(int(context.scene.addon_settings.quiltPreset))
				if context.scene.addon_settings.render_use_device == False: block.set_preset(int(context.scene.addon_settings.render_quilt_preset))
				block.set_aspect(device.aspect)
				block.set_view_cone(device.viewCone)

				# redraw region
				bpy.ops.wm.update_block_renderer('INVOKE_DEFAULT')

		return None


	# update settings for the viewport editor blocks
	def update_viewport_block_settings(self, context):

		# set device variable
		device = None

		# if a camera is selected
		if context.scene.addon_settings.lookingglassCamera != None:

			# if the settings are to be taken from device selection AND a device is active
			if context.scene.addon_settings.render_use_device == True and pylio.DeviceManager.get_active() is not None:

				# currently selected device
				device = pylio.DeviceManager.get_active()

			else:

				# make the emulated device the active device, if one was found
				device = pylio.DeviceManager.get_device(key='index', value=int(context.scene.addon_settings.render_device_type))


            # BLOCK RENDERER
			if device and LookingGlassAddon.ViewportBlockRenderer:

				# if the block renderer should be started
				if context.scene.addon_settings.viewport_block_show:
					LookingGlassAddon.ViewportBlockRenderer.start(bpy.context)

				# if the block renderer should be stopped
				if not context.scene.addon_settings.viewport_block_show:
					LookingGlassAddon.ViewportBlockRenderer.stop()

	            # if the block renderer is running
				if LookingGlassAddon.ViewportBlockRenderer.is_running():

					# get the viewport block
					block = LookingGlassAddon.ViewportBlockRenderer.get_viewport_block()
					if block:

						# update state variables
						block.set_active(False)
						if context.scene.addon_settings.render_use_device == True: block.set_preset(int(context.scene.addon_settings.quiltPreset))
						if context.scene.addon_settings.render_use_device == False: block.set_preset(int(context.scene.addon_settings.render_quilt_preset))
						block.set_aspect(device.aspect)
						block.set_view_cone(device.viewCone)

						# redraw region
						bpy.ops.wm.update_block_renderer('INVOKE_DEFAULT')

		return None


	# update settings for the image editor blocks
	def update_imageeditor_block_settings(self, context):

		# reset variables
		device = None
		block = None

		# make the emulated device the active device, if one was found
		device = pylio.DeviceManager.get_device(key='index', value=int(context.scene.addon_settings.imageeditor_block_device_type))

        # BLOCK RENDERER
		if device and LookingGlassAddon.ImageBlockRenderer:

			# if the block renderer should be started
			if context.scene.addon_settings.imageeditor_block_show:
				LookingGlassAddon.ImageBlockRenderer.start(bpy.context)

			# if the block renderer should be stopped
			if not context.scene.addon_settings.imageeditor_block_show:
				LookingGlassAddon.ImageBlockRenderer.stop()

            # if the block renderer is running
			if LookingGlassAddon.ImageBlockRenderer.is_running():

				# get the viewport block
				block = LookingGlassAddon.ImageBlockRenderer.get_imageeditor_block()
				if block:

					# update state variables
					block.set_active(False)
					block.set_preset(int(context.scene.addon_settings.imageeditor_block_quilt_preset))
					block.set_aspect(device.aspect)
					block.set_view_cone(device.viewCone)

					# redraw region
					bpy.ops.wm.update_block_renderer('INVOKE_DEFAULT')

		return None


	# Application handler that continously checks for changes of the depsgraph
	def synchronize_active_camera(scene, depsgraph):

		# if the active camera changed AND the active camera is not the "_quilt_render_cam"
		if scene.addon_settings.lookingglassCamera != scene.camera and scene.camera.name != "_quilt_render_cam":
			scene.addon_settings.lookingglassCamera = scene.camera

    # update function for property updates concerning camera selection
	def update_camera_synchronization(self, context):

		# if the synchronization is active, set the lookingglass camera to the active camera
		if context.scene.addon_settings.toggleCameraSync:

			if not LookingGlassAddonUI.synchronize_active_camera in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.append(LookingGlassAddonUI.synchronize_active_camera)
			if not LookingGlassAddonUI.synchronize_active_camera in bpy.app.handlers.frame_change_post: bpy.app.handlers.frame_change_post.append(LookingGlassAddonUI.synchronize_active_camera)
		
		elif not context.scene.addon_settings.toggleCameraSync:

			if LookingGlassAddonUI.synchronize_active_camera in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.remove(LookingGlassAddonUI.synchronize_active_camera)
			if LookingGlassAddonUI.synchronize_active_camera in bpy.app.handlers.frame_change_post: bpy.app.handlers.frame_change_post.remove(LookingGlassAddonUI.synchronize_active_camera)


    # update function for property updates concerning camera selection
	def update_camera_selection(self, context):

		# if no Looking Glass was detected AND debug mode is not activated
		if not pylio.DeviceManager.count() and not LookingGlassAddon.debugging_use_dummy_device:

			# set the checkbox to False (because there is no device we
			# could take the settings from)
			context.scene.addon_settings.render_use_device = False

		# if a camera was selected
		if context.scene.addon_settings.lookingglassCamera != None:

			# if this camera becomes a Looking Glass camera for the first time
			if not context.scene.addon_settings.lookingglassCamera.data.is_lightfield:

				# adjust the clipping values to default values if necessary
				if bpy.context.scene.addon_settings.clip_start <= 0.11:
					bpy.context.scene.addon_settings.clip_start = 4.2

				if bpy.context.scene.addon_settings.clip_end >= 99:
					bpy.context.scene.addon_settings.clip_end = 6.5

				if not (bpy.context.scene.addon_settings.clip_start < bpy.context.scene.addon_settings.focalPlane < bpy.context.scene.addon_settings.clip_end):
					bpy.context.scene.addon_settings.focalPlane = 5
				
				# set flag
				context.scene.addon_settings.lookingglassCamera.data.is_lightfield = True


			# update render settings
			LookingGlassAddonUI.update_render_setting_without_preset(self, context)

		return None


	# TODO: This function was previously used to keep the focal plane in the clipping range.
	#		It's left here in case it may be of further use later.
	# update function for property updates concerning camera clipping in the livew view
	def update_camera_setting(self, context):

		# if a camera was selected
		if context.scene.addon_settings.lookingglassCamera != None:

			# apply the settings to the selected camera object
			camera = context.scene.addon_settings.lookingglassCamera

		return None

	# getter for the (camera) clipping start
	def clip_start_getter(self):

		# display the clipping settings
		camera = bpy.context.scene.addon_settings.lookingglassCamera
		if camera:
			return camera.data.clip_start

	# setter for the (camera) clipping start
	def clip_start_setter(self, value):

		# display the clipping settings
		camera = bpy.context.scene.addon_settings.lookingglassCamera
		if camera:

			# update the clipping value
			camera.data.clip_start = value

			# make sure the focal plane stays within the clipping range
			if bpy.context.scene.addon_settings.focalPlane < camera.data.clip_start:
				bpy.context.scene.addon_settings.focalPlane = value

	# getter for the (camera) clipping end
	def clip_end_getter(self):

		# display the clipping settings
		camera = bpy.context.scene.addon_settings.lookingglassCamera
		if camera:
			return camera.data.clip_end

	# setter for the (camera) clipping end
	def clip_end_setter(self, value):

		# display the clipping settings
		camera = bpy.context.scene.addon_settings.lookingglassCamera
		if camera:

			# update the clipping value
			camera.data.clip_end = value

			# make sure the focal plane stays within the clipping range
			if bpy.context.scene.addon_settings.focalPlane > camera.data.clip_end:
				bpy.context.scene.addon_settings.focalPlane = value


	# TODO: This function was previously used to keep the focal plane in the clipping range.
	#		It's left here in case it may be of further use later.
	# update function for property updates concerning camera clipping in the livew view
	def update_focal_sync(self, context):

		# if a camera was selected
		if context.scene.addon_settings.lookingglassCamera != None:

			# apply the settings to the selected camera object
			camera = context.scene.addon_settings.lookingglassCamera
			if context.scene.addon_settings.toggleFocalSync:
				camera.data.dof.focus_distance = self['focalPlane']

		return None

	# getter for the focalPlane
	def focal_plane_getter(self):

		# if the focal plane is sync'ed with the camera focus distance
		if bpy.context.scene.addon_settings.toggleFocalSync:

			# use the focus distance of the camera
			camera = bpy.context.scene.addon_settings.lookingglassCamera
			if camera:
				if self.get('focalPlane', 5) != camera.data.dof.focus_distance:
					bpy.context.scene.addon_settings.focalPlane = camera.data.dof.focus_distance
		
		return self.get('focalPlane', 5)

	# setter for the focalPlane
	def focal_plane_setter(self, value):

		# get the current camera
		camera = bpy.context.scene.addon_settings.lookingglassCamera
		if camera:

			# if the clipping planes are pinned to the focal plane
			if bpy.context.scene.addon_settings.lockClippingPlanes:

				# make sure the new value is within the clipping range
				camera.data.clip_start += (value - self['focalPlane'])
				camera.data.clip_end += (value - self['focalPlane'])

			else:

				# make sure the new value is within the clipping range
				if value <= camera.data.clip_start:
					value = camera.data.clip_start
				elif value >= camera.data.clip_end:
					value = camera.data.clip_end

			# if the focal plane is sync'ed with the camera focus distance
			if bpy.context.scene.addon_settings.toggleFocalSync:
				camera.data.dof.focus_distance = value

			# set the focal plane value
			self['focalPlane'] = value



	# This callback populates the viewport selection with the WORKSPACES
	def workspaces_list_callback(self, context):

		# prepare a item list with entries of the form "identifier, name, description"
		items = []

		# check if the space still exists
		for workspace in bpy.data.workspaces.keys():

			# add an entry to notify the user about the missing Looking Glass
			items.append((workspace, workspace, 'The workspace the desired viewport is found.'))

		# return the item list
		return LookingGlassAddon.enum_string_cache_items(items)



	# This callback populates the viewport selection with the 3DVIEWs
	def view3D_list_callback(self, context):

		# prepare a item list with entries of the form "identifier, name, description" for the EnumProperty
		items = []

		# check if the space still exists
		if context.scene.addon_settings.blender_workspace in bpy.data.workspaces:

			# find all 3D Views in the selected Workspace
			for screen in bpy.data.workspaces[context.scene.addon_settings.blender_workspace].screens:
				for area in screen.areas:
					for space in area.spaces:
						if space.type == 'VIEW_3D':

							# add an item to the item list
							items.append((str(space), 'Viewport ' + str(len(items) + 1), 'The Blender viewport to which the Looking Glass adjusts.'))

		# if no spaces were found
		if len(items) == 0:

			# add a dummy entry to the item list
			items.append(('None', 'None', 'The Blender viewport to which the Looking Glass adjusts.'))

		# return the item list
		return LookingGlassAddon.enum_string_cache_items(items)



	# update function for property updates concerning lightfield window settings
	def update_lightfield_window_settings(self, context):

		# if the lightfield viewport is in quilt viewer mode
		if context.window_manager.addon_settings.renderMode == '1':

			# update the lightfield displayed on the device
			LookingGlassAddon.update_lightfield_window(int(context.window_manager.addon_settings.renderMode), LookingGlassAddon.quiltViewerLightfieldImage)

		# if the scene is cast (again): redraw it, otherwise the display keeps showing the quilt image
		elif context.window_manager.addon_settings.renderMode == '0' and context.window_manager.addon_settings.ShowLightfieldWindow:

			# the modal operator of the lightfield viewport does the refresh
			context.window_manager.addon_settings.viewport_manual_refresh = True


	# update function for property updates concerning quilt image selection
	def update_quilt_selection(self, context):

		# if a quilt was selected
		if context.window_manager.addon_settings.quiltImage != None:

			# update the setting observers
			LookingGlassAddon.quiltViewAsRender = context.window_manager.addon_settings.quiltImage.use_view_as_render
			LookingGlassAddon.quiltImageColorSpaceSetting = context.window_manager.addon_settings.quiltImage.colorspace_settings

			# if no pixel array exists
			if LookingGlassAddon.quiltPixels is None:

				# create a numpy array for the pixel data
				LookingGlassAddon.quiltPixels = np.empty(len(context.window_manager.addon_settings.quiltImage.pixels), dtype=np.float32)

			else:

				# resize the numpy array
				LookingGlassAddon.quiltPixels.resize(len(context.window_manager.addon_settings.quiltImage.pixels), refcheck=False)



			# GET PIXEL DATA
			# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			# TODO: Change. The current approach is hacky and slow, but I don't
			#		know of any other way to access the pixel data WITH applied
			#		color management directly in memory. Seems like Blender
			#		does not expose this pixel data to the Python API
			#
			#		I asked this also on stackexchange but got no better way yet:
			#		https://blender.stackexchange.com/questions/206910/access-image-pixel-data-with-color-management-settings
			#

			# if the image has the "view as render" option inactive
			if context.window_manager.addon_settings.quiltImage.use_view_as_render == False:

				# save the original settings
				tempViewTransform = context.scene.view_settings.view_transform
				tempLook = context.scene.view_settings.look
				tempExposure = context.scene.view_settings.exposure
				tempGamma = context.scene.view_settings.gamma
				tempUseCurveMapping = context.scene.view_settings.use_curve_mapping

				# apply standard settings
				context.scene.view_settings.view_transform = "Standard"
				context.scene.view_settings.look = "None"
				context.scene.view_settings.exposure = 0
				context.scene.view_settings.gamma = 1
				context.scene.view_settings.use_curve_mapping = False


			# set the temporary file path
			tempFilepath = bpy.app.tempdir + 'temp' + str(int(time.time())) + '.png'

			# set the output settings
			tempUseRenderCache = context.scene.render.use_render_cache
			tempFileFormat = context.scene.render.image_settings.file_format
			tempColorDepth = context.scene.render.image_settings.color_depth
			tempColorMode = context.scene.render.image_settings.color_mode
			context.scene.render.use_render_cache = False
			context.scene.render.image_settings.file_format = 'PNG'
			context.scene.render.image_settings.color_depth = '8'
			context.scene.render.image_settings.color_mode = 'RGBA'

			# save the image to the temporary directory
			context.window_manager.addon_settings.quiltImage.save_render(filepath=tempFilepath, scene=context.scene)

			# restore output render settings
			context.scene.render.use_render_cache = tempUseRenderCache
			context.scene.render.image_settings.file_format = tempFileFormat
			context.scene.render.image_settings.color_depth = tempColorDepth
			context.scene.render.image_settings.color_mode = tempColorMode

			# if the image has the "view as render" option inactive
			if context.window_manager.addon_settings.quiltImage.use_view_as_render == False:

				# restore the original settings
				context.scene.view_settings.view_transform = tempViewTransform
				context.scene.view_settings.look = tempLook
				context.scene.view_settings.exposure = tempExposure
				context.scene.view_settings.gamma = tempGamma
				context.scene.view_settings.use_curve_mapping = tempUseCurveMapping

			# if the file was created
			if os.path.isfile(tempFilepath) == True:

				# append the loaded image to the list
				tempImage = bpy.data.images.load(filepath=tempFilepath)

				# copy pixel data to the array and a BGL Buffer
				tempImage.pixels.foreach_get(LookingGlassAddon.quiltPixels)

			# TODO: The following lines would be enough, if the color
			#		management settings would be applied in memory. Not deleted
			#		for later
			#
			# # copy pixel data to the array and a BGL Buffer
			# context.window_manager.addon_settings.quiltImage.pixels.foreach_get(LookingGlassAddon.quiltPixels)
			# LookingGlassAddon.quiltTextureBuffer = bgl.Buffer(bgl.GL_FLOAT, len(context.window_manager.addon_settings.quiltImage.pixels), LookingGlassAddon.quiltPixels)

			# delete the temporary Blender image
			bpy.data.images.remove(tempImage)

			# delete the temporary file
			os.remove(tempFilepath)

			# CREATE A NEW PYLIGHTIO LIGHTFIELD IMAGE FROM THE BLENDER QUILT
			# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			# convert to uint8
			quiltPixels = 255 * LookingGlassAddon.quiltPixels
			quiltPixels = quiltPixels.astype(dtype=np.uint8)

			# if no quilt viewer LightfieldImage is selected
			if context.window_manager.addon_settings.quiltImage is None:

				# free the view data of the lightfield image, if one was loaded
				if LookingGlassAddon.quiltViewerLightfieldImage:
					LookingGlassAddon.quiltViewerLightfieldImage.clear_views()
					LookingGlassAddon.quiltViewerLightfieldImage = None

			# create a LightfieldImage from the selected quilt
			LookingGlassAddon.quiltViewerLightfieldImage = pylio.LightfieldImage.from_buffer(pylio.LookingGlassQuilt, quiltPixels, context.window_manager.addon_settings.quiltImage.size[0], context.window_manager.addon_settings.quiltImage.size[1], context.window_manager.addon_settings.quiltImage.channels, quilt_name = context.window_manager.addon_settings.quiltImage.name)

			# update the lightfield displayed on the device
			LookingGlassAddon.update_lightfield_window(int(context.window_manager.addon_settings.renderMode), LookingGlassAddon.quiltViewerLightfieldImage)

		# if the quilt selection was deleted
		else:

			# free the view data of the lightfield image, if one was loaded
			if LookingGlassAddon.quiltViewerLightfieldImage:
				LookingGlassAddon.quiltViewerLightfieldImage.clear_views()
				LookingGlassAddon.quiltViewerLightfieldImage = None

			# update the lightfield displayed on the device
			LookingGlassAddon.update_lightfield_window(int(context.window_manager.addon_settings.renderMode), LookingGlassAddon.quiltViewerLightfieldImage)

			# reset the variables
			LookingGlassAddon.quiltPixels = None

	# the shading modes of the custom viewport settings
	# NOTE: The material preview is not available for the render engines that cannot be cast (Cycles, Eevee)
	def shading_mode_items(self, context):
		items = [('WIREFRAME', '', 'Use the OpenGL wireframe rendering mode', 'SHADING_WIRE', 0),
				 ('SOLID', '', 'Use the OpenGL solid rendering mode', 'SHADING_SOLID', 1)]

		try: engine = bpy.context.scene.render.engine
		except Exception: engine = ''

		if engine not in LookingGlassAddon.unsupported_cast_engines:
			items.append(('MATERIAL', '', 'Use the current render engines material preview rendering mode', 'SHADING_RENDERED', 2))

		return LookingGlassAddon.enum_string_cache_items(items)

	# the number of views of the selected quilt (the "Quilt" dropdown in Quilt Creation)
	@staticmethod
	def preview_total_views(addon_settings):
		try:
			return max(1, int(pylio.LookingGlassQuilt.formats.get(int(addon_settings.render_quilt_preset))['total_views']))
		except Exception:
			return 128

	# the view index of the render preview is limited to the number of views of the selected quilt
	@staticmethod
	def get_preview_view_index(self):
		return max(0, min(int(self.get("_preview_view_index", 0)), LookingGlassAddonUI.preview_total_views(self) - 1))

	@staticmethod
	def set_preview_view_index(self, value):
		self["_preview_view_index"] = max(0, min(int(value), LookingGlassAddonUI.preview_total_views(self) - 1))

	@staticmethod
	def update_preview_view(self, context):
		"""Update camera position when preview slider changes while preview is active"""
		if not context.scene.addon_settings.preview_active:
			return
		
		import pylightio as pylio
		from math import tan, radians
		from mathutils import Matrix
		
		addon_settings = context.scene.addon_settings
		camera = addon_settings.lookingglassCamera
		
		if camera is None:
			return
		
		# GET QUILT PRESET DATA
		if addon_settings.render_use_device:
			device = pylio.DeviceManager.get_active()
			if device:
				total_views = device.default_quilt_columns * device.default_quilt_rows
				view_cone = device.view_cone
			else:
				return
		else:
			preset = pylio.LookingGlassQuilt.formats.get(int(addon_settings.render_quilt_preset))
			total_views = int(preset['total_views'])
			view_cone = 40.0
		
		# Get view index and ensure it's within bounds
		view_index = addon_settings.preview_view_index
		if view_index >= total_views:
			view_index = total_views - 1
			addon_settings.preview_view_index = view_index
		
		# Restore original matrix
		matrix_list = list(addon_settings.preview_original_matrix)
		original_matrix = Matrix((
			matrix_list[0:4],
			matrix_list[4:8],
			matrix_list[8:12],
			matrix_list[12:16]
		))
		
		# Calculate new preview position from original
		view_matrix = original_matrix.copy()
		view_matrix = view_matrix @ Matrix.Scale(1/camera.scale.x, 4, (1, 0, 0))
		view_matrix = view_matrix @ Matrix.Scale(1/camera.scale.y, 4, (0, 1, 0))
		view_matrix = view_matrix @ Matrix.Scale(1/camera.scale.z, 4, (0, 0, 1))
		view_matrix_inv = view_matrix.inverted_safe()
		
		fov = camera.data.angle
		cameraDistance = addon_settings.focalPlane
		cameraSize = cameraDistance * tan(fov / 2)
		offsetAngle = (0.5 - view_index / (total_views - 1)) * radians(view_cone)
		offset = cameraDistance * tan(offsetAngle)
		
		# Update camera position
		camera.matrix_world = view_matrix @ (Matrix.Translation((-offset, 0, 0)) @ LookingGlassAddon.view_toe_in(camera.data, offsetAngle) @ (view_matrix_inv @ original_matrix.copy()))
		camera.data.shift_x = addon_settings.preview_original_shift + LookingGlassAddon.view_shift(camera.data, offset, cameraSize)


# Properties in the preferences pane for this addon - Global values
class LookingGlassAddonSettingsWM(bpy.types.PropertyGroup):

	# PANEL: GENERAL
	# a list of connected Looking Glass displays
	activeDisplay: bpy.props.EnumProperty(
										items = LookingGlassAddonUI.connected_device_list_callback,
										name="Please select a Looking Glass",
										update=LookingGlassAddonUI.update_render_setting_without_preset,
										)

	# a boolean to toogle the render window on or off
	ShowLightfieldWindow: bpy.props.BoolProperty(
											name="Lightfield Window",
											description = "Creates a window for the light field rendering on the current Looking Glass device",
											default = False,
											)

	# PANEL: LIGHTFIELD WINDOW SETTINGS
	# UI elements for user control
	renderMode: bpy.props.EnumProperty(
										items = [('0', 'Scene', 'Cast the current scene to the Looking Glass', 'VIEW3D', 0),
												 ('1', 'Quilt Viewer', 'Display a pre-rendered quilt image in the Looking Glass', 'RENDER_RESULT', 1)],
										default='0',
										name="Render Mode",
										update=LookingGlassAddonUI.update_lightfield_window_settings,
										)

	# Lightfield Viewport Modes
	lightfieldMode: bpy.props.EnumProperty(
										items = [('0', 'Refresh Mode: Automatic', 'Automatically refresh the light field viewport'),
												 ('1', 'Refresh Mode: Manual', 'Manually refresh the light field viewport')],
										default='0',
										name="Light Field Viewport Modes",
										update=LookingGlassAddonUI.update_lightfield_window_settings,
										)

	# Lightfield Preview Resolution in Auto lightfield mode
	lightfield_preview_mode: bpy.props.EnumProperty(
										items = [('6', 'Preview Quality: Minimum', 'Minimum-resolution preview during interactions (512x512 quilt, 32 views). Sends the least data to Looking Glass Bridge'),
												 ('1', 'Preview Quality: Lowest', 'Low-resolution preview during interactions (1024x1024 quilt, 32 views)'),
												 ('5', 'Preview Quality: Low', 'Skip five out of six views during interactions'),
												 ('3', 'Preview Quality: Medium', 'Skip two out of three views during interactions'),
												 ('2', 'Preview Quality: Best', 'Skip every second view during interactions'),
												 ],
										default='6',
										name="Light Field Preview Mode",
										update=LookingGlassAddonUI.update_lightfield_window_settings,
										)

	# how long to wait without changes before the full-quality light field is rendered and sent
	full_quality_delay: bpy.props.FloatProperty(
										name="Full-quality refresh",
										description="Seconds without changes after which the full-quality light field is rendered and sent to Looking Glass Bridge. Longer values send fewer large images, which reduces the memory that Bridge uses",
										default = 0.7,
										min = 0.2,
										max = 10.0,
										step = 10,
										precision = 1,
										unit = 'TIME',
										)

	# wait with light field updates until the current operator (e.g., grabbing an object) has finished
	patient_mode: bpy.props.BoolProperty(
										name="Patient Mode",
										description="Wait with updating the light field until the current operator (e.g., moving an object) has finished. Faster and smoother in heavy scenes, but the light field does not update while you are dragging",
										default = False,
										)

	# pointer property that can be used to load a pre-rendered quilt image
	quiltImage: bpy.props.PointerProperty(
										name="Quilt",
										type=bpy.types.Image,
										description = "Quilt image for display in the Looking Glass",
										update = LookingGlassAddonUI.update_quilt_selection,
										)


	viewport_manual_refresh: bpy.props.BoolProperty(
										name="Refresh Looking Glass",
										description="Redraw the light field in the Looking Glass",
										default = False,
										)





# Properties in the preferences pane for this addon - Scene specific values
class LookingGlassAddonSettingsScene(bpy.types.PropertyGroup):

	# PANEL: GENERAL
	# a list of quilt presets
	quiltPreset: bpy.props.EnumProperty(
										items = LookingGlassAddonUI.quilt_preset_list_callback,
										name="View Resolution",
										update=LookingGlassAddonUI.update_render_setting_without_preset,
										)


	# PANEL: CAMERA SETTINGS
	# pointer property that can be used to load a pre-rendered quilt image
	lookingglassCamera: bpy.props.PointerProperty(
										name="Looking Glass Camera",
										type=bpy.types.Object,
										description = "Select a camera, which defines the view for your Looking Glass or quilt image",
										poll = LookingGlassAddonUI.camera_selection_poll,
										update = LookingGlassAddonUI.update_camera_selection,
										# options = {'ANIMATABLE'}
										)

	showFocalPlane: bpy.props.BoolProperty(
										name="Show Focal Plane",
										description="If enabled, the focal plane of the Looking Glass is shown in the viewport",
										default = True,
										)

	showFrustum: bpy.props.BoolProperty(
										name="Show Camera Frustum",
										description="If enabled, the render volume of the Looking Glass is shown in the viewport",
										default = True,
										)

	toggleCameraSync: bpy.props.BoolProperty(
										name="Synchronize with Active Camera",
										description="If enabled, the active camera will always be used as the Looking Glass camera (e.g., useful with camera markers)",
										default = False,
										update = LookingGlassAddonUI.update_camera_synchronization,
										)

	clip_start: bpy.props.FloatProperty(
										name = "Clip Start",
										default = 4.2,
										min = 0.000001,
										soft_min = 0.1,
										precision = 1,
										step = 5,
										unit = "LENGTH",
										description = "Far clipping plane of the Looking Glass frustum",
										update = LookingGlassAddonUI.update_camera_setting,
										get = LookingGlassAddonUI.clip_start_getter,
										set = LookingGlassAddonUI.clip_start_setter,
										)

	clip_end: bpy.props.FloatProperty(
										name = "Clip End",
										default = 6.5,
										min = 0,
										precision = 1,
										step = 5,
										unit = "LENGTH",
										description = "Far clipping plane of the Looking Glass frustum",
										update = LookingGlassAddonUI.update_camera_setting,
										get = LookingGlassAddonUI.clip_end_getter,
										set = LookingGlassAddonUI.clip_end_setter,
										)

	# the virtual distance of the plane, which represents the focal plane of the Looking Glass
	focalPlane: bpy.props.FloatProperty(
										name = "Focal Plane",
										default = 5,
										min = 0,
										precision = 2,
										step = 5,
										unit = "LENGTH",
										description = "Virtual distance to the focal plane. (This plane is directly mapped to the LCD display of the Looking Glass)",
										update = LookingGlassAddonUI.update_camera_setting,
										get = LookingGlassAddonUI.focal_plane_getter,
										set = LookingGlassAddonUI.focal_plane_setter,
										)

	toggleFocalSync: bpy.props.BoolProperty(
										name="Synchronize with Camera Focus Distance",
										description="If enabled, the focus distance (depth of field) and focal plane values of the Looking Glass Camera will be kept in synchronization",
										default = True,
										update = LookingGlassAddonUI.update_focal_sync,
										)

	lockClippingPlanes: bpy.props.BoolProperty(
										name="Lock Clipping Planes to Focal Plane",
										description="If enabled, the clipping planes will move with the focal plane",
										default = False,
										)


	# PANEL: RENDER SETTINGS
	# Use the device to set device settings
	# NOTE: The device and quilt for rendering are always the ones chosen in the Quilt Creation panel,
	#		independent of the Looking Glass that is used for casting. This property is kept (always off),
	#		because code and saved files still refer to it.
	render_use_device: bpy.props.BoolProperty(
										name="Use Device Settings",
										default = False,
										get = lambda self: False,
										set = lambda self, value: None,
										options = {'HIDDEN'},
										)

	# shut the computer down when a rendering is finished (e.g., for overnight renders)
	shutdown_after_render: bpy.props.BoolProperty(
										name="Shut off Computer after Render",
										description="If enabled, the computer is shut down 60 seconds after a quilt render is completed (not after a cancelled or failed render). A countdown window is shown; the shutdown can be aborted by pressing a key in it (Windows) or with 'shutdown -c' (Linux). Programs with unsaved changes are closed without asking",
										default = False,
										)

	# Add a suffix with metadata to the file name
	render_add_suffix: bpy.props.BoolProperty(
										name="Add Metadata",
										description="If enabled, metadata will be added to the quilt filename as a suffix. That metadata is used by Looking Glass Studio, Blocks, and other applications in the Looking Glass ecosystem to automatically determine the correct settings for displaying or editing the quilt",
										default = True,
										update=LookingGlassAddonUI.update_render_setting_without_preset,
										)

	# what the Quilt Creation panel builds the quilt from
	quilt_build_mode: bpy.props.EnumProperty(
									items = [('RENDER', 'Render', 'Render the quilt from the Looking Glass camera'),
											 ('FILES', 'Files', 'Build a quilt from existing view images')],
									default='RENDER',
									name="Build From",
									)

	# what the render button of the Quilt Creation panel does
	render_source: bpy.props.EnumProperty(
									items = [('QUILT', 'Render Quilt', 'Render a single quilt'),
											 ('ANIMATION', 'Render Animation Quilt', 'Render the frame range as quilt animation'),
											 ('HEADLESS', 'Render Quilt Headlessly', 'Save the file, close Blender and render a single quilt in a separate Blender process'),
											 ('ANIMATION_HEADLESS', 'Render Animation Quilt Headlessly', 'Save the file, close Blender and render the frame range as quilt animation in a separate Blender process')],
									default='QUILT',
									name="Source",
									)

	# Orientation of the views
	render_device_type: bpy.props.EnumProperty(
										items = LookingGlassAddonUI.emulated_device_list_callback,
										name="Device Type",
										update = LookingGlassAddonUI.update_render_setting_with_preset,
										)

	# Quilt presets
	render_quilt_preset: bpy.props.EnumProperty(
									items = LookingGlassAddonUI.render_quilt_preset_list_callback,
									name="Quilt Preset",
									update = LookingGlassAddonUI.update_render_setting_without_preset,
									)

	# File handling
	render_output: bpy.props.EnumProperty(
									items = [('0', 'View and Quilt Files', 'Each view is rendered to a separate file in the output directory in addition to the quilt.'),
											 ('1', 'Only Quilt File', 'Each view is rendered to a temporary file in the output directory. These files are deleted after the quilt is complete.'),
											 ('2', 'Only View Files', 'Render only the view files. Quilt generation is skipped.')],
									default='1',
									name="Output",
									)

	# Progress bar
	render_progress: bpy.props.FloatProperty(
										name = "",
										subtype='PERCENTAGE',
										default = 0,
										min = 0,
										max = 100,
										precision = 0,
										step = 100,
										description = "Total quilt rendering progress",
										)

	# Cancel button
	render_stop: bpy.props.BoolProperty(
										name="Cancel render job",
										description="Press this button or the 'ESC' key to stop the quilt rendering.",
										default = False,
										)

	# PANEL: ADVANCED SETTINGS
	advanced_quilt_source_path: bpy.props.StringProperty(
		name = "Source Directory",
		default = "//",
		description = "Select the directory containing the view images",
		subtype = 'DIR_PATH'
		)



	# PANEL: OVERLAY & SHADER SETTINGS
	viewportMode: bpy.props.EnumProperty(
										items = [
													('BLENDER', 'Viewport', 'Use the settings of a Blender viewport', 'BLENDER', 0),
													('CUSTOM', 'Custom', 'Specify the settings for the Looking Glass viewport manually', 'OVERLAY', 1)
												],
										default='BLENDER',
										name="Viewport Mode",
										)

	blender_workspace: bpy.props.EnumProperty(
										name="Workspace",
										items = LookingGlassAddonUI.workspaces_list_callback,
										update = LookingGlassAddonUI.update_workspace_selection
										)

	blender_view3d: bpy.props.EnumProperty(
										name="3D View",
										items = LookingGlassAddonUI.view3D_list_callback,
										update = LookingGlassAddonUI.update_viewport_selection
										)

	# Shading
	shadingMode: bpy.props.EnumProperty(
										items = LookingGlassAddonUI.shading_mode_items,
										default = 1,
										name="Shading",
										)

	viewport_show_xray: bpy.props.BoolProperty(
										name="",
										description="If enabled, the whole scene is rendered transparent in the Looking Glass",
										default = False,
										)

	viewport_xray_alpha: bpy.props.FloatProperty(
										name = "X-Ray Alpha",
										default = 0.5,
										min = 0.001,
										max = 1,
										precision = 3,
										step = 1,
										description = "Amount of alpha to use",
										)

	viewport_use_dof: bpy.props.BoolProperty(
										name="Depth of Field",
										description="If enabled, the lightfield is rendered using the depth of field settings of the multiview cameras",
										default = False,
										update = LookingGlassAddonUI.update_camera_setting,
										)

	# GUIDES
	viewport_show_floor: bpy.props.BoolProperty(
										name="Floor",
										description="If enabled, the floor grid is displayed in the Looking Glass",
										default = True,
										)

	viewport_show_axes: bpy.props.BoolVectorProperty(
										name="Axes",
										subtype="XYZ",
										description="If enabled, the x axis is displayed in the Looking Glass",
										size=3,
										default = (True, True, False),
										)

	# COMPOSITION GUIDES (drawn over every view)
	viewport_guide_center: bpy.props.BoolProperty(name="Center", description="Show the center lines in the Looking Glass", default = False)
	viewport_guide_diagonal: bpy.props.BoolProperty(name="Diagonals", description="Show the diagonals in the Looking Glass", default = False)
	viewport_guide_thirds: bpy.props.BoolProperty(name="Thirds", description="Show the rule of thirds in the Looking Glass", default = False)
	viewport_guide_golden: bpy.props.BoolProperty(name="Golden Ratio", description="Show the golden ratio lines in the Looking Glass", default = False)
	viewport_guide_golden_triangle_a: bpy.props.BoolProperty(name="Golden Triangle A", description="Show the golden triangles (diagonal from the lower left) in the Looking Glass", default = False)
	viewport_guide_golden_triangle_b: bpy.props.BoolProperty(name="Golden Triangle B", description="Show the golden triangles (diagonal from the upper left) in the Looking Glass", default = False)
	viewport_guide_opacity: bpy.props.FloatProperty(name="Opacity", description="Opacity of the composition guides", default = 0.6, min = 0.05, max = 1.0, precision = 2, subtype = 'FACTOR')

	viewport_grid_scale: bpy.props.FloatProperty(
										name = "Grid Scale",
										default = 1,
										min = 0.001,
										precision = 3,
										step = 0.1,
										description = "Multiplier for the distance between 3D View grid lines",
										)


	# OBJECTS
	viewport_show_extras: bpy.props.BoolProperty(
										name="Extras",
										description="If enabled, object details including empty wire, cameras, and light sources are displayed in the Looking Glass",
										default = True,
										)

	viewport_show_relationship_lines: bpy.props.BoolProperty(
										name="Relationship Lines",
										description="If enabled, relationship lines indicating parents or constraints are displayed in the Looking Glass",
										default = False,
										)

	viewport_show_outline_selected: bpy.props.BoolProperty(
										name="Show Outline Selected",
										description="If enabled, the outline of the selected object is displayed in the Looking Glass",
										default = False,
										)

	viewport_show_bones: bpy.props.BoolProperty(
										name="Bones",
										description="If enabled, bones are displayed in the Looking Glass",
										default = False,
										)

	viewport_show_motion_paths: bpy.props.BoolProperty(
										name="Motion Paths",
										description="If enabled, motion paths (without bones) are displayed in the Looking Glass",
										default = False,
										)

	viewport_show_origins: bpy.props.BoolProperty(
										name="Origins",
										description="If enabled, the object center dots are displayed in the Looking Glass",
										default = False,
										)

	viewport_show_origins_all: bpy.props.BoolProperty(
										name="Origins (All)",
										description="If enabled, the object center dot of all objects are displayed in the Looking Glass",
										default = False,
										)

	# GEOMETRY
	viewport_show_wireframes: bpy.props.BoolProperty(
										name="",
										description="If enabled, the face edges wires are displayed in the Looking Glass",
										default = False,
										)

	viewport_wireframe_threshold: bpy.props.FloatProperty(
										name="Wireframe",
										min=0,
										max=1,
										precision=3,
										description="Adjust the angle threshold for displaying edges in the Looking Glass",
										default = 1,
										)

	viewport_show_face_orientation: bpy.props.BoolProperty(
										name="Face Orientation",
										description="If enabled, the face orientation is displayed in the Looking Glass",
										default = False,
										)

	# PANEL: VIEWPORT BLOCKS SETTINGS
	# a boolean to toogle the block viewport preview on or off
	viewport_block_show: bpy.props.BoolProperty(
		name="Hologram preview",
		description = "Displays a Looking Glass hologram preview in the Blender viewport (not supported for Cycles)",
		default = False,
		update=LookingGlassAddonUI.update_viewport_block_settings,
		)

	# UI elements for user control
	viewport_block_alignment: bpy.props.EnumProperty(
										items = [('left', 'Left', 'The block is rendered on the lower left corner of the viewport'),
												 ('right', 'Right', 'The block is rendered on the lower right corner of the viewport')],
										default='left',
										name="Block Alignment",
										update=LookingGlassAddonUI.update_viewport_block_settings,
										)

	viewport_block_scaling_factor: bpy.props.FloatProperty(
		name="Scaling Factor",
		min=0,
		max=1,
		precision=2,
		description="Adjust the scaling of the hologram preview in the viewport",
		default = 0.25,
        update=LookingGlassAddonUI.update_viewport_block_settings,
		)

	viewport_block_alpha: bpy.props.FloatProperty(
		name="Alpha",
		min=0,
		max=1,
		precision=2,
		description="Adjust the alpha value of the hologram preview in the viewport if mouse is not over the block",
		default = 0.5,
        update=LookingGlassAddonUI.update_viewport_block_settings,
		)


	# PANEL: IMAGE EDITOR BLOCKS SETTINGS
	# a boolean to toogle the block viewport preview on or off
	imageeditor_block_show: bpy.props.BoolProperty(
		name="Hologram Preview",
		description = "Displays a Looking Glass hologram preview for this quilt",
		default = False,
		update=LookingGlassAddonUI.update_imageeditor_block_settings,
		)

	# device type for the block rendering
	imageeditor_block_device_type: bpy.props.EnumProperty(
									items = LookingGlassAddonUI.emulated_device_list_callback,
									name="Device Type",
									update = LookingGlassAddonUI.update_imageeditor_block_settings,
									)

	# quilt preset for the block rendering
	imageeditor_block_quilt_preset: bpy.props.EnumProperty(
									items = LookingGlassAddonUI.quilt_preset_list_callback,
									name="Quilt Preset",
									update = LookingGlassAddonUI.update_imageeditor_block_settings,
									)

	# PANEL: RENDER PREVIEW
	preview_view_index: bpy.props.IntProperty(
										name = "View Index",
										default = 0,
										min = 0,
										max = 128,
										description = "Index of the view to preview (0 to the number of views of the selected quilt - 1)",
										get = LookingGlassAddonUI.get_preview_view_index,
										set = LookingGlassAddonUI.set_preview_view_index,
										update = LookingGlassAddonUI.update_preview_view,
										)

	preview_active: bpy.props.BoolProperty(
										name = "Preview Active",
										default = False,
										options = {'HIDDEN'},
										description = "Whether preview mode is currently active",
										)

	preview_original_matrix: bpy.props.FloatVectorProperty(
										name = "Original Camera Matrix",
										size = 16,
										default = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1],
										options = {'HIDDEN'},
										description = "Original camera matrix before preview",
										)

	preview_original_shift: bpy.props.FloatProperty(
										name = "Original Camera Shift",
										default = 0.0,
										options = {'HIDDEN'},
										description = "Original camera shift_x before preview",
										)


# ----------------- PANEL FOR GENERAL SETTINGS --------------------
# an operator that refreshes the list of connected Looking Glasses
class LOOKINGGLASS_OT_refresh_display_list(bpy.types.Operator):
	bl_idname = "lookingglass.refresh_display_list"
	bl_label = "Refresh list"
	bl_description = "Refreshes the list of connected Looking Glass devices from Looking Glass Bridge"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):

		# log info
		LookingGlassAddonLogger.info("Refreshing device information ...")

		# if the connection to Looking Glass Bridge is not established (e.g., Bridge was started
		# after Blender or the display was connected later), try to connect again
		if LookingGlassAddon.service is None or not LookingGlassAddon.service.is_ready():
			try:
				LookingGlassAddonLogger.info(" [#] Trying to connect to Looking Glass Bridge ...")

				if LookingGlassAddon.service is not None: pylio.ServiceManager.remove(LookingGlassAddon.service)
				LookingGlassAddon.service = pylio.ServiceManager.add(pylio.lookingglass.services.LookingGlassBridge, client_name = LookingGlassAddon.name)

				if type(LookingGlassAddon.service) == pylio.lookingglass.services.LookingGlassBridge:
					pylio.DeviceManager.set_service(LookingGlassAddon.service)
					pylio.DeviceManager.add_emulated()

					if LookingGlassAddon.service.is_ready(): LookingGlassAddonLogger.info(" [#] Connected to Looking Glass Bridge version: %s" % LookingGlassAddon.service.get_version())
					else: LookingGlassAddonLogger.info(" [#] Connection failed.")

			except Exception as e:
				LookingGlassAddonLogger.warning(" [#] Could not connect to Looking Glass Bridge: %s" % e)

		# if a service for display communication was successfully added
		if (not LookingGlassAddon.service is None):

			# if the service is ready
			if LookingGlassAddon.service.is_ready():

				# refresh the list of connected devices using the active service
				pylio.DeviceManager.refresh()

				# log info
				LookingGlassAddonLogger.info(" [#] Number of connected displays: %i" % pylio.DeviceManager.count())

				# loop through all connected devices
				for idx, device in enumerate(pylio.DeviceManager.to_list()):

					# log info
					LookingGlassAddonLogger.info(" [#] Display %i: %s" % (idx, device.name,))

			# if no Looking Glass was detected AND debug mode is deaqctivated
			if not pylio.DeviceManager.count() and not LookingGlassAddon.debugging_use_dummy_device:

				# set the checkbox to False (because there is no device we
				# could take the settings from)
				context.scene.addon_settings.render_use_device = False

			# if a Looking Glass was detected, but non was previously selected
			elif pylio.DeviceManager.count():

				# get currently active device
				device = pylio.DeviceManager.get_active()

				# if None is active or the active device is an emulated one
				if not device or (device and device.emulated):

					# log info
					LookingGlassAddonLogger.info(" [#] Setting active display %i: %s" % (pylio.DeviceManager.to_list()[0].id, pylio.DeviceManager.to_list()[0].name,))

					# make the first connected display the active display
					pylio.DeviceManager.set_active(pylio.DeviceManager.to_list()[0].id)

					# get currently active device
					device = pylio.DeviceManager.get_active()

					# preselect the same device type for rendering (it can be changed independently)
					for emulated in pylio.DeviceManager.to_list(False, True):
						if emulated.type == device.type:
							if context.scene.addon_settings.render_device_type != str(emulated.index): context.scene.addon_settings.render_device_type = str(emulated.index)
							break

				# try to find the suitable default quilt preset
				preset = pylio.LookingGlassQuilt.formats.find(device.default_quilt_width, device.default_quilt_height, device.default_quilt_rows, device.default_quilt_columns)

				# then update the selected quilt preset from the device's default quilt
				if preset:
					context.scene.addon_settings.quiltPreset = str(preset)

				# fallback solution, if the default quilt is not found:
				# We use the Looking Glass Go standard quilt (48 views)
				else:
					context.scene.addon_settings.quiltPreset = "5"

		return {'FINISHED'}


# an operator that controls lightfield window opening and closing
class LOOKINGGLASS_OT_lightfield_window(bpy.types.Operator):
	bl_idname = "lookingglass.lightfield_window"
	bl_label = "Cast to Looking Glass"
	bl_description = "Creates a window for the light field rendering on the current Looking Glass device"
	bl_options = {'REGISTER', 'INTERNAL'}


	# Update the Boolean property that creates the hologram rendering window
	def execute(self, context):

		# set the property to the correct value
		context.window_manager.addon_settings.ShowLightfieldWindow = (not context.window_manager.addon_settings.ShowLightfieldWindow)

		# protect Blender from crashing: the material preview and rendered shading of Cycles and Eevee cannot be cast
		if context.window_manager.addon_settings.ShowLightfieldWindow == True and LookingGlassAddon.cast_shading_unsupported(context):
			context.window_manager.addon_settings.ShowLightfieldWindow = False
			self.report({'ERROR'}, "The selected viewport uses Material Preview or Rendered shading, which cannot be cast with this render engine. Change its shading to Solid or Wireframe.")
			return {'CANCELLED'}

		# if the bool property was set to True
		if context.window_manager.addon_settings.ShowLightfieldWindow == True:

			# remember the invoking context (window, area, region), because the forced
			# redraw below can leave Blender without an active area / region
			window, area, region = context.window, context.area, context.region

			# assign the current viewport for the shading & overlay settings
			bpy.ops.lookingglass.blender_viewport_assign('EXEC_DEFAULT')

			# draw the new UI first: creating the lightfield window is slow and would
			# otherwise block the panel from updating until it has finished
			try:
				for a in context.screen.areas: a.tag_redraw()
				bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
			except Exception: pass

			# Invoke modal operator for the lightfield rendering in the original context
			if hasattr(context, "temp_override"):
				with context.temp_override(window=window, area=area, region=region):
					bpy.ops.render.viewport('INVOKE_DEFAULT')
			else:
				bpy.ops.render.viewport('INVOKE_DEFAULT')

		return {'FINISHED'}



class LOOKINGGLASS_PT_panel_general(bpy.types.Panel):
	bl_idname = "LOOKINGGLASS_PT_panel_general" # unique identifier for buttons and menu items to reference.
	bl_label = "View Settings" # display name in the interface.
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Looking Glass"


	# Draw handler for the panel layout
	def draw(self, context):
		layout = self.layout

		# camera settings (top of the panel)
		draw_camera_settings(layout, context)
		layout.separator()

		# render preview: look through a single view of the quilt
		draw_render_preview(layout, context)
		layout.separator(type='LINE', factor=2.0)

		column = layout.column()

		# Cast button (large, full width)
		row_window = column.row(align = True)
		row_window.scale_y = 1.6
		row_window.operator("lookingglass.lightfield_window", text="Cast to Looking Glass", icon='WINDOW', depress=context.window_manager.addon_settings.ShowLightfieldWindow)

		# Device selection
		# NOTE: Only the dropdown is deactivated when Looking Glass Bridge is not available.
		#		The refresh button stays active, because it is used to find the display again.
		row_device = column.row(align = True)
		row_device_list = row_device.row(align = True)
		row_device_list.prop(context.window_manager.addon_settings, "activeDisplay", text="")
		row_device.operator("lookingglass.refresh_display_list", text="", icon='FILE_REFRESH')

		# if no Looking Glass was detected AND debug mode is not activated
		if (not pylio.DeviceManager.count() and not LookingGlassAddon.debugging_use_dummy_device):

			# deactivate the lightfield window button
			row_window.enabled = False

		# if the Looking Glass Bridge is not added or not ready
		if (LookingGlassAddon.service is None or not LookingGlassAddon.service.is_ready()) and not LookingGlassAddon.debugging_use_dummy_device:

			# deactivate the looking glass selection and lightfield window button
			row_device_list.enabled = False
			row_window.enabled = False

		# if a Looking Glass is selected AND the lightfield window is shown,
		# display the lightfield window options directly below the button
		if hasattr(context.window_manager, "addon_settings") and int(context.window_manager.addon_settings.activeDisplay) != -1 and context.window_manager.addon_settings.ShowLightfieldWindow == True:
			column.separator()
			draw_lightfield_window_options(layout, context)




# ------------- The Camera Settings Panel ----------------
# an operator that adds a camera to the scene
class LOOKINGGLASS_OT_add_camera(bpy.types.Operator):
	bl_idname = "object.add_lookingglass_camera"
	bl_label = "Add Looking Glass Camera"
	bl_description = "Creates a new camera object with settings optimized for the Looking Glass"
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

	def execute(self, context):

		# first we add a new camera and link it to the scene
		camera_data = bpy.data.cameras.new(name='Looking Glass Camera')
		camera = bpy.data.objects.new('Looking Glass Camera', camera_data)
		bpy.context.scene.collection.objects.link(camera)

		# set the camera position
		camera.location.z = context.scene.addon_settings.focalPlane

		# then we apply all the default settings to the camera
		camera.data.sensor_fit = 'VERTICAL'
		camera.data.angle_y = radians(14)
		camera.data.clip_start = context.scene.addon_settings.clip_start
		camera.data.clip_end = context.scene.addon_settings.clip_end
		camera.data.dof.focus_distance = context.scene.addon_settings.focalPlane

		# if currently no camera is selected
		if context.scene.addon_settings.lookingglassCamera == None:

			# use the new camera as the Looking Glass Camera
			context.scene.addon_settings.lookingglassCamera = camera

		return {'FINISHED'}

# render preview, drawn in the "View Settings" panel
def draw_render_preview(layout, context):
	"""Draws the render preview: the swivel button and a view slider (limited to the views of the selected quilt)."""
	row = layout.row(align=True)
	sub = row.row(align=True)
	sub.scale_x = 2.0
	sub.operator("lookingglass.preview_camera", text="Activate Swivel", icon='VIEW_CAMERA', depress=context.scene.addon_settings.preview_active)
	row.prop(context.scene.addon_settings, "preview_view_index", text="View Image")


# camera settings, drawn inline in the "View Settings" panel
def draw_camera_settings(layout, context):
	"""Draws the Looking Glass camera settings."""


	# define a column of UI elements
	column = layout.column(align = True)

	# Camera selection
	row_camera = column.row(align = True)
	column_1 = row_camera.column(align=True)
	row_camera_a = column_1.row(align = True)
	row_camera_a.enabled = (not context.scene.addon_settings.toggleCameraSync)
	row_camera_a.prop(context.scene.addon_settings, "lookingglassCamera", icon='VIEW_CAMERA', text="")
	row_camera_a.operator("object.add_lookingglass_camera", text="", icon='ADD')
	row_camera_a.separator()

	# Camera options
	column_2 = row_camera.column(align=True)
	row_camera_b = column_2.row(align = True)
	row_camera_b.prop(context.scene.addon_settings, "showFrustum", text="", icon='MESH_CUBE')
	row_camera_b.prop(context.scene.addon_settings, "showFocalPlane", text="", icon='MESH_PLANE')
	row_camera_b.prop(context.scene.addon_settings, "toggleCameraSync", text="", icon='LINKED')

	# display the clipping settings
	camera = context.scene.addon_settings.lookingglassCamera
	if camera:

		column.separator()
		row_clip_start = column.row(align = True)
		row_clip_start.prop(context.scene.addon_settings, "clip_start")
		row_clip_start.prop(context.scene.addon_settings, "lockClippingPlanes", text="", icon='PINNED')
		row_clip_end = column.row(align = True)
		row_clip_end.prop(context.scene.addon_settings, "clip_end")
		row_clip_end.prop(context.scene.addon_settings, "lockClippingPlanes", text="", icon='PINNED')
		row_focal_plane = column.row(align = True)
		row_focal_plane.prop(context.scene.addon_settings, "focalPlane")
		row_focal_plane.prop(context.scene.addon_settings, "toggleFocalSync", text="", icon='LINKED')

		# row_preset = column.row(align = True)
		# row_preset.prop(context.scene.addon_settings, "clip_start")
		# row_output = column.row(align = True)
		# row_output.prop(context.scene.addon_settings, "clip_end")
		# row_render_still = column.row(align = True)
		# row_render_still.prop(context.scene.addon_settings, "focalPlane")

	# # if no camera is Selected
	# if context.scene.addon_settings.lookingglassCamera == None:

	# 	# disable clipping and focal plane modifieres
	# 	row_clip_start.enabled = False
	# 	row_clip_end.enabled = False
	# 	row_focal_plane.enabled = False

# ------------- The Render Settings Panel ----------------
# the panel for the camera settings
class LOOKINGGLASS_PT_panel_render(bpy.types.Panel):
	bl_idname = "LOOKINGGLASS_PT_panel_render" # unique identifier for buttons and menu items to reference.
	bl_label = "Quilt Creation" # display name in the interface.
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Looking Glass"


	# define own poll method to be able to hide / show the panel on demand
	@classmethod
	def poll(self, context):

		# the panel should always be drawn
		return True

	# draw the UI for the configuration options
	def draw(self, context):
		layout = self.layout
		settings = context.scene.addon_settings

		# what to build the quilt from
		row_title = layout.row(align = True)
		row_title.alignment = 'CENTER'
		row_title.label(text="Build From:")
		layout.row(align = True).prop(settings, "quilt_build_mode", expand=True)

		# quilt generation from files (formerly the "Advanced" panel)
		if settings.quilt_build_mode == 'FILES':
			layout.prop(settings, "advanced_quilt_source_path", text="Build Quilt from Files")
			layout.separator(type='LINE', factor=2.0)
			row = layout.row(align=True)
			row.scale_y = 2.0
			row.operator("lookingglass.build_quilt_from_files", text="Build", icon='RENDER_STILL')

		else:

			# NOTE: Whether the settings are taken from the connected device ("render_use_device") is
			#		decided automatically: it is on when a Looking Glass is connected, otherwise off.
			row_orientation = layout.row(align = True)
			row_orientation.prop(settings, "render_device_type", text="Device")
			row_preset = layout.row(align = True)
			row_preset.prop(settings, "render_quilt_preset", text="Quilt")
			row_output = layout.row(align = True)
			row_output.prop(settings, "render_output", text="Output")
			row_source = layout.row(align = True)
			row_source.prop(settings, "render_source", text="Source")
			layout.separator(type='LINE', factor=2.0)

			use_multiview = (context.preferences.addons[__package__].preferences.camera_mode == '1')

			# if no lockfile was detected on start-up OR the render job is running
			if not LookingGlassAddon.has_lockfile or LookingGlassAddon.RenderInvoked:

				row_render = layout.row(align = True)
				row_render.scale_y = 2.0

				# while a quilt is rendered: show the progress bar and the stop button
				if LookingGlassAddon.RenderInvoked == True:
					row_render.prop(settings, "render_progress", text="", slider=True)
					row_render.prop(settings, "render_stop", text="", icon='CANCEL')

				# the button starts what the source dropdown says
				elif settings.render_source in ('QUILT', 'ANIMATION'):
					render_quilt = row_render.operator("render.quilt", text="Render", icon='CAMERA_DATA')
					render_quilt.animation = (settings.render_source == 'ANIMATION')
					render_quilt.use_multiview = use_multiview
				else:
					render_headless = row_render.operator("lookingglass.render_headless", text="Render", icon='CAMERA_DATA')
					render_headless.animation = (settings.render_source == 'ANIMATION_HEADLESS')

			# if a lockfile was detected on start-up
			else:

				# disable the UI
				row_orientation.enabled = False
				row_preset.enabled = False
				row_output.enabled = False
				row_source.enabled = False

				# inform the user and provide options to continue or to discard
				row_render = layout.row(align = True)
				row_render.label(text = "Last render job incomplete:", icon="ERROR")

				row_continue = layout.row(align = False)
				render_quilt = row_continue.operator("render.quilt", text="Continue", icon='RENDER_STILL')
				render_quilt.use_lockfile = True
				render_quilt.use_multiview = use_multiview
				render_quilt = row_continue.operator("render.quilt", text="Discard", icon='CANCEL')
				render_quilt.use_lockfile = True
				render_quilt.use_multiview = use_multiview
				render_quilt.discard_lockfile = True

			# disable the render settings, if a rendering process is running
			if LookingGlassAddon.RenderInvoked == True:
				row_orientation.enabled = False
				row_preset.enabled = False
				row_output.enabled = False
				row_source.enabled = False

			# if no camera is selected
			if settings.lookingglassCamera == None:

				# disable all elements
				row_orientation.enabled = False
				row_preset.enabled = False
				row_output.enabled = False
				row_source.enabled = False
				row_render.enabled = False


		# metadata handling
		layout.separator(type='SPACE')
		column_options = layout.column(align = True)
		column_options.prop(settings, "render_add_suffix", text="Add Metadata")
		column_options.prop(settings, "shutdown_after_render", text="Shut off Computer after Render")


# an operator that renders the quilt in a separate background Blender process
class LOOKINGGLASS_OT_render_headless(bpy.types.Operator):
	bl_idname = "lookingglass.render_headless"
	bl_label = "Render Headlessly"
	bl_description = "Save the file, close Blender and render the quilt in a separate Blender process without a user interface. The output settings of this file are used"
	bl_options = {'REGISTER', 'INTERNAL'}

	animation: bpy.props.BoolProperty(
								name = "Render Animation",
								description = "Render the frame range as quilt animation instead of the current frame as a single quilt",
								default = False,
								)

	@classmethod
	def poll(cls, context):
		return context.scene.addon_settings.lookingglassCamera is not None and not LookingGlassAddon.RenderInvoked

	def invoke(self, context, event):

		# the background process loads the file from disk
		if not bpy.data.filepath:
			self.report({'ERROR'}, "Save the Blender file first: the headless render loads it from disk.")
			return {'CANCELLED'}

		return context.window_manager.invoke_props_dialog(self, width = 480)

	def draw(self, context):
		layout = self.layout
		layout.label(text = "Blender will save this file and close.")
		layout.label(text = "The quilt is then rendered in a separate Blender process without a window.")
		layout.separator()
		layout.label(text = "File: " + os.path.basename(bpy.data.filepath))
		layout.label(text = "Output: " + bpy.path.abspath(context.scene.render.filepath))

	def execute(self, context):
		import subprocess
		from .updater import RESTART_HELPER

		# save the file, because the background process uses the settings stored in it
		try:
			bpy.ops.wm.save_mainfile()
		except Exception as e:
			self.report({'ERROR'}, "Could not save the file: %s" % e)
			return {'CANCELLED'}

		# the command that renders the quilt in the background (see "Renderfarm Implementation" in the README)
		command = [bpy.app.binary_path, '-b', bpy.data.filepath, '--', '--alicelg-render-anim' if self.animation else '--alicelg-render']

		# use the camera mode of the add-on preferences: in the single camera mode, the views are rendered one by one,
		# so the console can show the progress per view
		if context.preferences.addons[__package__].preferences.camera_mode == '0': command.append('--alicelg-single-camera')

		# show the progress in a new console window (Windows) or write it to a log file
		environment = os.environ.copy()
		if sys.platform == 'win32': environment['LG_NEW_CONSOLE'] = '1'
		else: environment['LG_LOGFILE'] = os.path.join(LookingGlassAddon.logpath, 'headless-render.log')

		# start the render as soon as this Blender instance has quit
		try:
			flags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if sys.platform == 'win32' else 0
			subprocess.Popen([sys.executable, "-c", RESTART_HELPER, str(os.getpid())] + command, env = environment, creationflags = flags, close_fds = True)
		except Exception as e:
			self.report({'ERROR'}, "Could not start the headless render: %s" % e)
			return {'CANCELLED'}

		# close this instance
		bpy.ops.wm.quit_blender()
		return {'FINISHED'}


# an operator that positions the camera for a specific view
class LOOKINGGLASS_OT_preview_camera(bpy.types.Operator):
	bl_idname = "lookingglass.preview_camera"
	bl_label = "Activate Swivel"
	bl_description = "Toggle camera preview for the selected view index"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		import pylightio as pylio
		from math import tan, radians
		from mathutils import Matrix

		scene = context.scene
		addon_settings = scene.addon_settings
		camera_original = addon_settings.lookingglassCamera

		if camera_original is None:
			self.report({'ERROR'}, "No Looking Glass camera selected!")
			return {'CANCELLED'}

		# If preview is currently active, restore original position
		if addon_settings.preview_active:
			# Restore original matrix
			matrix_list = list(addon_settings.preview_original_matrix)
			matrix = Matrix((
				matrix_list[0:4],
				matrix_list[4:8],
				matrix_list[8:12],
				matrix_list[12:16]
			))
			camera_original.matrix_world = matrix
			camera_original.data.shift_x = addon_settings.preview_original_shift
			addon_settings.preview_active = False
			return {'FINISHED'}

		# Store original camera state before applying preview
		original_matrix = camera_original.matrix_world.copy()
		matrix_flat = []
		for row in original_matrix:
			for val in row:
				matrix_flat.append(val)
		addon_settings.preview_original_matrix = matrix_flat
		addon_settings.preview_original_shift = camera_original.data.shift_x

		# GET QUILT PRESET DATA
		# ++++++++++++++++++++++++++++++++++++++++++++
		# if the device settings shall be used
		if addon_settings.render_use_device:

			# get active device
			device = pylio.DeviceManager.get_active()

			# if a device is connected
			if device:

				# get the default quilt settings from the device
				columns = device.default_quilt_columns
				rows = device.default_quilt_rows
				total_views = device.default_quilt_columns * device.default_quilt_rows
				view_cone = device.view_cone

			# if no device is connected
			else:
				self.report({'ERROR'}, "No Looking Glass device connected!")
				return {'CANCELLED'}

		# if a preset shall be used
		else:

			# get the preset
			preset = pylio.LookingGlassQuilt.formats.get(int(addon_settings.render_quilt_preset))

			# get the quilt settings from the preset
			columns = int(preset['columns'])
			rows = int(preset['rows'])
			total_views = int(preset['total_views'])
			view_cone = 40.0  # Default view cone in degrees

		# Ensure view index is within bounds
		view_index = addon_settings.preview_view_index
		if view_index >= total_views:
			view_index = total_views - 1
			addon_settings.preview_view_index = view_index

		# CAMERA POSITIONING MATH (from lightfield_render.py)
		# +++++++++++++++++++++++++++++++++++++++++++++++++++
		
		# get camera's modelview matrix
		view_matrix = camera_original.matrix_world.copy()

		# correct for the camera scaling
		view_matrix = view_matrix @ Matrix.Scale(1/camera_original.scale.x, 4, (1, 0, 0))
		view_matrix = view_matrix @ Matrix.Scale(1/camera_original.scale.y, 4, (0, 1, 0))
		view_matrix = view_matrix @ Matrix.Scale(1/camera_original.scale.z, 4, (0, 0, 1))

		# calculate the inverted view matrix
		view_matrix_inv = view_matrix.inverted_safe()

		# The field of view set by the camera
		fov = camera_original.data.angle

		# calculate cameraSize from its distance to the focal plane and the FOV
		cameraDistance = addon_settings.focalPlane
		cameraSize = cameraDistance * tan(fov / 2)

		# start at view_cone * 0.5 and go up to -view_cone * 0.5
		offsetAngle = (0.5 - view_index / (total_views - 1)) * radians(view_cone)

		# calculate the offset that the camera should move
		offset = cameraDistance * tan(offsetAngle)

		# translate the camera by the calculated offset in x-direction
		# NOTE: the matrix multiplications first transform the camera location into camera coordinates,
		#		then we apply the offset and transform back to world coordinates
		camera_original.matrix_world = view_matrix @ (Matrix.Translation((-offset, 0, 0)) @ LookingGlassAddon.view_toe_in(camera_original.data, offsetAngle) @ (view_matrix_inv @ original_matrix.copy()))

		# modify the projection matrix, relative to the camera size
		camera_original.data.shift_x = addon_settings.preview_original_shift + LookingGlassAddon.view_shift(camera_original.data, offset, cameraSize)

		# Mark preview as active
		addon_settings.preview_active = True

		return {'FINISHED'}


# ------------- The Lightfield Settings Panel ----------------
# Operator for manual redrawing of the Looking Glass (for manual Live View Mode)
class LOOKINGGLASS_OT_refresh_lightfield(bpy.types.Operator):
	bl_idname = "lookingglass.refresh_lightfield"
	bl_label = "Refresh the Light Field window."
	bl_description = "Render the current view directly in your Looking Glass"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):

		# refresh the Looking Glass
		context.window_manager.addon_settings.viewport_manual_refresh = True

		return {'FINISHED'}

def draw_lightfield_window_options(layout, context):
	"""Draws the lightfield window options inside the main Looking Glass panel."""

	# TABS to swap between "live preview" and a "loaded quilt image"
	layout.label(text="Select Cast Source")
	row = layout.row()
	row.prop(context.window_manager.addon_settings, "renderMode", expand=True)

	# define a column of UI elements
	column = layout.column(align = True)
	column.separator()

	# If no LookingGlass is selected
	if int(context.window_manager.addon_settings.activeDisplay) == -1:

		# ... then disable all UI elements except for the drop down menu and the refresh button
		column.enabled = False
		row.enabled = False

	# if the lightfield window is in viewport mode
	if context.window_manager.addon_settings.renderMode == '0':

		# all viewport settings live in one collapsible section
		# (collapsible via layout.panel on Blender 4.1+, otherwise a plain box)
		if hasattr(column, "panel"):
			header, body = column.panel("LOOKINGGLASS_PT_viewport_settings", default_closed=False)
			header.label(text="Cast Settings")
		else:
			body = column.box()
			body.label(text="Cast Settings")
		if body is not None:

			# Lightfield rendering mode & refresh button
			row_preset = body.row()
			row_preset.prop(context.window_manager.addon_settings, "lightfieldMode", text="")

			# Automatic refresh: "Patient Mode" button (only update once the user's operator has finished)
			if int(context.window_manager.addon_settings.lightfieldMode) == 0:
				row_preset.prop(context.window_manager.addon_settings, "patient_mode", text="", toggle=True, icon='TIME')

			# Manual refresh: refresh button
			else:
				row_preset.operator("lookingglass.refresh_lightfield", text="", icon='FILE_REFRESH')

			# time without changes after which the full-quality light field is shown (automatic mode only)
			if int(context.window_manager.addon_settings.lightfieldMode) == 0:
				body.prop(context.window_manager.addon_settings, "full_quality_delay", slider=True)

			# Preview settings
			row_output = body.row(align = True)
			row_output.prop(context.window_manager.addon_settings, "lightfield_preview_mode", text="")

			# Shading & overlay settings
			body.separator()
			draw_shading_overlays_settings(body, context)


	# if the lightfield window is in quilt viewer mode
	elif context.window_manager.addon_settings.renderMode == '1':

		# display all settings for the quilt view mode
		row = column.row(align = True)
		row.label(text="Select a Quilt Image to Display:")

		row = column.row(align = True)
		row.template_ID(context.window_manager.addon_settings, "quiltImage", open="image.open")



# ------------- Subpanel for overlay & shading settings ----------------
# Operator for manual redrawing of the Looking Glass (for manual Live View Mode)
class LOOKINGGLASS_OT_blender_viewport_assign(bpy.types.Operator):
	bl_idname = "lookingglass.blender_viewport_assign"
	bl_label = "Assign Active Viewport"
	bl_description = "Use the shading and overlay settings of this Blender viewport"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):

		# if the user activated the option to
		# use the shading and overlay settings of the currently used Blender 3D viewport
		if context.scene.addon_settings.viewportMode == 'BLENDER' and context.space_data is not None and context.space_data.type == 'VIEW_3D':

			# set the Workspace list to the current workspace
			context.scene.addon_settings.blender_workspace = context.workspace.name

			# set the 3D View list to the current 3D view
			context.scene.addon_settings.blender_view3d = str(context.space_data)

		return {'FINISHED'}

# Shading & overlay settings, drawn inside the light field viewport settings
def draw_shading_overlays_settings(layout, context):
	"""Draws the shading & overlay settings of the lightfield viewport."""

	# define a column of UI elements
	column = layout.column(align = True)

	# if the automatic render mode is active
	if int(context.window_manager.addon_settings.renderMode) == 0:

		# TABS to swap between "Custom Viewport" and a "Blender Viewport"
		row = column.row(align = True)
		row.prop(context.scene.addon_settings, "viewportMode", expand=True)

		# if the current mode is "BLENDER"
		if context.scene.addon_settings.viewportMode == "BLENDER":

			#column.separator()

			row = column.row(align = True)
			column = layout.column(align = True)
			row = column.row(align = True)
			row.label(text="Mirror Settings From:")
			row = column.row(align = True)
			row.prop(context.scene.addon_settings, "blender_workspace")
			row = column.row(align = True)
			row.prop(context.scene.addon_settings, "blender_view3d")

			column.separator()

			row = column.row(align = True)
			row.operator("lookingglass.blender_viewport_assign")

			# if the chosen workspace has no 3D View
			if context.scene.addon_settings.blender_view3d == "None":

				# disable the manual selection options
				row.enabled = False

		# if the current mode is "CUSTOM"
		elif context.scene.addon_settings.viewportMode == "CUSTOM":

			column.separator()

			row = column.row(align = True)
			row.label(text="Shading")
			#column.separator()
			row.prop(context.scene.addon_settings, "shadingMode", expand=True)
			column.separator()
			row = column.row(align = True)
			column_1 = row.column(align=True)
			column_1.prop(context.scene.addon_settings, "viewport_show_xray")
			column_2 = row.column(align=True)
			column_2.prop(context.scene.addon_settings, "viewport_xray_alpha", slider=True)

			# if x-ray is deactivated
			if context.scene.addon_settings.viewport_show_xray == False:
				# disable the slider
				column_2.enabled = False

			row = column.row(align = True)
			row.prop(context.scene.addon_settings, "viewport_use_dof")

			column.separator()

			row = column.row(align = True)
			row.label(text="Guides")
			row = column.row(align = True)
			row.prop(context.scene.addon_settings, "viewport_show_floor")
			row.prop(context.scene.addon_settings, "viewport_show_axes", toggle=1)
			column.separator()
			row = column.row(align = True)
			row.prop(context.scene.addon_settings, "viewport_grid_scale")

			column.separator()

			row = column.row(align = True)
			row.label(text="Composition Guides")
			grid = column.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=False, align=True)
			for name in ("center", "diagonal", "thirds", "golden", "golden_triangle_a", "golden_triangle_b"):
				grid.prop(context.scene.addon_settings, "viewport_guide_" + name)
			row = column.row(align = True)
			row.prop(context.scene.addon_settings, "viewport_guide_opacity", slider=True)

			column.separator()

			row = column.row(align = True)
			row.label(text="Objects")
			row = column.row(align = True)
			column_1 = row.column(align = True)
			column_1.prop(context.scene.addon_settings, "viewport_show_extras")
			column_1.prop(context.scene.addon_settings, "viewport_show_relationship_lines")
			column_1.prop(context.scene.addon_settings, "viewport_show_outline_selected")

			column_2 = row.column(align = True)
			column_2.prop(context.scene.addon_settings, "viewport_show_bones")
			column_2.prop(context.scene.addon_settings, "viewport_show_motion_paths")
			column_2.prop(context.scene.addon_settings, "viewport_show_origins")
			column_2.prop(context.scene.addon_settings, "viewport_show_origins_all")

			column.separator()

			row = column.row(align = True)
			row = row.label(text="Geometry")
			row = column.row(align = True)
			column_1 = row.column(align=True)
			column_1.prop(context.scene.addon_settings, "viewport_show_wireframes")
			column_2 = row.column(align=True)
			column_2.prop(context.scene.addon_settings, "viewport_wireframe_threshold", slider=True)
			row = column.row(align = True)
			row.prop(context.scene.addon_settings, "viewport_show_face_orientation")

			# if no wireframes shall be displayed
			if context.scene.addon_settings.viewport_show_wireframes == False:
				# disable the slider
				column_2.enabled = False


# ------------- Buttons & elements in region headers ----------------
# Button for the blocks viewport preview
class LOOKINGGLASS_HT_button_viewport_blocks(bpy.types.Header):
	bl_label = "Hologram Preview" # display name in the interface.
	bl_space_type = "VIEW_3D"
	bl_region_type = "HEADER"

	def draw_item(self, context):
		layout = self.layout
		row = layout.row(align=True)
		row.prop(context.scene.addon_settings, "viewport_block_show", icon='META_PLANE', text="")
		sub = row.row(align=True)
		sub.active = context.scene.addon_settings.viewport_block_show
		sub.popover(panel="LOOKINGGLASS_PT_panel_blocks_viewport_options", text="")

		# if the cycles render engine is active in this viewport
		if context.space_data.shading.type == 'RENDERED' and context.engine == 'CYCLES':
			row.enabled = False

	def draw(self, context):
		pass

# panel for the hologram preview settings
class LOOKINGGLASS_PT_panel_blocks_viewport_options(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'HEADER'
	bl_label = "Hologram Preview"
	bl_ui_units_x = 8

	def draw(self, context):
		layout = self.layout
		layout.label(text="Hologram Preview")
		layout.active = context.scene.addon_settings.viewport_block_show

		# define a column of UI elements
		column = layout.column(align = True)

        # Location
		row_alignment_label = column.row(align = True)
		row_alignment_label.label(text="Alignment")
		row_alignment = column.row(align = True)
		row_alignment.prop(context.scene.addon_settings, "viewport_block_alignment", expand=True)

		# Hologram preview settings
        # Scaling factor
		row_appearance_label = column.row(align = True)
		row_appearance_label.label(text="Appearance")
		row_scaling = column.row(align = True)
		row_scaling.prop(context.scene.addon_settings, "viewport_block_scaling_factor", slider=True)
        # Alpha value
		row_alpha = column.row(align = True)
		row_alpha.prop(context.scene.addon_settings, "viewport_block_alpha", slider=True)

# Button for the blocks display in the image editor
class LOOKINGGLASS_HT_button_imageeditor_blocks(bpy.types.Header):
	bl_label = "Hologram Image Editor Preview" # display name in the interface.
	bl_space_type = "IMAGE_EDITOR"
	bl_region_type = "HEADER"

	def draw_item(self, context):
		layout = self.layout
		row = layout.row(align=True)
		row.prop(context.scene.addon_settings, "imageeditor_block_show", icon='META_PLANE', text="")
		sub = row.row(align=True)
		sub.active = context.scene.addon_settings.imageeditor_block_show
		sub.popover(panel="LOOKINGGLASS_PT_panel_blocks_imageeditor_options", text="")

	def draw(self, context):
		pass

# panel for the block display settings
class LOOKINGGLASS_PT_panel_blocks_imageeditor_options(bpy.types.Panel):
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'HEADER'
	bl_label = "Display hologram preview"
	bl_ui_units_x = 13

	def draw(self, context):
		layout = self.layout
		layout.label(text="Hologram Preview")
		layout.active = context.scene.addon_settings.imageeditor_block_show

		# was the quilt and device type automatically detected
		if LookingGlassAddon.ImageBlockRenderer.is_imageeditor_detected():

			# Info for user
			row_info = layout.row(align = True)
			row_info.label(text="Quilt type automatically detected.")

		# Device Type
		row_orientation = layout.row(align = True)
		column_1 = row_orientation.row(align = True)
		column_1.label(text="Device Type:")
		column_1.scale_x = 0.3
		column_2 = row_orientation.row(align = True)
		column_2.prop(context.scene.addon_settings, "imageeditor_block_device_type", text="")
		column_2.scale_x = 0.7

		# Quilt settings
		row_preset = layout.row(align = True)
		row_preset.enabled = (not LookingGlassAddon.ImageBlockRenderer.is_imageeditor_detected())
		column_1 = row_preset.row(align = True)
		column_1.label(text="Quilt Preset:")
		column_1.scale_x = 0.3
		column_2 = row_preset.row(align = True)
		column_2.prop(context.scene.addon_settings, "imageeditor_block_quilt_preset", text="")
		column_2.scale_x = 0.7
