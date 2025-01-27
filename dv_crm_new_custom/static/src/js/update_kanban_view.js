/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { patch } from "@web/core/utils/patch";
import { Component, onPatched, onWillDestroy, onWillPatch, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(KanbanRenderer.prototype, {

    async sortRecordDrop(dataRecordId, dataGroupId, params) {
        // Llamamos del método original
        await super.sortRecordDrop(dataRecordId, dataGroupId, params);
        // Condición para aplicar solo en crm.lead
        if (this.props.list.config.resModel === 'crm.lead') {
            await this.props.list.load();
        }
    },
});