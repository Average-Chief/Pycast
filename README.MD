# PyCast

<p align="center">
<img src="pycast_logo.png" alt="PyCast Logo" width="180">
</p>
<p align="center">
A keyboard-driven launcher for Windows built with Python.
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue">
  <img src="https://img.shields.io/badge/Platform-Windows-blue">
  <img src="https://img.shields.io/badge/License-MIT-green">
  <img src="https://img.shields.io/badge/Keyboard-Driven-success">
  <img src="https://img.shields.io/badge/Search-Fuzzy-important">
  <img src="https://img.shields.io/badge/Status-Active%20Development-orange">
</p>


## What is PyCast?

**PyCast** is a lightweight keyboard launcher that lets you open apps, run workflows, manage files, and search the web without leaving your keyboard.

Instead of navigating the Start Menu or clicking around your desktop, you can simply press a shortcut, type what you want, and launch it instantly.

Example workflow:

1. Press `Ctrl + Alt + Space`
2. Start typing the name of an app
3. Press `Enter`
4. The app launches immediately

PyCast is inspired by tools like **Raycast**, **Spotlight**, and **Alfred**, but designed specifically for Windows and built entirely in Python as a personal project.

The main goal of PyCast is to make everyday actions faster and remove the need to switch between keyboard and mouse.



## Main Idea

The philosophy behind PyCast is simple:

> Everything you need should be reachable from the keyboard.

PyCast tries to centralize common tasks into one small launcher:

* Opening applications
* Launching groups of apps
* Searching the web
* Managing files and folders
* Running workflows

All of these actions can be performed from a single search bar.



## How the Launcher Works

The launcher is opened using a global hotkey:

```
Ctrl + Alt + Space
```

When the launcher appears, you can start typing immediately.

PyCast searches your installed applications in real time and shows matching results instantly.

Navigation is entirely keyboard based:

| Key       | Action                |
| --------- | --------------------- |
| `↑` / `↓` | Navigate results      |
| `Enter`   | Launch selected item  |
| `Tab`     | Trigger Google search |
| `Escape`  | Close launcher        |

The launcher shows a maximum of **7 results at a time** to keep the interface simple and focused.



# App Search

The core feature of PyCast is its **real-time app search system**.

As you type, PyCast searches across multiple sources:

* Windows Start Menu applications
* Microsoft Store applications
* Custom commands defined in the configuration file

This allows the launcher to find almost every application installed on the system.



## How App Discovery Works

PyCast scans several locations to build its internal list of launchable applications.

### Start Menu Applications

Traditional Windows applications are discovered by scanning `.lnk` shortcut files inside the Start Menu directories.

The launcher checks:

```
C:\ProgramData\Microsoft\Windows\Start Menu\Programs
%APPDATA%\Microsoft\Windows\Start Menu\Programs
```

Most installed desktop applications place shortcuts in these directories.

These shortcuts point to the actual executable files of the applications.



### Microsoft Store Applications

Microsoft Store applications are detected using the PowerShell command:

```
Get-StartApps
```

This allows PyCast to discover UWP applications such as:

* Calculator
* Photos
* Microsoft Store apps
* Other packaged Windows applications

These apps are stored differently than traditional executables, so they require a different discovery method.



### Manual Commands

Users can also define their own commands in the configuration file.

Example:

```python
MANUAL_COMMANDS = {
    "notepad": "notepad",
    "youtube": "start https://youtube.com",
}
```

Manual commands always take priority over scanned applications.

This allows users to create custom shortcuts or override default behavior.



# Fuzzy Matching

PyCast does not require exact typing.

Instead it uses **fuzzy matching** to rank results based on how closely they match your query.

Results are sorted by the following priority:

1. **Exact match**

```
chrome
```

2. **Name starts with query**

```
chr → chrome
```

3. **Query appears anywhere inside the name**

```
rome → chrome
```

4. **Subsequence match**

Characters appear in the same order.

```
crm → chrome
```

This allows users to type only a few characters to find an application.



# App Icons

Every search result shows an icon next to the application name.

PyCast attempts to extract icons using multiple methods.



## Traditional Desktop Applications

For regular applications, PyCast extracts the icon directly from the executable file.

This is done using Windows API calls that read the embedded icon resources inside `.exe` files.

Examples:

* Chrome
* Visual Studio Code
* Spotify
* Notepad



## Microsoft Store Applications

Store applications do not store icons in the same way as traditional programs.

Instead, PyCast reads the application's `AppxManifest.xml` file and finds the icon declared in the manifest.

