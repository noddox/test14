# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging
from odoo.exceptions import UserError
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class Res_Users(models.Model):
    _inherit = 'res.users'


    retention_iva_percentage_id = fields.Many2one("retention.iva.percentage", string="Retention IVA Percentage")
    tax_payer_type_id = fields.Many2one("tax.payer.type", string="Tax Payer Type")
    retention_boolean = fields.Boolean('Show retention iva %',default=False)
    # person_type_name = fields.Many2one("retention.islr.person.type", string="Person Type Name")

    @api.onchange('tax_payer_type_id')
    def onchange_tax_payer_type_id(self):
        if self.tax_payer_type_id:
            if self.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
                self.retention_boolean = True
            else:
                self.retention_boolean = False
        else:
            self.retention_boolean = False
