# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
import requests
import base64
from dateutil.parser import parse as duparse
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError
from odoo.tools import ustr, consteq
_logger = logging.getLogger(__name__)
from datetime import date


class IvaRetentionCreationWizard(models.TransientModel):
    _name = "iva.invoice.retention.wizard"
    _description = "IVA Retention Creation"

    ret_iva_percent = fields.Many2one("retention.iva.percentage", string="Retention IVA Percentage",required=True)
    ret_date = fields.Date(string='Retention Date', default=date.today(),
                           required=True)
    iva_taxable_amount = fields.Float(string='IVA Taxable Amount')
    iva_tax_amount = fields.Float(string='IVA TAX amount')
    iva_retention_ammount = fields.Float(string='IVA Retention Amount')
    subtract_amount = fields.Float(string='Subtract Amount',default=0)
    net_retention  = fields.Float(string='Net Retention')

    @api.model
    def default_get(self, fields_list):
        rec = models.TransientModel.default_get(self, fields_list)
        print('\n\n rezssssssssssssssssssssss ',rec)
        # res.update({
        #     'project_id': self._context.get('project_id'),
        #     'name': self._context.get('project_wbs'),
        #     'sub_project': self._context.get('sub_project'),
        # })
        return rec


    @api.onchange('retention_iva_percentage_id')
    def onchange_retention_iva_percentage_id(self):
        if self.retention_iva_percentage_id.ret_value:
            self.iva_retention_ammount = (self.iva_tax_amount * self.retention_iva_percentage_id.ret_value) / 100
            self.net_retention = self.iva_retention_ammount - self.subtract_amount
        else:
            raise UserError("Please add a IVA Retention value")


    def create_iva_retention(self):
        print('\n\n context =', self._context)
        ret_type = self.env['ret.type'].search(
            [('ret_type', '=', 'IVA')])
        if ret_type:
            ret_type=ret_type.id
        else:
            ret_type=False
        context = self._context
        create_iva_retention={}
        if context.get('move_id'):
            move_id= context.get('move_id')
            move_id = self.env['account.move'].browse(int(move_id))
            print(move_id,move_id.name)
            # payment_type=''
            partner_type=''
            if move_id.move_type=='in_invoice':
                # payment_type='inbound'
                partner_type = 'supplier'
            if move_id.move_type=='out_invoice':
                # payment_type='outbound'
                partner_type = 'customer'
            create_iva_retention={
                'move_type':move_id.move_type,
                'partner_id': move_id.partner_id.id,
                # 'payment_type': payment_type,
                'partner_type': partner_type,
                'ret_type': ret_type,
                'taxable_amount': self.iva_taxable_amount,
                'tax_amount': self.iva_tax_amount,
                'ret_amount': self.iva_retention_ammount,
                'subtract_amount': self.subtract_amount,
                'ret_iva_percentage': self.retention_iva_percentage_id.id,
                'net_retention': self.net_retention,
                'bill_number': move_id.name,
                'bill_date': move_id.invoice_date,
                'move_ref':move_id.id,

            }
            if create_iva_retention:
                print('create_iva_retention',create_iva_retention)

                iva_retention = self.env['invoice.retention'].sudo().create(create_iva_retention)
                if iva_retention:
                    move_id.iva_retention_status='created'
                new_move = False
                if move_id:
                    ret_type = self.env['ret.type'].search(
                        [('ret_type', '=', 'IVA')])
                    if move_id.move_type == 'out_invoice':
                        new_move = move_id.create_journal_iv_islr(self.net_retention, ret_type.posting_account,
                                                            move_id.partner_id.commercial_partner_id.property_account_receivable_id,
                                                            ret_type.journal_id, "test", move_id.invoice_date, move_id.partner_id.commercial_partner_id.id)
                    else:
                        new_move = move_id.create_journal_iv_islr(self.net_retention,
                                                            move_id.partner_id.commercial_partner_id.property_account_payable_id,
                                                            ret_type.posting_account,
                                                            ret_type.journal_id, "test", move_id.invoice_date,move_id.partner_id.commercial_partner_id.id)
                    new_pay_term_lines = new_move.line_ids \
                        .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    inv_pay_term_lines = move_id.line_ids \
                        .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    (new_pay_term_lines+inv_pay_term_lines).reconcile()

            return 1