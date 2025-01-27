/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { patch } from "@web/core/utils/patch";

patch(KanbanRenderer.prototype, {
    async sortRecordDrop(dataRecordId, dataGroupId, params) {
        // Llamamos del método original
        await super.sortRecordDrop(dataRecordId, dataGroupId, params);
        // Condición para aplicar solo en crm.lead
        if (this.props.list.config.resModel === 'crm.lead') {
            // Forzar recarga de la vista web
            window.location.reload();
        }
        if (this.props.list.config.resModel === 'project.project'){
            window.location.reload();
        }
    },
});