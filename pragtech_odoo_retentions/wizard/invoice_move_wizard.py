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


class account_move_wizard(models.TransientModel):
    _name = 'account.move.wizard'
    _description = "Account Move Wizard"

    partner_id = fields.Many2one('res.partner', string='Customer/Vendor', required=True)
    # move_line = fields.One2many('accont.move.line.wizard', 'wizard_id', string='Move Lines')
    ret_percentage = fields.Many2one("retention.islr.percentage", string="Retention Percent")
    person_type_code = fields.Many2one("retention.islr.person.type", string="Person Type Code",required=True)
    ret_islr_factor = fields.Many2one("retention.islr.factor", string="Retention ISLR Factor",required=True)
    ret_islr_tax_unit = fields.Many2one("tax.unit", string="Tax Unit",required=True)

    move_id = fields.Many2one('account.move', string='Account Move',
                                       copy=False)
    invoice_line_ids = fields.Many2one('account.move.line', string='Invoice lines',
                                        required = True )
    ret_date = fields.Date(string='Retention Date',
                           required=True)
    islr_taxable_amount = fields.Float(string='ISLR Taxable Amount',compute='_compute_data_values')
    islr_tax_amount = fields.Float(string='ISLR TAX amount',compute='_compute_data_values')
    islr_retention_ammount = fields.Float(string='ISLR Retention Amount',compute='_compute_data_values')
    sw_has_subtract = fields.Float(string='Has Subtract',compute='_compute_data_values')
    subtract_amount = fields.Float(string='Subtract Amount', default=0)
    net_retention = fields.Float(string='Net Retention',compute='_compute_data_values')
    # concept_code = fields.Many2one("retention.islr.concept", string="Name and Full name",required=True)

    @api.depends('invoice_line_ids')
    def _compute_data_values(self):
        if self.invoice_line_ids:
            print('\n\n self.invoice_line_ids', self.invoice_line_ids)

            self.islr_taxable_amount = self.invoice_line_ids.price_subtotal
            self.islr_tax_amount = self.invoice_line_ids.price_total - self.invoice_line_ids.price_subtotal
            # self.concept_code = self.invoice_line_ids.concept_code.id
            print('\n\n ===================== ', self.person_type_code.id, self.invoice_line_ids.concept_code.id)
            ret_percentage = self.env['retention.islr.percentage'].search(
                [('person_type_code', '=', self.person_type_code.id),
                 ('concept_code', '=', self.invoice_line_ids.concept_code.id)], limit=1)
            print(ret_percentage, '........................')
            if ret_percentage:
                self.ret_percentage = ret_percentage.id
                self.islr_retention_ammount = (self.islr_tax_amount * ret_percentage.ret_percentage) / 100
                self.sw_has_subtract = ret_percentage.sw_has_subtract
                self.subtract_amount = (
                                                   ret_percentage.sw_has_subtract * ret_percentage.ret_percentage * self.ret_islr_factor.factor_value * self.ret_islr_tax_unit.tax_unit_amount) / 100
                self.net_retention = self.islr_retention_ammount - self.subtract_amount

        else:
            self.islr_taxable_amount = 0
            self.islr_tax_amount = 0
            self.ret_percentage = 0
            self.islr_retention_ammount = 0
            self.sw_has_subtract = 0
            self.subtract_amount =0
            self.net_retention =0

    @api.onchange('ret_date')
    def onchange_ret_date(self):
        if self.ret_date:

            islr_factor = self.env['retention.islr.factor'].search([('init_date', '<', self.ret_date),
                                                                    ('end_date', '>', self.ret_date)], order='id desc')

            if islr_factor:
                self.ret_islr_factor = islr_factor[0].id
            else:
                raise UserError("Please Add ISLR Factor")
            tax_unit = self.env['tax.unit'].search([('init_date', '<', self.ret_date),
                                                                    ('end_date', '>', self.ret_date)],order='id desc')
            if tax_unit:
                self.ret_islr_tax_unit = tax_unit[0].id
            else:
                raise UserError("Please Add UNIT")



    @api.onchange('move_id')
    def onchange_move_id(self):
        res = {'domain': {}, 'value': {}}
        results = []
        account_move_search = self.env['account.move.line'].search([('move_id', '=', self.move_id.id),
                                                                    ('islr_retention_line_status', '=', 'not_created')])

        res['domain'].update({'invoice_line_ids': [('id', 'in', account_move_search.ids)]})
        return res

    @api.onchange('invoice_line_ids')
    def onchange_invoice_line_ids(self):
        if self.invoice_line_ids:
            print('\n\n self.invoice_line_ids',self.invoice_line_ids)

            self.islr_taxable_amount = self.invoice_line_ids.price_subtotal
            self.islr_tax_amount = self.invoice_line_ids.price_total - self.invoice_line_ids.price_subtotal
            # self.concept_code = self.invoice_line_ids.concept_code.id
            print('\n\n ===================== ',self.person_type_code.id,self.invoice_line_ids.concept_code.id)
            ret_percentage = self.env['retention.islr.percentage'].search([('person_type_code', '=', self.person_type_code.id),
                                                                ('concept_code', '=', self.invoice_line_ids.concept_code.id)],limit=1)
            print(ret_percentage,'.....++++++++++++++++++++++++++++++......')
            if ret_percentage:
                self.ret_percentage = ret_percentage.id
                self.islr_retention_ammount = (self.islr_tax_amount*ret_percentage.ret_percentage)/100
                self.sw_has_subtract = ret_percentage.sw_has_subtract
                self.subtract_amount = (ret_percentage.sw_has_subtract*ret_percentage.ret_percentage*self.ret_islr_factor.factor_value*self.ret_islr_tax_unit.tax_unit_amount)/100
                self.net_retention = self.islr_retention_ammount-self.subtract_amount


            else:
                raise UserError("Please Add record for ISLR percentage")
    @api.model
    def default_get(self, fields):
        res = super(account_move_wizard, self).default_get(fields)

        context = self._context
        active_move_id = int(context.get('default_move_id'))
        account_move_obj = self.env['account.move']
        if active_move_id:
            account_move_search = account_move_obj.search([('id', '=', active_move_id)], limit=1)
            result = []
            if account_move_search and account_move_search.invoice_line_ids:

                res.update({'partner_id':account_move_search.partner_id.id,})
        return res

    def create_islr_retention(self):
        ret_type = self.env['ret.type'].search(
            [('ret_type', '=', 'ISLR')])
        if ret_type:
            ret_type = ret_type.id
        else:
            ret_type = False
        create_islr_retention = {}
        if self.move_id:
            move_id = self.move_id
            # payment_type=''
            partner_type = ''
            if move_id.move_type == 'in_invoice':
                partner_type = 'supplier'
            if move_id.move_type == 'out_invoice':
                partner_type = 'customer'
            create_islr_retention = {
                'move_type': move_id.move_type,
                'partner_id': move_id.partner_id.id,
                'partner_type': partner_type,
                'ret_type': ret_type,
                'taxable_amount': self.islr_taxable_amount,
                'tax_amount': self.islr_tax_amount,
                'ret_amount': self.islr_retention_ammount,
                'subtract_amount': self.subtract_amount,
                'ret_percentage': self.ret_percentage.id,
                'net_retention': self.net_retention,
                'bill_number': move_id.name,
                'bill_date': move_id.invoice_date,
                'move_ref': move_id.id,

            }


        if create_islr_retention:
            print("GGGGGGGggggg", create_islr_retention)
            iva_retention = self.env['invoice.retention'].sudo().create(create_islr_retention)
            if iva_retention:
                self.invoice_line_ids.write({'islr_retention_line_status':'created'})
            account_move_search = self.env['account.move.line'].search([('move_id', '=', self.move_id.id),
                                                                        ('islr_retention_line_status', '=',
                                                                         'not_created')])
            if not account_move_search:
                self.move_id.write({'islr_retention_status': 'created'})
            # if self.move_id:
            #     ret_type = self.env['ret.type'].search(
            #         [('ret_type', '=', 'ISLR')])
            #     print('\nn\ n self.move_id.partner_id.commercial_partner_id.id',self.move_id.partner_id.commercial_partner_id.id,self.move_id.partner_id)
            #     if self.move_id.move_type == 'out_invoice':
            #         new_move = self.move_id.create_journal_iv_islr(iva_retention.net_retention, ret_type.posting_account, self.move_id.partner_id.commercial_partner_id.property_account_receivable_id, ret_type.journal_id, "test", self.move_id.invoice_date, self.move_id.partner_id.commercial_partner_id.id)
            #     else:
            #         new_move = self.move_id.create_journal_iv_islr(iva_retention.net_retention,
            #                                             self.move_id.partner_id.commercial_partner_id.property_account_payable_id,ret_type.posting_account,
            #                                             ret_type.journal_id, "test", self.move_id.invoice_date, self.move_id.partner_id.commercial_partner_id.id)
            #     new_pay_term_lines = new_move.line_ids \
            #         .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            #     inv_pay_term_lines = self.move_id.line_ids \
            #         .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            #     (new_pay_term_lines + inv_pay_term_lines).reconcile()

        return 1