The launcher then searches for the best available icon variant.

Windows often generates multiple versions of each icon:

```
scale-200
scale-150
scale-100
targetsize-32
```

PyCast attempts to load them in that order to obtain the highest quality image.



## Fallback Icons

Some applications do not expose their icons properly.

In these cases PyCast shows a fallback icon:

* a dark square
* the first letter of the application name

This ensures that every result still has a visible icon.



## Icon Performance

Icons are preloaded asynchronously using a background thread.

This prevents the user interface from freezing while icons are being extracted.

The launcher can therefore remain responsive even when many icons need to be loaded.



# Web Search

If no installed application matches the text you typed, PyCast automatically offers a web search option.

The launcher displays a result like:

```
Search Google for "<your query>"
```

Pressing **Tab** or selecting the row opens the search in your default web browser.

Example:

Typing:

```
python list comprehension
```

will open Google search results for that query.

This allows PyCast to function both as an app launcher and a quick search tool.



# Flows (`>`)

Flows allow you to launch **multiple apps and URLs at once**.

They are essentially small automation scripts that run several steps in sequence.



## Using Flows

To enter flow mode, type:

```
>
```

This switches the launcher into flow search mode.

You can then type the name of a flow or one of its aliases.

Example:

```
>dev
```

This could launch your development environment.

Use arrow keys to select a flow and press **Enter** to execute it.



## Creating Flows

Flows are stored inside a file called:

```
flows.json
```

Users can edit this file to create custom workflows.

Example flow configuration:

```json
[
  {
    "name": "Run Dev",
    "description": "Opens Chrome, VS Code and Spotify",
    "aliases": ["dev", "code", "work"],
    "steps": [
      { "type": "app", "value": "chrome" },
      { "type": "app", "value": "visual studio code" },
      { "type": "url", "value": "https://spotify.com" }
    ]
  }
]
```



## Flow Step Types

Each flow contains multiple steps.

Two types of steps are currently supported.

### App

Launches an installed application.

```json
{ "type": "app", "value": "chrome" }
```

The same fuzzy matching logic used in normal search is applied here.



### URL

Opens a website in the default browser.

```json
{ "type": "url", "value": "https://spotify.com" }
```

If the protocol is missing, PyCast automatically adds `https://`.



## Flow Execution

Flow steps run sequentially with a small delay between each action.

This delay prevents applications from starting simultaneously and interfering with each other.

Flows run in a background thread so the launcher remains responsive.



# File Commands (`?`)

PyCast also allows users to manipulate files and folders directly from the launcher.

Typing:

```
?
```

shows the available file commands.



## Create Folder

```
?newfolder:<path>
?new:<path>
?mkdir:<path>
```

Example:

```
?mkdir:C:\Projects\Test
```

Creates the specified directory.

Environment variables such as `%APPDATA%` are automatically expanded.



## Delete

```
?delete:<path>
?del:<path>
?rm:<path>
```

Deletes files or directories.

Directories are removed recursively.



## Rename / Move

```
?rename:<path>|<new name>
?ren:<path>|<new name>
?mv:<path>|<new name>
```

Example:

```
?rename:C:\notes\todo.txt|todo_old.txt
```

If the new value contains a full path, the file will be moved instead of renamed.



## Live Preview

While typing file commands, PyCast shows a **live preview** of the operation.

When executed, the result is displayed briefly with color feedback indicating success or failure.



## Explorer Refresh

After file operations, Windows Explorer is refreshed automatically using the Windows API.

This means changes appear instantly without needing to press `F5`.



# Configuration

All configuration options are stored in `config.py`.



## Hotkey

```python
HOTKEY = "ctrl+alt+space"
```

Defines the global shortcut used to open the launcher.



## Manual Commands

```python
MANUAL_COMMANDS = {
    "notepad": "notepad",
    "youtube": "start https://youtube.com",
}
```

Manual commands override automatically detected apps.



## Scan Directories

```python
SCAN_DIRS = [
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs",
]
```

These directories are scanned to discover installed applications.



## Layout Settings

```python
WIDTH    = 640
MAX_ROWS = 7
ROW_H    = 48
```

These settings control the size and layout of the launcher interface.


# Project Goal

PyCast started as a personal project to explore building a productivity tool with Python.

The goal was to create a simple launcher that could replace several everyday tasks and keep everything accessible from the keyboard.

Even though it started as a learning project, the aim is to keep improving it and gradually add more capabilities while keeping the interface minimal and fast.


# License

MIT License
