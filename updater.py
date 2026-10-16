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
# Detects whether the add-on's GitHub repository has new commits and
# installs the update. If the installed commit is known, only the files
# that changed between the installed and the latest commit are downloaded.

# ------------------ INTERNAL MODULES --------------------
from .globals import *

# ------------------- EXTERNAL MODULES -------------------
import bpy
import json, threading, urllib.request, urllib.parse, io, zipfile, hashlib

# ---------------- GLOBAL ADDON LOGGER -------------------
import logging
LookingGlassAddonLogger = logging.getLogger('Alice/LG')

# ------------------- CONFIGURATION ---------------------
GITHUB_REPO = "11moo11/AliceLG"
GITHUB_BRANCH = "master"
API_URL = "https://api.github.com/repos/%s" % GITHUB_REPO
RAW_URL = "https://raw.githubusercontent.com/%s" % GITHUB_REPO
TIMEOUT = 10

# paths that are never touched by an update (large / user-specific data)
PROTECTED_PREFIXES = ("lib/", "logs/", "tmp/", "__pycache__/", ".git")

# NOTE: The only exception in "lib/" are the python source files of pyLightIO (which contain
#		the communication with Looking Glass Bridge). All other files in "lib/" are large binaries.
UPDATED_LIB_PREFIX = "lib/pylightio/"

STATE_FILE = os.path.join(LookingGlassAddon.path, ".installed_commit")


class LookingGlassAddonUpdater:
	"""Holds the update state; all network access happens in threads."""

	checking = False
	updating = False
	latest_sha = None		# newest commit on GitHub
	latest_message = ""
	update_available = False
	restart_needed = False		# an update was installed successfully
	status = "Not checked yet."
	_lock = threading.Lock()

	@staticmethod
	def installed_sha():
		try:
			with open(STATE_FILE) as f: return f.read().strip() or None
		except OSError:
			return None

	@staticmethod
	def _get(url, binary = False):
		req = urllib.request.Request(url, headers = {"User-Agent": "Alice-LG-updater", "Accept": "application/vnd.github+json"})
		with urllib.request.urlopen(req, timeout = TIMEOUT) as r:
			data = r.read()
		return data if binary else json.loads(data.decode("utf-8"))

	@staticmethod
	def _redraw():
		# worker threads must not touch bpy directly; this timer runs in the main thread
		def _tag():
			try:
				for window in bpy.context.window_manager.windows:
					for area in window.screen.areas: area.tag_redraw()
			except Exception: pass
			return None
		bpy.app.timers.register(_tag, first_interval = 0.1)

	@classmethod
	def check(cls):
		"""Start a non-blocking check against GitHub."""
		with cls._lock:
			if cls.checking or cls.updating: return
			cls.checking = True
			cls.status = "Checking for updates ..."
		threading.Thread(target = cls._check_worker, daemon = True).start()

	@classmethod
	def _check_worker(cls):
		try:
			info = cls._get("%s/commits/%s" % (API_URL, GITHUB_BRANCH))
			cls.latest_sha = info["sha"]
			cls.latest_message = info["commit"]["message"].split("\n")[0]
			installed = cls.installed_sha()
			cls.update_available = installed != cls.latest_sha
			if cls.update_available:
				cls.status = "Update available: %s (%s)" % (cls.latest_message, cls.latest_sha[:7])

			# even if the commit is the same: are the pyLightIO sources (Bridge communication) outdated?
			elif cls._outdated_pylightio_files():
				cls.update_available = True
				cls.status = "Update available: the Looking Glass Bridge communication files are outdated (%s)." % cls.latest_sha[:7]
			else:
				cls.status = "Alice/LG is up to date (%s)." % cls.latest_sha[:7]
			LookingGlassAddonLogger.info("Update check: " + cls.status)
		except Exception as e:
			cls.status = "Update check failed: %s" % e
			LookingGlassAddonLogger.warning(cls.status)
		finally:
			cls.checking = False
			cls._redraw()

	@classmethod
	def update(cls):
		"""Start a non-blocking update to the latest commit."""
		with cls._lock:
			if cls.checking or cls.updating or not cls.latest_sha: return
			cls.updating = True
			cls.status = "Updating ..."
		threading.Thread(target = cls._update_worker, daemon = True).start()

	@staticmethod
	def _safe_target(rel):
		"""Return the absolute target path or None if it is protected / outside the add-on."""
		is_pylightio_source = rel.startswith(UPDATED_LIB_PREFIX) and rel.endswith(".py")
		if rel.startswith(PROTECTED_PREFIXES) and not is_pylightio_source: return None
		target = os.path.normpath(os.path.join(LookingGlassAddon.path, rel))
		if os.path.commonpath([target, LookingGlassAddon.path]) != os.path.normpath(LookingGlassAddon.path): return None
		return target

	@classmethod
	def _outdated_pylightio_files(cls):
		"""List the pyLightIO source files that differ from the latest commit (compares git blob hashes)."""
		outdated = []
		tree = cls._get("%s/git/trees/%s?recursive=1" % (API_URL, cls.latest_sha))
		for item in tree.get("tree", []):
			path = item["path"]
			if item["type"] != "blob": continue
			target = cls._safe_target(path)
			if not target or not (path.startswith(UPDATED_LIB_PREFIX) and path.endswith(".py")): continue

			# git blob hash of the local file
			try:
				with open(target, "rb") as f: local = f.read()
				local_sha = hashlib.sha1(b"blob %d\0" % len(local) + local).hexdigest()
			except OSError:
				local_sha = None

			if local_sha != item["sha"]: outdated.append((path, target))

		return outdated

	@classmethod
	def _sync_pylightio(cls):
		"""Download all pyLightIO source files that differ from the latest commit."""
		count = 0
		for path, target in cls._outdated_pylightio_files():
			data = cls._get("%s/%s/%s" % (RAW_URL, cls.latest_sha, urllib.parse.quote(path)), binary = True)
			os.makedirs(os.path.dirname(target), exist_ok = True)
			with open(target, "wb") as f: f.write(data)
			count += 1
			LookingGlassAddonLogger.info("Updated pyLightIO source file: %s" % path)

		return count

	@classmethod
	def _update_worker(cls):
		try:
			installed = cls.installed_sha()
			changed, removed = None, []

			# fast path: only the files that differ from the installed commit
			if installed:
				try:
					cmp = cls._get("%s/compare/%s...%s" % (API_URL, installed, cls.latest_sha))
					if len(cmp.get("files", [])) < 300:
						changed, removed = [], []
						for f in cmp["files"]:
							if f["status"] == "removed": removed.append(f["filename"])
							else: changed.append(f["filename"])
				except Exception:
					changed = None

			if changed is not None:
				for rel in changed:
					target = cls._safe_target(rel)
					if not target: continue
					data = cls._get("%s/%s/%s" % (RAW_URL, cls.latest_sha, urllib.parse.quote(rel)), binary = True)
					os.makedirs(os.path.dirname(target), exist_ok = True)
					with open(target, "wb") as f: f.write(data)
				for rel in removed:
					target = cls._safe_target(rel)
					if target and os.path.isfile(target): os.remove(target)
				count = len(changed) + len(removed)

			# slow path: full snapshot (first update or compare failed)
			else:
				data = cls._get("%s/zipball/%s" % (API_URL, cls.latest_sha), binary = True)
				count = 0
				with zipfile.ZipFile(io.BytesIO(data)) as z:
					for name in z.namelist():
						rel = name.split("/", 1)[1] if "/" in name else ""
						if not rel or rel.endswith("/"): continue
						target = cls._safe_target(rel)
						if not target: continue
						os.makedirs(os.path.dirname(target), exist_ok = True)
						with open(target, "wb") as f: f.write(z.read(name))
						count += 1

			# make sure that the pyLightIO sources are up to date (previous updates did not touch them)
			try: count += cls._sync_pylightio()
			except Exception as e: LookingGlassAddonLogger.warning("Could not check the pyLightIO sources: %s" % e)

			with open(STATE_FILE, "w") as f: f.write(cls.latest_sha)
			cls.update_available = False
			cls.restart_needed = True
			cls.status = "Updated %d file(s) to %s. Restart Blender to apply." % (count, cls.latest_sha[:7])
			LookingGlassAddonLogger.info(cls.status)
		except Exception as e:
			cls.status = "Update failed: %s" % e
			LookingGlassAddonLogger.error(cls.status)
		finally:
			cls.updating = False
			cls._redraw()


