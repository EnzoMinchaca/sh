from odoo import fields, models


class ResumeLineType(models.Model):
    _name = 'helpdesk.line.type'
    _description = "Type of a resume line"
    _order = "sequence"

    name = fields.Char(default="Tickets")
    sequence = fields.Integer('Sequence', default=10)
