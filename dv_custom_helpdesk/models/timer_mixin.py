from odoo import models, fields, api, _
from math import ceil

class TimerMixin(models.AbstractModel):
    _inherit = 'timer.mixin'

    @api.depends_context('uid')
    def _compute_user_timer_id(self):
        """ Get the timers according these conditions
            :user_id is the user associated with the record
            :res_id is the current record
            :res_model is the current model
            limit=1 by security but the search should never have more than one record
        """
        Timer = self.env['timer.timer']
        for record in self:
            if record._name == 'helpdesk.ticket':
                user_id = record.user_id.id
            else:
                user_id = self.env.user.id
            timer_read_group = Timer._read_group(
                domain=[
                    ('user_id', '=', user_id),
                    ('res_id', '=', record.id),
                    ('res_model', '=', self._name),
                ],
                groupby=['res_id'],
                aggregates=['id:array_agg']
            )
            timer_by_model = dict(timer_read_group)
            record.user_timer_id = timer_by_model.get(record.id, False)

    def action_timer_start(self):
        """ Start the timer of the current record
        First, if a timer is running, stop or pause it
        If there isn't a timer for the current record, create one then start it
        Otherwise, resume or start it
        """
        self.ensure_one()
        # self._stop_timer_in_progress()
        # timer = self.user_timer_id
        if self._name == 'helpdesk.ticket':
            ticket = self.env['helpdesk.ticket'].browse(self.id)
            user_id = ticket.user_id.id
        else:
            self._stop_timer_in_progress()
            user_id = self.env.user.id
        timer = self.user_timer_id
        if not timer:
            timer = self.env['timer.timer'].create({
                'timer_start': False,
                'timer_pause': False,
                'is_timer_running': False,
                'res_model': self._name,
                'res_id': self.id,
                'user_id': user_id,
            })
            timer.action_timer_start()
        else:
            # Check if it is in pause then resume it or start it
            if timer.timer_pause:
                timer.action_timer_resume()
            else:
                timer.action_timer_start()
    
    def action_timer_resume(self):
        self.ensure_one()
        if self._name != 'helpdesk.ticket':
            self._stop_timer_in_progress()
        timer = self.user_timer_id
        timer.action_timer_resume()
    
    def _stop_timer_in_progress(self):
        """
        Cancel the timer in progress if there is one
        Each model can interrupt the running timer in a specific way
        By setting it in pause or stop by example
        """
        timers = self._get_user_timers().filtered(lambda t: t.is_timer_running)
        for timer in timers:
            if timer:
                model = self.env[timer.res_model].browse(timer.res_id)
                model._action_interrupt_user_timers()