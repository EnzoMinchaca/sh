/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AccountReportSearchBar } from "@account_reports/components/account_report/search_bar/search_bar";

patch(AccountReportSearchBar.prototype, {
    search() {
        const query = this.searchText.el.value.trim().toLowerCase();
        const linesIDsMatched = [];

        for (const line of this.controller.lines) {
            if (line.visible) {
                let lineName = line.name.trim().toLowerCase();
                let match = (lineName.indexOf(query) !== -1);

                // Buscar en 'td_po' si no hay coincidencia con 'name'
                if (!match) {
                    for (const column of line.columns) {
                        if (column.expression_label === 'td_po' && column.name) {
                            let tdPo = column.name.trim().toLowerCase();
                            match = (tdPo.indexOf(query) !== -1);
                            if (match) break;
                        }
                    }
                }

                // Buscar en 'td_invoice' si no hay coincidencia con 'name' ni con 'td_po'
                if (!match) {
                    for (const column of line.columns) {
                        if (column.expression_label === 'td_invoice' && column.name) {
                            let tdInvoice = column.name.trim().toLowerCase();
                            match = (tdInvoice.indexOf(query) !== -1);
                            if (match) break;
                        }
                    }
                }

                if (match) {
                    linesIDsMatched.push(line.id);
                }
            }
        }

        if (query.length && linesIDsMatched.length) {
            this.controller.lines_searched = linesIDsMatched;
            this.controller.updateOption("filter_search_bar", query);
        } else {
            delete this.controller.lines_searched;
            this.controller.deleteOption("filter_search_bar");
        }
    }
})

// registry.category('components').add('AccountReportSearchBar', CustomAccountReportSearchBar);

// export default CustomAccountReportSearchBar;