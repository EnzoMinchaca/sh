/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

class OpenMoveLineRelatedWidget extends Component {
    static props = { ...standardFieldProps };

    setup() {
        super.setup();
        this.action = useService("action");
    }

    async openMove(ev) {
        const invoiceId = this.props.record.data.related_move_id[0];
        const letterId = this.props.record.data.account_letter_id[0];
        if (invoiceId) {
            this.action.doActionButton({
                type: "object",
                resId: invoiceId,
                name: "action_open_business_doc",
                resModel: "account.move",
            });
        }
        else{
            this.action.doActionButton({
                type: "object",
                resId: letterId,
                name: "action_open_business_doc",
                resModel: "account.letter",
            });
        }
    }
}

OpenMoveLineRelatedWidget.template = "dv_account_followup_paid.OpenMoveLineRelatedWidget";
registry.category("fields").add("open_move_line_related_widget", {
    component: OpenMoveLineRelatedWidget,
});