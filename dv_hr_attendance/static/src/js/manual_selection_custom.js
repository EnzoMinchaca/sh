 /** @odoo-module **/

import {KioskManualSelection} from "@hr_attendance/components/manual_selection/manual_selection";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import {Component, useState} from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

// export class CustomKioskManualSelection extends KioskManualSelection {
//     onSearchInput(ev) {
//         super.onSearchInput(ev);
//         console.log("CustomKioskManualSelection imported successfully!"); // Agregar este log
//         const searchInput = ev.target.value.toLowerCase();
//         if (searchInput.length) {
//             this.state.displayedEmployees = this.props.employees.filter(item =>
//                 (item.name && item.name.toLowerCase().includes(searchInput)) || 
//                 (item.vendor && item.vendor.toLowerCase().includes(searchInput))
//             );
//         } else {
//             this.state.displayedEmployees = this.props.employees;
//         }
//     }
// }
patch(KioskManualSelection.prototype, {
    onSearchInput(ev) {
        super.onSearchInput(ev);
        console.log("CustomKioskManualSelection imported successfully!"); // Agregar este log
        const searchInput = ev.target.value.toLowerCase();
        if (searchInput.length) {
            this.state.displayedEmployees = this.props.employees.filter(item =>
                (item.name && item.name.toLowerCase().includes(searchInput)) || 
                (item.vendor && item.vendor.toLowerCase().includes(searchInput))
            );
        } else {
            this.state.displayedEmployees = this.props.employees;
        }
    },
});
console.log("CustomKioskManualSelection initialized successfully!");