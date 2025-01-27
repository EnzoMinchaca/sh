import ast
import base64
import datetime
import dateutil
import email
import email.policy
import hashlib
import hmac
import json
import lxml
import logging
import pytz
import re
import time
import threading

from collections import namedtuple
from email.message import EmailMessage
from email import message_from_string
from lxml import etree
from werkzeug import urls
from xmlrpc import client as xmlrpclib
from markupsafe import Markup, escape

from odoo import _, api, fields, models, tools, registry, SUPERUSER_ID, Command
from odoo.exceptions import UserError, MissingError, AccessError
from odoo.osv import expression
from odoo.tools import is_html_empty, html_escape, html2plaintext, parse_contact_from_email
from odoo.tools.misc import clean_context, split_every

_logger = logging.getLogger(__name__)


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"
    
    original_partner_ids = fields.Many2many(
        'res.partner',
        'mail_compose_message_original_partner_rel',
        'wizard_id',
        'partner_id',
        string='Original Partner IDs',
        readonly=False,
        store=True,
    )
    
    @api.model
    def default_get(self, fields):
        res = super(MailComposeMessage, self).default_get(fields)
        #obtengo el contexto
        model = self._context.get('default_model')
        res_id = self._context.get('default_res_ids')

        if model and res_id:
            record = self.env[model].browse(res_id)
            follower_ids = record.message_partner_ids.ids

            #excluyo al usuario actual, ya que sino se estaria enviando un correo a si mismo 
            current_user_partner_id = self.env.user.partner_id.id
            follower_ids = [fid for fid in follower_ids if fid != current_user_partner_id]

            if 'partner_ids' in fields and follower_ids:
                res['partner_ids'] = [(6, 0, follower_ids)]
                res['original_partner_ids'] = [(6, 0, follower_ids)]    #este me sirve para copiar los contactos originales para no perder su referencia
        return res

    #este metodo se ejecuta unicamente en el formulario de la ventana modal, asi que viene joya para agregar el contexto aca y pasarlo de metodo en metodo hasta llegar a message_post para que haga la condicion
    def action_send_mail(self):
        """ Used for action button that do not accept arguments. """
        #con este contexto hago referencia que el mensaje enviado proviene desde el modal, para que asi en message_post evalue esto y asigne un valor u otro a un atibuti escencial para que funcione correctamente
        context = self.env.context.copy()
        context.update({'es_del_modal': True})

        #llamo a "_action_send_mail" con el nuevo contexto donde se incluye a es_del_modal
        self.with_context(context)._action_send_mail(auto_commit=False)
        model = self._context.get('default_model')
        res_id = self._context.get('default_res_ids')
        if model and res_id:
            record = self.env[model].browse(res_id)
            #el comportamiento nativo de odoo es suscribir a todos los nuevos que se incluyen en partner_ids al enviar el mensaje, entonces con esto me guardo los originales, luego desuscribo a todos los existentes para luego solo suscribir a los originales, asi evito que hayan nuevos seguidores que yo no haya agregado manualmente desde la vista de agregar seguidores
            #desuscribir a todos los seguidores actuales
            current_followers = record.message_partner_ids
            if current_followers:
                record.message_unsubscribe(partner_ids=current_followers.ids)
            #agregar al usuario actual como seguidor
            current_user_partner_id = self.env.user.partner_id.id
            if current_user_partner_id not in self.original_partner_ids.ids:
                self.original_partner_ids = [(4, current_user_partner_id)]
            
            #suscribir solo a los seguidores originales (partner_ids_custom)
            if self.original_partner_ids:
                record.message_subscribe(partner_ids=self.original_partner_ids.ids)
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _action_send_mail(self, auto_commit=False):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed.

        :return tuple: (
            result_mails_su: in mass mode, sent emails (as sudo),
            result_messages: in comment mode, posted messages
        )
        """
        result_mails_su, result_messages = self.env['mail.mail'].sudo(), self.env['mail.message']

        for wizard in self:
            if wizard.res_domain:
                search_domain = wizard._evaluate_res_domain()
                search_user = wizard.res_domain_user_id or self.env.user
                res_ids = self.env[wizard.model].with_user(search_user).search(search_domain).ids
            else:
                res_ids = wizard._evaluate_res_ids()
            # in comment mode: raise here as anyway message_post will raise.
            if not res_ids and wizard.composition_mode == 'comment':
                raise ValueError(
                    _('Mail composer in comment mode should run on at least one record. No records found (model %(model_name)s).',
                      model_name=wizard.model)
                )

            if wizard.composition_mode == 'mass_mail':
                result_mails_su += wizard.with_context(self.env.context)._action_send_mail_mass_mail(res_ids, auto_commit=auto_commit)  #asi para incluir al contexto de es_del_modal
            else:
                result_messages += wizard.with_context(self.env.context)._action_send_mail_comment(res_ids) #asi para incluir al contexto de es_del_modal
                
        #con esto hago que en la vista aparezca el usuario que hace la accion y no el configurado para el correo saliente, solo para la vista es esto
        user = self.env.user
        result_messages.author_id = user.partner_id

        return result_mails_su, result_messages
    
    def _action_send_mail_comment(self, res_ids):
        """ Send in comment mode. It calls message_post on model, or the generic
        implementation of it if not available (as message_notify). """
        self.ensure_one()
        post_values_all = self._prepare_mail_values(res_ids)
        ActiveModel = self.env[self.model] if self.model and hasattr(self.env[self.model], 'message_post') else self.env['mail.thread']
        if self.composition_batch:
            # add context key to avoid subscribing the author
            ActiveModel = ActiveModel.with_context(
                mail_create_nosubscribe=True,
                **self.env.context  #le agrego el contexto donde incluyo a es_del_modal
            )

        messages = self.env['mail.message']
        for res_id, post_values in post_values_all.items():
            if ActiveModel._name == 'mail.thread':
                post_values.pop('message_type')  # forced to user_notification
                post_values.pop('parent_id', False)  # not supported in notify
                if self.model:
                    post_values['model'] = self.model
                    post_values['res_id'] = res_id
                message = ActiveModel.message_notify(**post_values)
                if not message:
                    # if message_notify returns an empty record set, no recipients where found.
                    raise UserError(_("No recipient found."))
                messages += message
            else:
                messages += ActiveModel.browse(res_id).with_context(self.env.context).message_post(**post_values)   #llamo a este metodo pasandole el contexto donde esta es_del_modal
        return messages

#agregue este xq necesito modificar una parte del metodo message_post que tiene para agregarle una nueva condicion segun un contexto
class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    #para no romper el metodo se copio todo y alli hice modificaciones como para no perder partes fundamentales del metodo, solo se agrego una condicion
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *,
                     body='', subject=None, message_type='notification',
                     email_from=None, author_id=None, parent_id=False,
                     subtype_xmlid=None, subtype_id=False, partner_ids=None,
                     attachments=None, attachment_ids=None, body_is_html=False,
                     **kwargs):
        """ Post a new message in an existing thread, returning the new mail.message.

        :param str|Markup body: body of the message, str content will be escaped, Markup
            for html body
        :param str subject: subject of the message
        :param str message_type: see mail_message.message_type field. Can be anything but
            user_notification, reserved for message_notify
        :param str email_from: from address of the author. See ``_message_compute_author``
            that uses it to make email_from / author_id coherent;
        :param int author_id: optional ID of partner record being the author. See
            ``_message_compute_author`` that uses it to make email_from / author_id coherent;
        :param int parent_id: handle thread formation
        :param str subtype_xmlid: optional xml id of a mail.message.subtype to
          fetch, will force value of subtype_id;
        :param int subtype_id: subtype_id of the message, used mainly for followers
            notification mechanism;
        :param list(int) partner_ids: partner_ids to notify in addition to partners
            computed based on subtype / followers matching;
        :param list(tuple(str,str), tuple(str,str, dict)) attachments : list of attachment
            tuples in the form ``(name,content)`` or ``(name,content, info)`` where content
            is NOT base64 encoded;
        :param list attachment_ids: list of existing attachments to link to this message
            Should not be a list of commands. Attachment records attached to mail
            composer will be attached to the related document.
        :param bool body_is_html: indicates body should be threated as HTML even if str
            to be used only for RPC calls

        Extra keyword arguments will be used either
          * as default column values for the new mail.message record if they match
            mail.message fields;
          * propagated to notification methods if not;

        :return record: newly create mail.message
        """
        self.ensure_one()  # should always be posted on a record, use message_notify if no record

        # preliminary value safety check
        self._raise_for_invalid_parameters(
            set(kwargs.keys()),
            forbidden_names={'model', 'res_id', 'subtype'}
        )
        if self._name == 'mail.thread' or not self.id:
            raise ValueError(_("Posting a message should be done on a business document. Use message_notify to send a notification to an user."))
        if message_type == 'user_notification':
            raise ValueError(_("Use message_notify to send a notification to an user."))
        if attachments:
            # attachments should be a list (or tuples) of 3-elements list (or tuple)
            format_error = not tools.is_list_of(attachments, list) and not tools.is_list_of(attachments, tuple)
            if not format_error:
                format_error = not all(len(attachment) in {2, 3} for attachment in attachments)
            if format_error:
                raise ValueError(
                    _('Posting a message should receive attachments as a list of list or tuples (received %(aids)s)',
                      aids=repr(attachment_ids),
                     )
                )
        if attachment_ids and not tools.is_list_of(attachment_ids, int):
            raise ValueError(
                _('Posting a message should receive attachments records as a list of IDs (received %(aids)s)',
                  aids=repr(attachment_ids),
                 )
            )
        attachment_ids = list(attachment_ids or [])
        if partner_ids and not tools.is_list_of(partner_ids, int):
            raise ValueError(
                _('Posting a message should receive partners as a list of IDs (received %(pids)s)',
                  pids=repr(partner_ids),
                 )
            )
        partner_ids = list(partner_ids or [])

        # split message additional values from notify additional values
        msg_kwargs = {key: val for key, val in kwargs.items()
                      if key in self.env['mail.message']._fields}
        notif_kwargs = {key: val for key, val in kwargs.items()
                        if key not in msg_kwargs}

        # Add lang to context immediately since it will be useful in various flows later
        self = self._fallback_lang()

        # Find the message's author
        guest = self.env['mail.guest']._get_guest_from_context()
        if self.env.user._is_public() and guest:
            author_guest_id = guest.id
            author_id, email_from = False, False
        else:
            author_guest_id = False
            author_id, email_from = self._message_compute_author(author_id, email_from, raise_on_email=True)

        if subtype_xmlid:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id(subtype_xmlid)
        if not subtype_id:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        # automatically subscribe recipients if asked to
        if self._context.get('mail_post_autofollow') and partner_ids:
            self.message_subscribe(partner_ids=list(partner_ids))

        msg_values = dict(msg_kwargs)
        if 'email_add_signature' not in msg_values:
            msg_values['email_add_signature'] = True
        if not msg_values.get('record_name'):
            # use sudo as record access is not always granted (notably when replying
            # a notification) -> final check is done at message creation level
            msg_values['record_name'] = self.sudo().display_name
        if body_is_html and self.user_has_groups("base.group_user"):
            _logger.warning("Posting HTML message using body_is_html=True, use a Markup object instead (user: %s)",
                self.env.user.id)
            body = Markup(body)
        msg_values.update({
            # author
            'author_id': author_id,
            'author_guest_id': author_guest_id,
            'email_from': email_from,
            # document
            'model': self._name,
            'res_id': self.id,
            # content
            'body': escape(body),  # escape if text, keep if markup
            'message_type': message_type,
            'parent_id': self._message_compute_parent_id(parent_id),
            'subject': subject or False,
            'subtype_id': False if self.env.context.get('es_del_modal') else subtype_id,    #con esto logro el comportamiento deseado dependiendo de donde se envie, si es del modal debe de estar en False si o si, y si no proviene del modal debe tener a subtype_id si o si, esto para que funcione adecuadamente enviando el correo a quien corresponde
            # recipients
            'partner_ids': partner_ids,
        })
        # add default-like values afterwards, to avoid useless queries
        if 'record_alias_domain_id' not in msg_values:
            msg_values['record_alias_domain_id'] = self.sudo()._mail_get_alias_domains(default_company=self.env.company)[self.id].id
        if 'record_company_id' not in msg_values:
            msg_values['record_company_id'] = self._mail_get_companies(default=self.env.company)[self.id].id
        if 'reply_to' not in msg_values:
            msg_values['reply_to'] = self._notify_get_reply_to(default=email_from)[self.id]

        msg_values.update(
            self._process_attachments_for_post(attachments, attachment_ids, msg_values)
        )  # attachement_ids, body
        new_message = self._message_create([msg_values])

        # subscribe author(s) so that they receive answers; do it only when it is
        # a manual post by the author (aka not a system notification, not a message
        # posted 'in behalf of', and if still active).
        author_subscribe = (not self._context.get('mail_create_nosubscribe') and
                             msg_values['message_type'] != 'notification')
        if author_subscribe:
            real_author_id = False
            # if current user is active, they are the one doing the action and should
            # be notified of answers. If they are inactive they are posting on behalf
            # of someone else (a custom, mailgateway, ...) and the real author is the
            # message author
            if self.env.user.active:
                real_author_id = self.env.user.partner_id.id
            elif msg_values['author_id']:
                author = self.env['res.partner'].browse(msg_values['author_id'])
                if author.active:
                    real_author_id = author.id
            if real_author_id:
                self._message_subscribe(partner_ids=[real_author_id])

        self._message_post_after_hook(new_message, msg_values)
        self._notify_thread(new_message, msg_values, **notif_kwargs)
        return new_message