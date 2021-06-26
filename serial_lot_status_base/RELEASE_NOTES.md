
## Module serial_lot_status_base

## 12/21/2020 Initial Version
### Version 13.0.1.0.0
#### Initial Version
- Serail Lot Status - [ADD]: add initial commit of this module.

## 12/22/2020 Initial Version
### Version 13.0.1.0.0
#### Updated for serial quantity update
- Fixed issues while the update/create quantity.
- Reset code for Stock Quant
- Rename File stock.py to stock_quant.py

## 12/28/2020 Initial Version
### Version 13.0.1.0.0
#### Stock Moves & Lot Status
- Manges Serial/Lot Status with Installed Flag
- Remove dead code

## 12/29/2020 Code Cleanup
### Version 13.0.1.0.0
#### MO Components Move
- Updated for MO Component move lot changes and also set finished lot on move lines.

## 12/30/2020 Bug Fixing
### Version 13.0.1.0.0
#### Consume Lot on update status
- Fixed lot installation status issue for those MO Products which is not serialised.

## 01/04/2021
### Version 13.0.1.0.0
#### Serial/Lot Installed lot_id
- Added method name get_root_lot to reach root Serial/Lot of current Lot.   

## 01/12/2021
### Version 13.0.1.0.0
#### Code cleanup & Enhancements
- Added the doc string and remove unnecessary local variables and added method to replace the old lot with new lot installation location.

## 01/22/2021
### Version 13.0.1.0.0
#### Enhancement
- Update QC on change of Lot/Serial number.

## 01/25/2021
### Version 13.0.1.0.0
#### Enhancements
- Moved the get_root_lot method to partial serialization module.

## 02/01/2021
### Version 13.0.1.0.0
#### Bug Fixing & Enhancements
- Improve code quality and code cleanup.
- Added status in Lot/Serial Tree.
- Remove unnecessary code.
- Added quality to dependency.

## 02/05/2021
### Version 13.0.1.0.0
#### Bug Fixing
- Check for type edit in context to filter lot.
- Manage demo data references with search.
