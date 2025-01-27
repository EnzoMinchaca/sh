/** @odoo-module **/
import { FormController } from '@web/views/form/form_controller';
import { KanbanController } from '@web/views/kanban/kanban_controller';
import { KanbanRecordQuickCreate } from '@web/views/kanban/kanban_record_quick_create';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useEffect, useState } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            ...this.state,
            sku: "",
            sku_anterior: "",
        });
        //con esto logro que se ejecute de primeras,
        useEffect(() => {
            if (this.model.root.resModel === "crm.lead") {
                this._initializeSkuListener();  //lo hago en una funcion asi no le pongo tanto codigo al useEffect
            }
        });
    },
    //debounce? este metodo me permite poner una espera antes de ejecutar, en este caso estoy poniendo un tiempo de espera de 100 indicado debajo, esto significa que luego de que se ingresa un caracter se esperan 100 milisegundos antes de ejecutar toda la logica correspondiente, esto es para los casos en los que se borra un caracter y rapidamente se ingresa uno nuevo, al ser tan rapido, el codigo no tiene tiempo de procesar la segunda accion porque recien termina de procesar la primera, entonces por ejemplo si complete el sku y borro el ultimo caracter y nuevamente ingreso otro quedara el <p> del sku anterior pese a que ya se completo, entonces al esperar este tiempo no ejecutamos la primera accion ya que no pasan 200 ms antes de ingresar el siguiente caracter, consiguiendo evitar este compotamiento no deseado ante cambios muy rapidos
    debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },

    _initializeSkuListener() {
        //hay dos tipos de formularios, uno es el normal de siempre que ocupa toda la pantalla, y el otro es el modal(distinto del kanban), hago esto porque cada uno tiene una clase distinta, y si yo pongo solo el listener para el sku no va a funcionar por mas que el div este presente en ambos, asi solo lo reconoce para el formulario normal pero no para el modal, entonces debo de tomar todo el contenedor para hacer referencia al div sku dentro de ese contenedor dependiendo del tipo de formulario, de este modo si puedo capturar el valor del sku ingresado para ambos formularios con la condicional de en que formulario estoy segun su clase
        const modalForm = document.querySelector(".modal-content");
        const regularForm = document.querySelector(".o_form_view");

        //aca le doy prioridad al modal por el mismo motivo de que por si solo no me lo tomaba, sino existe es el otro formulario
        const formElement = modalForm || regularForm;

        if (!formElement) {
            console.error("No se encontró ningún formulario existente.");
            return;
        }

        //defino la funcion que emplea mi debounce para el input del listener del form
        const debouncedHandleInput = this.debounce(async (event) => {
            const target = event.target;
            //verifico que realmente el evento es del sku, mas que nada por si llega a cambiar entre un formulario o otro, dificilmente pasara pero por las dudas
            if (target.tagName === "INPUT" && target.parentElement.getAttribute("name") === "sku") {
                const skuInput = target;
                const divSku = skuInput.parentElement;
                const newSkuValue = skuInput.value;

                //elimino el p para cuando sea menor a 6
                if (!newSkuValue || newSkuValue.length < 6) {
                    const existingParagraph = divSku.nextElementSibling;
                    if (existingParagraph && existingParagraph.tagName === "P") {
                        existingParagraph.remove();
                    }
                    return;
                }
                
                let paragraph = divSku.nextElementSibling;
                if (!paragraph || paragraph.tagName !== "P") {
                    paragraph = document.createElement("p");
                    divSku.insertAdjacentElement("afterend", paragraph);
                }

                //validaciones de cuando sea mayor a 6 y menor a 9
                if (!newSkuValue || newSkuValue.length < 6 || newSkuValue.length >= 9) {
                    paragraph.textContent = ""; //si la cumple le borro el contenido
                    return;
                }

                //buscar el SKU anterior si el valor tiene entre 6 y 9 caracteres
                if (newSkuValue.length >= 6 && newSkuValue.length < 9) {
                    try {
                        const leads = await this.orm.searchRead("crm.lead", [], ["sku"]); //leads con sku
                        const terminacionesValidas = ["LG", "CE", "SC", "LP", "DP"];  //terminos existentes
                        const añomesYTerminacion = newSkuValue.slice(0, 6);    //año, mes y codigo ingresado
                        const terminacion = newSkuValue.slice(4, 6);    //codigo ingresado

                        if (terminacionesValidas.includes(terminacion)) {  //comparo la terminacion del sku ingresado con respecto a las ya existentes
                            const skusValidos = leads
                                .map((lead) => lead.sku)
                                .filter((sku) => {
                                    if (!sku || sku.length !== 9) return false;  //tiene el formato correcto
                                    return sku.slice(0, 6) === añomesYTerminacion;
                                })
                                .sort((a, b) => {   //aca comparo los ultimos 3 numeros para ordenarlos de mayor a menor para traer el mas nuevo
                                    const numA = parseInt(a.slice(6), 10);
                                    const numB = parseInt(b.slice(6), 10);
                                    return numB - numA; //orden descendente osea mas reciente primero
                                });
                            //si hay un sku pongo ese sino pongo el que se esta escribiendo con 000 al final
                            const skuAnterior = skusValidos.length > 0
                                ? skusValidos[0]
                                : `${newSkuValue.slice(0, 6)}000`;
                            //y si hay un sku anterior lo agrego al p
                            paragraph.textContent = skuAnterior;
                        } else {
                            //si no se escribio una terminacion correspondiente a las existentes
                            paragraph.textContent = "Nomenclatura no válida";
                        }
                    } catch (error) {
                        console.error("Error al buscar las leads:", error);
                    }
                }
            }
        }, 200); //ejecuto una espera de 200 mlisisegundos
        //le agrego el listener al input del formulario y le paso tambien el metodo para su ejecucion
        formElement.addEventListener("input", debouncedHandleInput);
    },
});


