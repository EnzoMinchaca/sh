# -*- coding: utf-8 -*-

from odoo import models, fields, api
LINE_ID_HIERARCHY_DELIMITER = '|'

class AccountReport(models.Model):
    _inherit = 'account.report'

    @api.model
    def _parse_line_id(self, line_id):
        """Parse the provided string line id and convert it to its list representation.
        Empty strings for model and value will be converted to None.

        For instance if line_id is markup1~account.account~5|markup2~res.partner~8 (where | is the LINE_ID_HIERARCHY_DELIMITER),
        it will return [('markup1', 'account.account', 5), ('markup2', 'res.partner', 8)]
        :param line_id (str): the generic line id to parse
        """
        # return line_id and [
        #     # 'value' can sometimes be a string percentage, i.e. "20.0".
        #     # To prevent a ValueError, we need to convert it into a float first, then into an int.
        #     (markup, model or None, int(float(value)) if value else None)
        #     for markup, model, value in (key.split('~') for key in line_id.split(LINE_ID_HIERARCHY_DELIMITER))
        # ] or []

        return line_id and [
            # If value is complex, avoid trying to convert to int
            (markup, model or None, int(float(value)) if value.replace('_', '').isdigit() else value)
            for markup, model, value in (key.split('~') for key in line_id.split(LINE_ID_HIERARCHY_DELIMITER))
        ] or []