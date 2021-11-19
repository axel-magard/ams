# AMS - Analytical Modeling System
AMS is a tool to model manufacturing lines and to compute key performance indicators (KPIs) of a manufacturing line like 

* Maximum Throughput
* Utilization
* Leadtime
* Work In Process (WIP)
* Efficieny
* Yield

based on a model consisting of

 * Workcenter - physical resources like e.g. machines, where work is performed
 * Product Types - Types of parts manufactured
 * Operations - process steps needed to manufacture parts
 * and a Process Flow describing how parts flow from operation to operation 
 
 using some math based on formulas from [Queueing Theory](https://en.wikipedia.org/wiki/Queueing_theory) rather than [Discrete Event Simulation](https://en.wikipedia.org/wiki/Discrete-event_simulation)
 
 ## History
 AMS has been developed @ IBM more than 30 years ago. A first version was written in APL running on mainframe computers, later on we developed a version for OS/2 Presentation Manager 
 written in C. We used AMS to plan and improve some of our own manufacturing lines, like our assembly line for storage sub systems or our semi-conductor lines to produce magnetic heads for disk drives. Those manufacturing lines consisted of some hundred operations and ~100 product types and it turned out that using AMS instead of discrete event simulators allowed us to do computations within minutes rather than hours or days.
 
 OS/2 went away and thus AMS went away, but I kept the source code all the time and now after retiring from IBM I decided to re-implement AMS in Python, using the wxPython library for the Graphical User Frontend.
 
 The math behind AMS has been developed by [Prof. Dr. Thomas Hanschke](https://www.mathematik.tu-clausthal.de/personen/thomas-hanschke/)
 
  ## Documentation
  is [here](https://htmlpreview.github.io/?https://raw.githubusercontent.com/axel-magard/ams/main/html/ams.html) 
  
  An introdcution video is available [here](https://www.youtube.com/watch?v=Nd4KpAgHseQ) on youtube.
  
  ## Installation
  
  ### Alternative 1
  
  1. Install Python3 ( Windows users can get it from the Microsoft Store )
  2. Install git ( Windows users can get it from [here](https://git-scm.com/download/win) )
  3. Clone this repo ( `git clone https://github.com/axel-magard/ams.git` )
  4. Install missing Python packages ( `pip install -r requirements.txt` )
  5. Run AMS ( `ams.cmd` for Windows user or `python -W ignore ams.py` for Linux user  )

  ### Alternative 2
  
  1. Install Python3 ( Windows users can get it from the Microsoft Store )
  2. Download this repo as zip file into a directory of your choice and unpack it there
  4. Install missing Python packages ( `pip install -r requirements.txt` )
  5. Run AMS ( `ams.cmd` for Windows user or `python -W ignore ams.py` for Linux user )

  ### Alternative 3 for Windows user only
  
  This alternative is for those who do not want to install Python or any Python package on their system.
  
  1. Download a binary version from [here](https://u.pcloud.link/publink/show?code=kZx1UUXZhBmaczXdFrJGsP8CB2kYJysRiYL7); right-click on file ams_inst.exe and select "Download"
  2. Run ams_inst.exe in a directory of your choice. Note that Windows first will refuse to run it since it is from an unknown publisher. ( Hey folks, it is just me ! ). Display details and continue from there to run it.
  3. Run `ams.exe` to start AMS

  ### Alternative 4 for Linux user
  Since installing wxPython tends to fail on many linux distributions using [conda](https://docs.conda.io/en/latest/) might help.
  
  1. Install conda
  2. Create conda environment:
  ```
  conda create -n python3.8 python=3.8
  conda activate python38
  ```
  3. Install git
  4. Clone this repo ( `git clone https://github.com/axel-magard/ams.git` )
  4. Install missing Python packages within conda environment ( `pip install -r requirements.txt` )
  5. Run AMS ( `python -W ignore ams.py` )
  
