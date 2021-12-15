# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from dateutil.parser import parse as duparse
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError
from odoo.tools import ustr, consteq
_logger = logging.getLogger(__name__)
from datetime import date


class LineConceptCodeWizard(models.TransientModel):
    _name = "line.concept.code.wizard"
    _description = "Add Concept Code"

    concept_code = fields.Many2one("retention.islr.concept", string="Concept Code",required=True)


    def add_concept_code(self):
        context = self._context
        if context.get('move_line_id'):
            move_line_id = context.get('move_line_id')
            move_line_id = self.env['account.move.line'].browse(int(move_line_id))
            zero_concept_id = self.env['retention.islr.concept'].search([('concept_code', '=', '0')], limit=1)
            if self.concept_code.id and self.concept_code.id == zero_concept_id.id:
                move_line_id.sudo().write({'concept_code': self.concept_code.id,'islr_retention_line_status':'not_applied'})
            if self.concept_code.id and self.concept_code.id != zero_concept_id.id:
                move_line_id.sudo().write({'concept_code': self.concept_code.id, 'islr_retention_line_status': 'not_created'})

