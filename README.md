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
 witten in C. OS/2 went away and thus AMS went away, but I kept the source code all the time and now after retiring from IBM I decided to re-implement AMS in Python, using the wxPython library for the Graphical User Frontend.
