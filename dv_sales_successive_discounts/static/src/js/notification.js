/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from '@odoo/owl';


class CustomComponentDiscount extends Component {
    setup() {
        super.setup();
        // Escuchar notificaciones usando useBus
        this.busService = this.env.services.bus_service
        this.channel = "successive_discount_notification"
        this.busService.addChannel(this.channel)
        this.busService.addEventListener("notification", this._onNotification.bind(this))
    }

    /**
     * Función para manejar la notificación del canal
     * @param {Array} notifications 
     */
    _onNotification({ detail: notifications }) {
        this.reload(data.id);
        let payload = message.detail[0].payload
        console.log("Notificaciones recibidas:", notifications); // Verifica que se reciban notificaciones
        if(payload.channel === 'successive_discount_notification' && payload.data.id === this.model.data.id){
            if(payload.data.state === 'confirmed'){
                console.log("Notificación de descuento sucesivo recibida:", message);
            }
        }
        /* for (const [channel, message] of notifications) {
            console.log("Canal:", channel, "Mensaje:", message);
            console.log("Mensaje:", message.data.id, "Modelo:", this.model.data.id);
            if (channel === 'successive_discount_notification' && message.data.id === this.model.data.id) {
                console.log("Notificación de descuento sucesivo recibida:", message);
                // Acciones a realizar cuando el estado cambia a 'Confirmado'
                if (message.data.state === 'confirmed') {
                    console.log("Notificación de descuento sucesivo recibida:", message);
                    this.reload(); // Recargar la vista si es necesario
                } else {
                    console.log("Estado no es confirmado:", message.data.state); // Si no es confirmado, muestra el estado
                }
            } else {
                console.log("Canal o ID no coinciden."); // Muestra si no coincide el canal o el ID
            }
        } */
    }
}

// Registrar el componente modificado
registry.category('components').add('custom_component_discount', CustomComponentDiscount);
