/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { formatDate } from "@web/core/l10n/dates";
import { formatDateTime } from "@web/core/l10n/dates";
import { ListRenderer } from "@web/views/list/list_renderer";
import { registry } from "@web/core/registry"; 
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { onWillStart } from "@odoo/owl";
import { useService } from '@web/core/utils/hooks';
import { formatDuration } from "@web/core/l10n/dates";
import {
    useX2ManyCrud,
    useOpenX2ManyRecord,
} from "@web/views/fields/relational_utils";


export class TicketListRenderer extends ListRenderer {

    setup() {
        super.setup();
        this.orm = useService('orm');
        this.action = useService("action");
        this.actionService = useService("action");
        this.priorityMap = {
            0: 'Prioridad Baja',
            1: 'Prioridad Media',
            2: 'Prioridad Alta',
            3: 'Urgente',
        };

        this.stateMap = {
            'normal': 'En Progreso',
            'done': 'Listo',
            'blocked': 'Bloqueado',
        };

        onWillStart(async () => {
            if (this.props.list) {
                this.list = this.props.list;
            }
            const res = await this.orm.searchCount('helpdesk.ticket', []);
            this.anyTicket = res > 0;
        });
    }

    formatDate(date) {
        return formatDate(date);
    }

    formatDateTime(datetime) {
        return formatDateTime(datetime, { format: 'HH:mm' });
    }

    setDefaultColumnWidths() {}

    calculateColumnWidth(column) {

        return {
            type: 'absolute',
            value: '90px',
        }

    }

    get colspan() {
        if (this.props.activeActions) {
            return 3;
        }
        return 2;
    }

    get groupedList() {
        const grouped = {};
        for (const record of this.list.records) {
            const data = record.data;
            const group = this.formatDate(data.create_date); // Agrupamos por fecha (ej. "25/08/2024")
            const durationTracking = data['duration_tracking'] || {};

            let duration = 0;
            for (const key in durationTracking) {
                if (durationTracking.hasOwnProperty(key)) {
                    duration = durationTracking[key];
                    break;
                }
            }

            if (grouped[group] === undefined) {
                grouped[group] = {
                    name: group,
                    list: {
                        records: [],
                    },
                };
            }

            if (duration > 0) {
                record.shortTimeInStage = formatDuration(duration, false);
                record.fullTimeInStage = formatDuration(duration, true);
            } else {
                record.shortTimeInStage = 0;
            }

            grouped[group].list.records.push(record);
        }

        // Ordenar los grupos por fecha, de más reciente a más antiguo
        return Object.fromEntries(
            Object.entries(grouped).sort((a, b) => new Date(b[0]) - new Date(a[0]))
        );
    }

    get showTable() {
        return this.props.list.records.length;
    }

    get isEditable() {
        return this.props.editable !== false;
    }

    async onCellClicked(record, column, ev) {
        if (!this.isEditable) {
            return;
        }

        return await super.onCellClicked(record, column, ev);
    }

}
TicketListRenderer.rowsTemplate = "dv_custom_helpdesk.TicketListRenderer.Rows";
TicketListRenderer.template = 'dv_custom_helpdesk.TicketListRenderer';
TicketListRenderer.recordRowTemplate = "dv_custom_helpdesk.TicketListRenderer.RecordRow";

export class TicketX2ManyField extends X2ManyField {
    setup() {
        super.setup()
        const { saveRecord, updateRecord } = useX2ManyCrud(
            () => this.list,
            this.isMany2Many
        );

        const openRecord = useOpenX2ManyRecord({
            resModel: this.list.resModel,
            activeField: this.activeField,
            activeActions: this.activeActions,
            getList: () => this.list,
            saveRecord: async (record) => {
                await saveRecord(record);
                await this.props.record.save();
            },
            updateRecord: updateRecord,
            withParentId: this.props.widget !== "many2many",
        });

        this._openRecord = (params) => {
            params.title = this.getWizardTitleName();
            openRecord({...params});
        };
    }

    getWizardTitleName() {
        return _t("Ticket")
    }

}
TicketX2ManyField.components = {
    ...X2ManyField.components,
    ListRenderer: TicketListRenderer,
};

export const ticketX2ManyField = {
    ...x2ManyField,
    component: TicketX2ManyField,
};

registry.category("fields").add("ticket_one2many", ticketX2ManyField);