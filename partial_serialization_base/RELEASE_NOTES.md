## Module partial_serialization_base

## 12/15/2020 Initial Version
### Version 13.0.1.0.0
#### Initial Version
- [ADD] Added module: partial_serialization_base

## 01/05/2021
### Version 13.0.1.0.0
#### Enhancements
- Added method is_product_fleet_use, to check that
    - Current product traceability is partial serial.
    - It does not have any tacking policy.
    - Also, it must use for Fleet.

## 01/06/2021
### Version 13.0.1.0.0
#### Enhancements
- Added method is_product_manufacturing_use, to check that
    - Current product traceability is partial serial.
    - It does not have any tacking policy.
    - Also, it must use for MRP.

## 01/25/2021
### Version 13.0.1.0.0
#### Enhancements
- Added methods:
  - get_root_lot: To reach root Serial/Lot of current Lot/Serial.
  - _get_root_children: To get all the children of current Lot/Serial.
  - _get_root_children_after_map_parent: To get all the children of current Lot/Serial, but it will match the ROOT Lot/Serial.
  - adopt_children: To move children from one to another Lot/Serial.

## 01/28/2021
### Version 13.0.1.0.0
#### Enhancements
- Added field production_state to manage moves to edit lot.

## 01/29/2021
### Version 13.0.1.0.0
#### Enhancements
- Added method is_partial_serialization_product to check for partial.

## 02/01/2021
### Version 13.0.1.0.0
#### Enhancements
- Improve code quality and code cleanup.
