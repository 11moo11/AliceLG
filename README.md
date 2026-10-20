# Alice/LG - Blender Add-on for Looking Glass Displays (fork with a simplified interface)

This repository is an unofficial fork of [Alice/LG by Christian Stolze](https://github.com/regcs/AliceLG). Alice/LG lets you display Blender scenes and render quilts for Looking Glass light field displays. This fork keeps that functionality and changes how it is operated, with the aim of making the interaction simpler.

## Please read first: AI-generated code

All changes in this fork were made entirely with Claude, an AI model from Anthropic, following instructions from the fork's maintainer. The code has not been independently reviewed or audited. If you have ethical objections to AI-generated code, this fork is not for you. The [original add-on](https://github.com/regcs/AliceLG) is the alternative.

## About Alice/LG
Alice/LG was created by Christian Stolze for using Blender with Looking Glass holographic displays. Version 2.x was developed in collaboration with the [Looking Glass Factory](https://lookingglassfactory.com/). The original project, its releases and its documentation are at [github.com/regcs/AliceLG](https://github.com/regcs/AliceLG). Please report problems with this fork in this repository's issues, not to the original author.

## What this fork changes
- The panels are reorganized: camera settings and the display selection are in one _View Settings_ panel, and everything for rendering quilts is in a _Quilt Creation_ panel.
- Showing your scene in the Looking Glass is done with a single _Cast to Looking Glass_ button.
- The hologram updates automatically when the scene changes, objects are hidden or shown, or viewport shading / overlay settings change.
- The preview while you edit is adjustable (_Preview Quality_, _Full-quality refresh_, _Patient Mode_), and the defaults can be set in the add-on preferences.
- The add-on can check for and install updates from its preferences.

## Features of Alice/LG
- integration into the common Blender workflow
- an optional view frustum representing the Looking Glass volume in the scene
- a light field viewport in the Looking Glass with automatic and manual refresh modes
- render any camera view as single quilt image or quilt animation
- decide if you want to keep the separate view files or just the final quilt
- support for multiple scenes and view layers
- camera & quilt settings are saved with your Blender file
- support for the available Looking Glass displays (including the Looking Glass Go)
- _Experimental feature:_ Detect incomplete render jobs (see below for details)

## System Requirements
- Windows, Linux, or macOS
- [Blender 2.93.6 or later](https://www.blender.org/download/)
- [Looking Glass Bridge or HoloPlay Service (for legacy devices)](https://lookingglassfactory.com/software)

## Installation

1. [Download](https://lookingglassfactory.com/software) and install the Looking Glass Bridge (or HoloPlay Service) app on your PC or Mac.

2. Download the zip file of this repository (_Code → Download ZIP_ on [github.com/11moo11/AliceLG](https://github.com/11moo11/AliceLG)). The releases of the original add-on at [github.com/regcs/AliceLG](https://github.com/regcs/AliceLG/releases/) do not contain the changes of this fork.

3. Install _Alice/LG_ in Blender:
   - Open Blender
   - In the main menu, navigate to _Edit → Preferences → Add-ons → Install → Install Add-on_
   - Select the downloaded zip file and click "Install"
   - Enable the add-on by activating the check box on the left
   - Expand the preferences of the add-on by clicking on the small arrow next to the checkbox
   - Click the "Install" button to install required Python modules to the add-on directory
   - Restart Blender

### Updating

Once the add-on is installed, you can update it from Blender:

- Open _Edit → Preferences → Add-ons_ and expand the preferences of _Alice/LG_
- The add-on checks GitHub for a newer version when Blender starts (this can be switched off with _Check for updates on startup_). You can also click _Check for Updates_ at any time.
- If an update is available, click _Install Update_. Only the files that changed since your installed version are downloaded. The same applies to the Python files of the Looking Glass Bridge communication (pyLightIO) in the add-on's `lib` folder. Large binary dependencies are never touched.
- When the update is installed, a red _Restart Blender_ button appears. Restart Blender to activate the update. (Right after an update, the button can also show as plain red text. Restart Blender manually then.)

You can still update by installing the zip file of a new version as described above.

## How to Use

The following provides some basic information which is going to help you to get started. But make sure, you also check out the [Getting Started Guide](https://docs.lookingglassfactory.com/artist-tools/blender) as well as the [very helpful tutorial](https://lookingglassfactory.com/tutorial/blender) on the Looking Glass Factory website!

### Add-on Controls

After the installation you find a _Looking Glass_ tab in each Blender 3D viewport. It contains two panels:

- **View Settings.** From top to bottom:

   - **Camera settings.** Select the camera that defines the view for the Looking Glass (or create a new one with the "+" button), show or hide the view frustum and focal plane, synchronize the camera, and set the clipping planes and focal plane.

   - **Activate Swivel.** Move the camera to a single view of the quilt to check it: the _View Image_ slider is limited to the number of views of the selected quilt (e.g., 48 views for Portrait), and _Activate Swivel_ toggles the preview position. The preview is reset when a file is loaded.

   - **Cast to Looking Glass.** The large button that starts and stops casting your scene to the Looking Glass. Below it you select the connected Looking Glass display (with a refresh button for the display list).

   - **Select Cast Source.** Appears while casting. Choose between _Scene_ (a live view of your Blender scene) and _Quilt Viewer_ (a pre-rendered quilt image).

   - **Cast Settings.** The settings of the live scene view (see below).

- **Quilt Creation.** Switch _Build From_ between _Render_ and _Files_. _Render_: choose the device, quilt resolution and output, then pick what the _Render_ button does under _Source_ (_Render Quilt_, _Render Animation Quilt_, or one of the two _Headlessly_ variants). _Files_: assemble a quilt from existing view images. _Add Metadata_ at the bottom applies to both. Next to it, _Shut off Computer after Render_ shuts the computer down 60 seconds after a quilt render has completed (not after a cancelled or failed one), e.g., for overnight renders; it also works for headless renders. Programs with unsaved changes are closed without asking. On Windows a countdown window is shown, and nothing has to be pressed: the computer shuts down when the countdown ends, unless a key is pressed in that window. On Linux the shutdown can be aborted with `shutdown -c`.

### Cast to Looking Glass

The light field / hologram is displayed on your Looking Glass display via the Looking Glass Bridge (or HoloPlay Service) app. Click _Cast to Looking Glass_ in the _View Settings_ panel if you have a Looking Glass connected and Looking Glass Bridge (or HoloPlay Service) is running. The cast source can be:

- **Scene.** The live view of your scene, which acts like a normal Blender viewport in the Looking Glass - except that it is holographic.

- **Quilt Viewer.** Load or select a rendered quilt image and display it as a hologram. Playing animations is not supported yet. If the image is unlinked, the Looking Glass shows a black screen. _NOTE: To display the quilt correctly, the correct quilt preset must be used._ Switching back to _Scene_ redraws your scene.

#### Cast Settings (Scene)

- **Refresh Mode.**
   - _Automatic_ (default): The hologram is updated when something visible changes: object transforms and geometry, hiding or showing objects, and viewport shading & overlay settings (e.g., _Show Overlays_, shading mode, X-ray). Changes that do not show up in the hologram (such as changes to the add-on's own panel settings or window / workspace changes) do not trigger a redraw.
   - _Manual_: The hologram is only rendered if you click the refresh button.

- **Patient Mode** (button next to the refresh mode, Automatic mode only). Off by default: the hologram updates while you are still moving or editing something. With _Patient Mode_ on, the update waits until your current operation has finished (e.g., you released the mouse after moving an object). This can help in heavy scenes. Animation playback always updates live.

- **Full-quality refresh** (Automatic mode only). While you edit, a fast preview is shown. After this many seconds without changes (default: 0.7 s), the full-quality hologram is rendered and sent. Full-quality refreshes are also limited to one every 2 seconds.

- **Preview Quality.** How the preview during changes is rendered:
   - _Minimum_ (default): a very small 512×512 quilt. Sends the least data to Looking Glass Bridge.
   - _Lowest_: a 1024×1024 quilt.
   - _Low_: only one of six views is rendered.
   - _Medium_: one of three views.
   - _Best_: one of two views.

- **Shading & overlays.** Choose _Viewport_ to mirror the shading and overlay settings of a Blender 3D viewport (select the workspace and 3D view and click _Assign Active Viewport_), or _Custom_ to define your own settings for the hologram.
   - Material Preview and Rendered shading cannot be cast when the render engine is Cycles or Eevee (it can crash Blender). In _Custom_, the Material Preview option is not offered for these engines. In _Viewport_, casting is turned off automatically if the mirrored 3D view uses Material Preview or Rendered shading with one of these engines; switch that view to Solid or Wireframe.

#### Default Cast Settings

In _Edit → Preferences → Add-ons → Alice/LG_ you find _Default Cast Settings (for all Blender files)_: Refresh Mode, Preview Quality, Full-quality refresh, Patient Mode and Quilt (the default quilt resolution, Looking Glass Portrait with 48 views unless changed; _Match connected Looking Glass_ uses the default quilt of the connected display). These values are applied whenever a Blender file is loaded, so they hold for all your files. Changes you make in the _Cast Settings_ panel apply until the next file is loaded.

#### Notes on performance and Looking Glass Bridge memory

- Rendering the views is done by Blender's 3D viewport renderer, so heavy scenes need time. The preview quality levels trade quality for speed.
- Looking Glass Bridge may use more and more memory when it receives many large images. Blender's own memory use stays flat. Using _Preview Quality: Minimum_, a longer _Full-quality refresh_ time, or restarting Looking Glass Bridge from its tray icon during long sessions helps.
- _Experimental:_ The add-on preference _Experimental: update Looking Glass Bridge via its quilt cache_ sends the hologram as one named, replaced quilt in the cache of Looking Glass Bridge. In testing on one setup it did not stop Bridge's memory growth. It is off by default.
- For troubleshooting, set the _Logging Mode_ in the add-on preferences to _Debug messages_. The log then shows what triggered each update, how long rendering and sending took, and the memory used by Blender.

### Camera Setup & Quilt Creation

You can render still scenes and animation frames as complete quilt images. You can render for your currently connected device or for any other Looking Glass:

**(1) Rendering for your currently connected device**
- select your connected Looking Glass (if not already selected) under _Looking Glass → View Settings_ and a quilt resolution under _Looking Glass → Quilt Creation → Quilt_
- select an existing camera in _Looking Glass → View Settings → Camera_ or create a new camera by clicking "+" in the same section
- locate the camera to the specific view you would like to render
- adjust the render and post-processing settings in the usual Blender panels (_NOTE: Image dimensions are overwritten by the add-on based on your connected Looking Glass or your manual settings under _Looking Glass → Quilt Creation__)
- click on _Looking Glass → Quilt Creation_, choose _Render Quilt_ or _Render Animation Quilt_ under _Source_ and click _Render_ in the add-on controls.

**(2) Rendering for other Looking Glasses**
- select an existing camera in _Looking Glass → View Settings → Camera_ or create a new camera by clicking "+" in the same section
- the _Device_ and _Quilt_ lists are active when no Looking Glass is connected (with a connected Looking Glass, its settings are used)
- choose the Looking Glass you want to render for from the list _Looking Glass → Quilt Creation → Device_
- choose the quilt preset/resolution you want to render for from the list _Looking Glass → Quilt Creation → Quilt
- locate the camera to the specific view you would like to render
- adjust the render and post-processing settings in the usual Blender panels (_NOTE: Image dimensions are overwritten by the add-on based on your connected Looking Glass or your manual settings under _Looking Glass → Quilt Creation__)
- click on _Looking Glass → Quilt Creation_, choose _Render Quilt_ (or, for animation frames, _Render Animation Quilt_) under _Source_ and click _Render_ in the add-on controls.

You can also assemble a quilt from existing view images with _Looking Glass → Quilt Creation → Build From: Files_.

**Render Headlessly** (_Looking Glass → Quilt Creation →_ _Source_ set to one of the _Headlessly_ options, then _Render_) saves the Blender file, closes Blender, and renders the quilt (or the frame range as a quilt animation) in a separate Blender process without a user interface, using the settings stored in the file, including its output path. On Windows the progress is shown in a console window; when the render is done, Enter opens the scene in Blender and ESC closes the window. on other systems it is written to `logs/headless-render.log` in the add-on folder. It uses the _Camera Mode_ of the add-on preferences. In _Single Camera Mode_ (the default) the views are rendered one by one and the console shows a line per view with the elapsed time and an estimate of the remaining time; in _Multiview Camera Mode_ all views are rendered in one step without progress per view. The file has to be saved once before, and Blender is closed by this button. It uses the command line mechanism described under _Renderfarm Implementation_.

The _Render Quilt_ option will render the different views separately. After the last view has been rendered, a quilt will be automatically assembled. For the _Render Animation Quilt_ option, the same will happen for each frame of the animation, which will result in one quilt per frame. After rendering, the created quilt image or animation frames have to be handled in the same way as normal renders. You can still render normal (non-holographic) images in Blender as you usually do.

_NOTE: Option (2) can be used even if no Looking Glass is connected._

### Incomplete Render Jobs (Experimental)

The add-on attempts to detect Blender crashes during quilt rendering as well as quilt animation rendering and prompts you with an option to continue or to discard an incomplete render job the next time you open the crashed file. The successful detection of an incomplete render job and its continuation requires that:

- the filename of the .blend-file did not change
- the file was saved before starting the render job **OR** no significant changes happened to the setup (e.g., camera position, render settings, etc.)
- the (temporary) view files of the incomplete render job are still on disk and not corrupted

While the add-on tries to check some basic settings, the user is highly recommended to check if the current render settings fit to the settings used for the incomplete render job before clicking the "Continue" button.

If you decide to discard the incomplete render jobs, the add-on will try to delete the view files of the incomplete render job.

_NOTE: This feature is considered to be 'experimental'. It might not detect crashes under all circumstances and might not succeed to continue the rendering always. If you encounter a situation were this feature failed, please submit a detailed bug report._

## Renderfarm Implementation (Experimental)

The rendering of still holograms and holographic animations can be a time-consuming task. Therefore, this add-on provides a command line mechanism that was created for render farms which want to support the quilt rendering by Alice/LG on their systems. Since it has not been tested on a render farm environment yet, this feature is considered experimental. If you are working at a render farm and need help to implement this mechanism on your system, please [open an issue on the add-on's GitHub repository](https://github.com/regcs/AliceLG/issues).

### Basic Command Line Calls

As a first prerequisite, Alice/LG needs to be installed and activated on the render farm's Blender installation. If you setting up your own local render farm and need to install the dependencies of the add-on, use the following command:

- `--alicelg-install`: Install the python dependencies of the add-on.

To initiate a quilt rendering from the command line, there are two main calls which are understood by Alice/LG:

- `--alicelg-render`: Start the rendering of a single quilt.
- `--alicelg-render-anim`: Start the rendering of a quilt animation.

Both arguments require that Blender is started in background mode (i.e., using the '-b' command line argument) and with a .blend-file specified, which contains all the necessary render settings. Furthermore, both arguments must be preceded by a `--`. An example, which opens the file 'my_lg_hologram.blend' and starts rendering a single quilt looks like that:

`blender -b my_lg_hologram.blend -- --alicelg-render`

### Additional Parameters

The add-on also understands some additional parameters to fine-tune the rendering process. These parameters are very similar to Blender's internal command line rendering parameters:

- `-o`  or `--render-output` `<path>`: Set the render path and file name. Automatically disables the "Add Metadata" option.
- `-s`  or `--frame-start` `<frame>`: Set start to frame `<frame>`, supports +/- for relative frames too.
- `-e`  or `--frame-end` `<frame>`: Set end to frame `<frame>`, supports +/- for relative frames too.
- `-j`  or `--frame-jump` `<frame>`: Set number of frames to step forward after each rendered frame
- `-f`  or `--render-frame`: Specify a single frame to render

**It is important that these arguments are specified after the mandatory `--`** to notify Blender that the arguments are meant for the add-on. An example call which would start Blender in background mode, load the 'my_lg_hologram.blend' file, and render a quilt animation from frame 10 to 24 with the base file name `quilt_anim` would look like this:

`blender -b my_lg_hologram.blend -- --alicelg-render-anim -o /tmp/quilt_anim.png -s 10 -e 24`

Another example, which would only render the frame 16 as a single quilt, would like this:

`blender -b my_lg_hologram.blend -- --alicelg-render -o /tmp/quilt.png -f 16`

## License & Dependencies

The Blender add-on part of this project is licensed under the [GNU GPL v3 License](LICENSE).

This Blender add-on partially relies on the following GPL-compatible open-source libraries / modules and their dependencies:

- pyLightIO licensed under Apache Software License 2.0