class LOOKINGGLASS_OT_check_update(bpy.types.Operator):
	bl_idname = "lookingglass.check_update"
	bl_label = "Check for Updates"
	bl_description = "Check the GitHub repository for a newer version of Alice/LG"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):
		LookingGlassAddonUpdater.check()
		return {'FINISHED'}


class LOOKINGGLASS_OT_install_update(bpy.types.Operator):
	bl_idname = "lookingglass.install_update"
	bl_label = "Install Update"
	bl_description = "Download only the changed files from GitHub and install them. Blender must be restarted afterwards"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):
		LookingGlassAddonUpdater.update()
		return {'FINISHED'}


def draw_update_ui(layout):
	"""Draws the update section; used by the add-on preferences."""
	u = LookingGlassAddonUpdater
	box = layout.box()
	box.label(text = u.status, icon = 'URL')
	row = box.row()
	row.enabled = not (u.checking or u.updating)
	row.operator("lookingglass.check_update", icon = 'FILE_REFRESH')

	# after a successful update: tell the user (in red) that Blender must be restarted
	if u.restart_needed:
		sub = row.row()
		sub.alert = True
		sub.label(text = "Restart Blender", icon = 'ERROR')

	else:
		sub = row.row()
		sub.enabled = u.update_available and not (u.checking or u.updating)
		sub.operator("lookingglass.install_update", icon = 'IMPORT')


def auto_check():
	"""Startup check; honours the preference (default: on)."""
	try:
		prefs = bpy.context.preferences.addons[__package__].preferences
		if not prefs.check_updates_on_startup: return None
	except Exception:
		pass
	LookingGlassAddonUpdater.check()
	return None
