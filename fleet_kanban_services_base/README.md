# Odoo 13.0

Installation 
============
* Install the Application => Apps -> Fleet Kanban Services (Technical Name: fleet_kanban_services_base)


Fleet Kanban Services
=============================
* This module will managing Vehicle, its Availability, Status, Discrepancy, Service Request and Fleet Repair Order. 


Configuration
===================
1). Vehicle
-----------------------
- Vehicle Status
- Vehicle Tags
- Vehicle Stage
- Partial Serialization
- Vehicle Availability

2). Discrepancy
-------------------
- Discrepancy State
- Discrepancy Type
- Observed During
- HW Failure Version

3). Service Request
-------------------
- Service Stages
- Service Tags
- Service Types

4). Repair Order
-----------------
- Repair Stages
- Repair Types
- Repair Tags

Steps
=====
1). Create a Vehicle with respected partial serialized product and then Scan that Vehicle barcode in "Scan Discrepancy" kanban screen.

2). After entering the details of vehicle then click on confirm button, so that in backend its Discrepancy and Services Request are created. We can also create repair order from there.

3). We can also create Services Request manually and assigned this services request to any existing repair order whose vehicle will be same.

