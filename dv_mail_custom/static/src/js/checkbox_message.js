/** @odoo-module **/
import { SuggestedRecipient } from '@mail/core/web/suggested_recipient';
import { patch } from "@web/core/utils/patch";

patch(SuggestedRecipient.prototype, {
    setup() {
        super.setup();
        //esto es para que el checkbox que aparece al presionar el boton Enviar mensaje aparezca siempre desseleccionado, lo comentado es por si solo se quiere para la vista de crm, sino es para todos los modulos 
        // if (this.props.thread.model == "crm.lead") {
        // }
        if (this.props.recipient) {
            this.props.recipient.checked = false;
        }
    },
})