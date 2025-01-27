/** @odoo-module **/

import { registry } from '@web/core/registry';
import { formatDuration } from '@web/core/l10n/dates';
import { CharField, charField } from "@web/views/fields/char/char_field";

export class FieldDuration extends CharField {

    setup() {
        super.setup();
        const durationTracking = this.props.record.data.duration_tracking || {};
        let duration = 0;
        
        for (const key in durationTracking) {
            if (durationTracking.hasOwnProperty(key)) {
                duration = durationTracking[key];
                break;
            }
        }

        if (duration > 0) {
            this.props.record.data.shortTimeInStage = formatDuration(duration, false);
        } else {
            this.props.record.data.shortTimeInStage = "0";
        }
    }

}
FieldDuration.template = 'dv_custom_helpdesk.FieldDuration';

export const fieldDuration = {
    ...charField,
    component: FieldDuration,
};

registry.category('fields').add('format_duration', fieldDuration);
