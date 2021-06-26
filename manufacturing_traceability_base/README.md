# Odoo 13.0

Installation 
============
* Install the Application => Apps -> As-Built for Manufacturing (Technical Name: manufacturing_traceability_base)


As-Maintained Traceability
=============================
* This module is dependent on Partial Serialization in which we can manage Product tracking as  Partially Serialized.
* In odoo standard Manufacturing Order, it allows user to add Lot/Serial only when Product Tracking is either by Lot or Serial. We have added additional conditions so that If Product is Partially Serialized then also system will ask for Lot/Serial.
