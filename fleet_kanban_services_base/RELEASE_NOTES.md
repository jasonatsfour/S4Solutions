## Module fleet_kanban_services_base

## 12/23/2020 Initial Version
### Version 13.0.1.0.0
#### Initial Version
- [ADD] Added module: fleet_kanban_services_base
- Set models and code optimization for models

## 12/24/2020 Base Setup
### Version 13.0.1.0.0
#### Manage Folder Structure
- Set models and code optimization for models
- Set views with individual files
- Reset manifest data file sequences
- Rename File: stock.py -> stock_warehouse.py

## 12/28/2020 Initial Version
### Version 13.0.1.0.0
#### Repair Lines for Fleet
- Managed code for fleet repair type and also manage move line updates
- Fixed issues for x_location fields

## 12/30/2020 Code Cleanup
### Version 13.0.1.0.0
#### Remove dead code
- Managed code quality and fixed some missing code and invalid code

## 01/01/2021 Bug Fixing
### Version 13.0.1.0.0
#### SO/RO/Service Template
- Create RO & Add SO : Fixed part creation issues on RO from SO
- Reset SO Location field visibility to set Part on Services from Service Templates
- On change function to set up the part locations from repair location

## 01/02/2021
### Version 13.0.1.0.0
#### Bug fixing & Enhancements
- Changed action name Service State -> Service Stages
- Remove limit to fetch all the RO on SO smart button

## 01/05/2021
### Version 13.0.1.0.0
#### Code cleanup & Enhancements
- Setup Doc strings.
- Removed unnecessary local variables.
- Repair Order + Repair Order Lines (Operations/Parts):
  - Rename method cal_fleet_in_use => _compute_fleet_in_use.
- Added few attributes in fleet repair form.

## 01/06/2021
### Version 13.0.1.0.0
#### Bug Fix
- Fixed not to add the Serial/lot into Installed Locations itself.

## 01/07/2021
### Version 13.0.1.0.0
#### Enhancements
- Added related fields from Stage to RO/SR.
- Added the domain to the fields to restrict to make changes after RO/SR reached to done stage.

## 01/08/2021
### Version 13.0.1.0.0
#### Enhancements & Bug Fixing
- Manage name attributes where needed.
- Fixed unnecessary variables.
- Manage naming convention issues for object -> self.

## 01/12/2021
### Version 13.0.1.0.0
#### Code cleanup
- Added the doc string and remove unnecessary local variables.

## 01/13/2021
### Version 13.0.1.0.0
#### Bug fixing
- Remove readonly attribute from Discrepancy Image field.

## 01/18/2021
### Version 13.0.1.0.0
#### Bug fixing
- Discrepancy: Update Availability on Discrepancy vehicle.
- RO: changes for context on Lot/Serial for new parts.

## 01/25/2021
### Version 13.0.1.0.0
#### Enhancements
- Reset domain.

## 01/28/2021
### Version 13.0.1.0.0
#### bug fixing Enhancements
- Vehicle's information on service request by calling onchange from recurring service.
- Fix repair order count on service request.
- Manage image name sequence while deleting images from discrepancy screen.

## 01/29/2021
### Version 13.0.1.0.0
#### search view added for several models
- fleet.repair.
- fleet.service.type.
- recurring.service.plan.
- service.request.template.
- vehicle.discrepancy.
- vehicle.flight.log.
- vehicle.services.

## 01/29/2021
### Version 13.0.1.0.0
#### Code Cleanup & Enhancements
- Code cleanup and enhancements.

## 02/02/2021
### Version 13.0.1.0.0
#### Code Cleanup & Enhancements
- Reduce code complexity for recurring service plan (cron).
- Rename Cron: 'Service: Generate services' => 'Generate Recurring Services for Fleet'
- Added two booleans to recurring service plan named as Display 1 and Display 2.
- Added constrain on Booleans: "Another Recurring Service Plan has already been marked as 'Display 1.' You must first un-assign that plan's 'Display 1' field prior to assigning this plan as the 'Display 1' plan."
- Prevent the user from saving the record on error.

## 02/03/2021
### Version 13.0.1.0.0
#### Code Cleanup & Enhancements
- Reduce code complexity for recurring service plan (cron).
- Added model to log Recurring Plan Vehicle History.
- Code cleanup for vehicles.
- Added Assigned Recurring Services to vehicle master.
- Creating Service history if service created from recurring plan.

## 02/04/2021
### Version 13.0.1.0.0
#### Code Cleanup & Enhancements
- Added MOC Field in: Fleet Vehicle Available, Repair Stage & Repair Type Objects.
- Setup MOC computation on RO on change of stage.
- Added 'Last Generated At Hours' to vehicle to note the previous service hours of that vehicle from Recurring Services.
- Added Color field in Fleet Vehicle Available Object.
- Added O2M in child_plan_ids to map sub recurring plans to reduce search calls on execution of cron.
- Fixed order of recurring history to get latest data on top and make filtered more easy.
- Code cleanup for th extra loop(s)/condition(s)/search.
  
## 02/05/2021
### Version 13.0.1.0.0
#### Code Cleanup & Enhancements
- Trello-146: Update Apply on Multiple SR function:
  - setup for mutli SR + multi vehicle.
  - code cleanup.
- Trello-123: Replace Included Service "Completed By" field:
  - added fields to Fleet Vehicle Cost and Included Services.
- Trello-130: Add archive ability to HW Failure Mode.
- Trello-96: Kanban card color updates not functioning for certain vehicles.
- Resolved -The domain term '('repair_id', '=', [])' should use the 'in' or 'not in' operator.
  
## 02/08/2021
### Version 13.0.1.0.0
#### Code Cleanup & Enhancements
- Setup for the parent recurring service on execution of cron.

## 02/09/2021
### Version 13.0.1.0.0
#### Big Fixing, Code Cleanup & Enhancements
- Fixed Typo Errors.
- Added @api.model to recurring create method.
  
## 02/10/2021
### Version 13.0.1.0.0
#### Big Fixing, Code Cleanup & Enhancements
- Fixed for the parent recurring service with exist service.

## 02/12/2021
### Version 13.0.1.0.0
#### Big Fixing, Code Cleanup & Enhancements
- Fixed for the parent recurring service with exist service.
