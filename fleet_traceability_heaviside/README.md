# Odoo 13.0

Installation 
============
* Install the Application => Apps -> As-Maintained Traceability (Technical Name: fleet_traceability)


As-Maintained Traceability
=============================
* This module will support creation and maintenance of As-Maintained structures of installed components for serialized products. 


Configuration
===================
1). First we need to give access right to the user for managing the As-Maintained Structure. For that you need to mark "Edit As-Maintained Structure" boolean as true under the Technical Settings section of the User configuration in the Settings app.

2). Then we need to set the default source and destination location for "adds" & "removes". This four location will be added to custom repair order creation by their respective operation i.e "add" & "remove"

3). Need to create partial serialization for product and mark as "Use in Fleet" as true in fleet app under the configuration menu titled Partial Serialization

4). Then we need to add the repair type for As-Maintained by marking "Is As-Maintained" boolean as true in the Fleet app under the Configuration Menu title Repair Types. This will be set the custom repair order type as As-Maintained, if we creating repair order from as-maintained stucture.


Steps
=====

1). Adding Lot Serial Number from As-Maintained Structure
------------------------------------------------------------
First we will create one lot serial number with respected stockable product
(Note:- If the product have no tracking, then we need to add its partial serialization under Inventory tab which we have configured above.)

Then go to the "As-Maintained Traceability" Report, where we now adding the traceable lot by clicking on "add" button in as_maintained structure. By adding this, the custom repair order of add child_lot in "Parts" will be created in backend in completed stage.

By adding traceable lot number, the versioning of parent_lot will be extend by one, also added the Lot history Line in "As-Maintained Lot History" tab and this parent_lot will be added as "Installed Location" in child lot.


2). Removing the Lot Serial number from As-Maintained Structure
-----------------------------------------------------------------
For removing the lot, we need to click on "remove" button in as_maintained structure then that lot will be removed and custom repair order of remove child_lot in "Parts" is created automatically in backend. 

Also the parent_lot will be removed from installed location of that removing lot.The version of the parent_lot will be updated and also add the lot history line in it.


3). Editing the Lot Serial Number from As-Maintained Structure
-----------------------------------------------------------------
On editing the lot serial number, we just need to click on "edit" button in as_maintained structure then the old child_lot will be removed and new lot which the user will be selected will be added as installed location. 

So therefore in custom repair order, the two entries will be created in "Parts" the first one for removing the old child lot and the second will be the adding of the new child lot. The versioning is will also updated and log entries will be added in parent_lot too.


4). Adding/Removing/Editing the Non-Traceable lot From As-Maintained Structure.
----------------------------------------------------------------------------------
First we need to create non-traceable lot from Inventory app under Master data menu titled Non-Traceable Entries.


The follow would be the same but there will be no repair order will be created by adding/removing/editing the Non-Traceable lot and also the versioning will not update. Just the non-traceable lot will be added as installed location under parent_lot in as_maintained stucture.


5). By Manually Creating Custom Repair Order
----------------------------------------------
We will also create the custom repair order with respection "add" and "remove" operation under Parts tab. By making mark_done/Mark_all_done the operation and then move the repair order stage to final stage. Then this operation will reflect to the As-Maintained Structure.