patch(KanbanController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },
    //cuando se ejecuta esta accion se despliega el formulario del kanban, entonces aca le meto toda la logica
    async createRecord() {
        const { onCreate } = this.props.archInfo;
        const { root } = this.model;
        if (this.canQuickCreate && onCreate === "quick_create") {
            const firstGroup = root.groups[0];
            //primero valido si estoy en el modelo de crm para no meterle todo este codigo para todos los kanban de cualquier modelo
            if (this.model.root.resModel === "crm.lead") {
                setTimeout(() => {
                    let divSku = document.querySelector('div[name="sku"]');
                    if (!divSku) return; //por las dudas de que no detecte el div salgo asi no se rompe
    
                    let skuInput = divSku.querySelector('input');
                    if (skuInput) {
                        skuInput.addEventListener('input', async (event) => {
                            const newSkuValue = event.target.value;
                            this._handleSkuInput(newSkuValue, divSku); //me creo una funcion nueva asi ya no le agrego tantas cosas a esta funcion actual que estoy sobrescribiendo
                        });
                    }
                }, 1000);   //le agrego este setTimeOut ya que hay una pequeña demora entre apretar el boton y que se visualicen los camppos del formulario rapido
            }
            if (firstGroup.isFolded) {
                await firstGroup.toggle();
            }
            this.quickCreateState.groupId = firstGroup.id;
        } else if (onCreate && onCreate !== "quick_create") {
            const options = {
                additionalContext: root.context,
                onClose: async () => {
                    await root.load();
                    this.model.useSampleModel = false;
                    this.render(true); // FIXME WOWL reactivity
                },
            };
            await this.actionService.doAction(onCreate, options);
        } else {
            await this.props.createRecord();
        }
    },

    async _handleSkuInput(newSkuValue, divSku) {
        //me guardo el proximo elemento del div del sku
        let paragraph = divSku.nextElementSibling;

        //solo muestro el p si pasa los 6 y antes de los 9
        if (!newSkuValue || newSkuValue.length < 6 || newSkuValue.length >= 9) {
            if (paragraph && paragraph.tagName === 'P') {
                paragraph.remove(); //lo borro si es un p
            }
            return;
        }

        //si no existe el p lo creo
        if (!paragraph || paragraph.tagName !== 'P') {
            paragraph = document.createElement('p');
            divSku.insertAdjacentElement('afterend', paragraph);
        }

        //llamo a esta otra funcion que me busca el sku anterior
        if (newSkuValue.length >= 6 && newSkuValue.length < 9) {
            await this._fetchSkuAnterior(newSkuValue, paragraph);
        }
    },

    async _fetchSkuAnterior(newSkuValue, paragraph) {
        try {
            //este paso es practicamente igual al del formcontroller
            const leads = await this.orm.searchRead('crm.lead', [], ['sku']);
            const terminacionesValidas = ["LG", "CE", "SC", "LP", "DP"];
            const añomesYTerminacion = newSkuValue.slice(0, 6); //año, mes y codigo ingresado
            const terminacion = newSkuValue.slice(4, 6); //codigo ingresado

            if (terminacionesValidas.includes(terminacion)) {   //comparo la terminacion del sku ingresado con respecto a las ya existentes
                const skusValidos = leads
                    .map(lead => lead.sku)
                    .filter(sku => {
                        if (!sku || sku.length !== 9) return false; //me fijo si tiene el formato correcto
                        return sku.slice(0, 6) === añomesYTerminacion;
                    })
                    .sort((a, b) => {
                        //aca comparo los ultimos 3 numeros para ordenarlos de mayor a menor para traer el mas nuevo
                        const numA = parseInt(a.slice(6), 10);
                        const numB = parseInt(b.slice(6), 10);
                        return numB - numA; //orden descendente osea el mas reciente va primero
                    });

                //si hay un sku pongo ese sino pongo el que se esta escribiendo con 000 al final
                const skuAnterior = skusValidos.length > 0 ? skusValidos[0] : `${newSkuValue.slice(0, 6)}000`;

                //y si hay un sku anterior lo agrego al p
                paragraph.textContent = skuAnterior;
            } else {
                //si no se escribio una terminacion correspondiente a las existentes
                paragraph.textContent = "Nomenclatura no válida";
            }
        } catch (error) {
            console.error("Error al buscar las leads:", error);
        }
    },
});
//solo me interesa KanbanQuickCreateController pero este no se exporta, asi que ingreso a el desde KanbanRecordQuickCreate que lo tiene como objeto desde components
patch(KanbanRecordQuickCreate.components.KanbanQuickCreateController.prototype, {
    //metodo que hace las validaciones
    async _validateSku(sku) {
        //valido su codigo de nomenclatura
        const validEndings = ["LG", "CE", "SC", "LP", "DP"];
        const ending = sku.slice(4, 6);
        if (!validEndings.includes(ending)) {
            return "El SKU debe contener con una nomenclatura válida (LG, CE, SC, LP, DP).";
        }
        //valido si termina en 000
        if (sku.endsWith("000")) {
            return "No se puede guardar un SKU con terminación '000'. Ingrese un SKU válido.";
        }
        try {
            const [existingSku] = await this.model.orm.call(    //busco si ya existe un sku igual 
                "crm.lead",
                "search_read",
                [
                    ["|", ["sku", "=", sku], ["sku", "ilike", `%${sku}`]],
                    ["sku"],
                ],
                { limit: 1 }
            );
            if (existingSku) {
                if (existingSku.sku === sku) {
                    return "El SKU ingresado ya existe en otro registro. Ingrese otro.";
                }
            }
        } catch (e) {
            console.error("Error al validar SKU existente:", e);
            return "Ocurrió un error al validar el SKU. Inténtelo de nuevo.";
        }
        //si no cumple con ninguna no hay problema y no devuelvo ningun mensaje
        return null;
    },
    //metodo sobreescrito, solo le agrego la validacion del sku, lo demas es como el original
    async validate(mode) {
        //solo ejecuto las validaciones si el modelo es crm
        if (this.props.resModel === "crm.lead") {
            const sku = this.model.root.data.sku;
            //si hay un mensaje quiere decir que el sku no es valido asi que muestro el mensaje y corto la ejecucion posterior
            const validationMessage = await this._validateSku(sku);
            if (validationMessage) {
                this.model.notification.add(validationMessage, {
                    type: "danger",
                });
                this.state.disabled = false;
                return;
            }
        }
        //codigo original
        let resId = undefined;
        if (this.state.disabled) {
            return;
        }
        this.state.disabled = true;

        const keys = Object.keys(this.model.root.activeFields);
        if (keys.length === 1 && keys[0] === "display_name") {
            const isValid = await this.model.root.checkValidity(); // needed to put the class o_field_invalid in the field
            if (isValid) {
                try {
                    [resId] = await this.model.orm.call(
                        this.props.resModel,
                        "name_create",
                        [this.model.root.data.display_name],
                        {
                            context: this.props.context,
                        }
                    );
                } catch (e) {
                    this.showFormDialogInError(e);
                }
            } else {
                this.model.notification.add(_t("Display Name"), {
                    title: _t("Invalid fields: "),
                    type: "danger",
                });
            }
        } else {
            await this.model.root.save({
                reload: false,
                onError: (e) => this.showFormDialogInError(e),
            });
            resId = this.model.root.resId;
        }

        if (resId) {
            await this.props.onValidate(resId, mode);
            if (mode === "add") {
                await this.model.load({ resId: false });
            }
        }
        this.state.disabled = false;
    }
});