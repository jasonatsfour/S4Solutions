# Module fleet_traceability_base

## 12/28/2020 Initial Version
### Version 13.0.1.0.0
#### Initial Version
- [ADD] Fleet Traceability: Added th module after code cleanup

## 12/28/2020
### Version 13.0.1.0.0
#### Code cleanup
- Remove extra redefined fields.

## 12/29/2020 Code cleanup
### Version 13.0.1.0.0
#### Rename Files
- Rename: stock_move.py -> stock_production_lot.py
- Rename: stock_move_view.xml -> stock_production_lot_views.xml
- Code cleanup and remove dead code

## 12/30/2020
### Version 13.0.1.0.0
#### Code cleanup
- Code cleanup and remove dead code

## 01/04/2021
### Version 13.0.1.0.0
#### Code cleanup & Enhancements for As-Maintained
- Reduce search process in check_lot_status function.
- Reduce code from JS file by setting up the methods in JS.
- Reduce code in Controller methods.
- Repair order has going to be created from As-Maintained screen it must have root product Serial/Lot.
- Added fields in:
  - Serial/Lot Number: sub_part_history_ids | To manage origin traceability of sub part to root part.
  - As-Maintain History & Repair Line: origin_part_of_id | To trace origin component.

## 01/05/2021
### Version 13.0.1.0.0
#### Code cleanup & Enhancements for As-Maintained
- Setup Doc strings.
- Removed unnecessary local variables.
- Update Serial/Lot version while adding child of child.
- Repair Order + Repair Order Lines (Operations/Parts):
  - Set serial of vehicle on change of vehicle.
  - Added Method _onchange_product_lot to fetch vehicle with Product and lot.
  - Rename method cal_fleet_in_use => _compute_fleet_in_use.
- Manage views XPATH and Context for fleet repair form.
- Added method _get_root_vehicle_location to get root Serial/Lot & Location with Installed Vehicle.

## 01/06/2021
### Version 13.0.1.0.0
#### Bug fixing, Code cleanup & Enhancements for As-Maintained
- Setup Doc strings.
- Removed unnecessary local variables.
- Create RO only if there is no RO or not in final stage for As-Maintained Screen.
- Updated context for Replacement lot on operations.
- Removed print and console.
- Search with the product to resolve maximum recursive issues.
- As-Maintained History:
  - Hide Installed Location and visible Origin Lot on Parent History.
  - Hide Origin Location and visible Parent 0n Sub Serial/Lot History.
- Added Origin Lot on Part of Repair.
- Move RO stage to done for that is created during at As-Maintained Screen.

## 01/07/2021
### Version 13.0.1.0.0
#### Bug fixing
- Manage return statement on JS and PY for Expand Button of As-Maintained Screen.
- Added the domain to the fields to restrict to make changes after RO/SR reached to done stage.

## 01/08/2021
### Version 13.0.1.0.0
#### Bug fixing
- Fetch parent lot vehicle while creating RO for As-Maintained Screen.
- Added context on Vehicle Serial/Lot to set default product and company.

## 01/22/2021
### Version 13.0.1.0.0
#### Enhancement
- New RO must be created for As-Maintained Screen operations.

## 01/25/2021
### Version 13.0.1.0.0
#### Enhancements
- Fix replaced Lot/Serial issues.
- Code cleanup and enhancement for RO replacement.

## 01/27/2021
### Version 13.0.1.0.0
#### Enhancements
- Fix replaced Lot/Serial issues to expand with the caret sign.
- Fix Collapse and Expand issues for As-Maintained screen after replace product id and lot name with lot id.

## 01/28/2021
### Version 13.0.1.0.0
#### Enhancements
- Setup parent lot and data lot to manage collapse process on As-Maintained Screen.
- Fixed issues for add data from As-Maintained screen and manage process for the Installed Location for RO Lines.
- Fixes As-Maintained Screen Edit functionality and remove dead code.

## 01/29/2021
### Version 13.0.1.0.0
#### Bug Fixing
- Create RO while removing any traceable part using As-Maintained Screen by seeting up controller method routed as: /remove_lot_serial_number.
- Set is_none_production as True if part remove.

## 01/29/2021
### Version 13.0.1.0.0
#### Added fields in search view.
- vehicle.services (fields added product_id, lot_id).

## 02/05/2021
### Version 13.0.1.0.0
#### Bug Fixing.
- Trello-124: Bug in As-Maintained direct add/edit functionality.

## 02/09/2021
### Version 13.0.1.0.0
#### Bug Fixing.
- Fixed issue to updated Lot/Status version multiple times.
