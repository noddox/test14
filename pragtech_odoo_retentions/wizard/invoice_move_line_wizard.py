# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.TransientModel):
    _name = 'accont.move.line.wizard'
    _description = "Account Move line Wizard"

    @api.depends('product_qty', 'price_unit')
    def compute_amount(self):
        if self:
            for rec in self:
                rec.price_subtotal = rec.product_qty * rec.price_unit
    
    name = fields.Text(string='Label')
    # wizard_id = fields.Many2one('account.move.wizard')

    product_id = fields.Many2one('product.product', string='Product')
    account_id = fields.Many2one('account.account', string='Account',
                                 index=True, ondelete="cascade",
                                 domain="[('deprecated', '=', False), ('company_id', '=', 'company_id'),('is_off_balance', '=', False)]",
                                 check_company=True,
                                 tracking=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount")
    concept_code = fields.Many2one("retention.islr.concept", string="Concept Code", )
    islr_retention_line_status = fields.Selection(selection=[
        ('not_created', 'ISLR Not created'),
        ('created', 'ISLR Created'),
        ('not_applied', 'ISLR Not applicable'),
    ], string='ISLR retention status ', required=True, readonly=True, copy=False, tracking=True,
        default='not_created')
    product_qty = fields.Float(string='Quantity', default=1)
    price_unit = fields.Float(string='Unit Price')
    price_subtotal = fields.Float(compute='compute_amount', string='Subtotal')
    
    # @api.onchange('product_id')
    # def get_unit_price(self):
    #     if self:
    #         for rec in self:
    #             if rec and rec.product_id:
    #                 # this code is for assign unit price automatic
    #                 product_obj = self.env['product.product']
    #                 product_id = product_obj.search([('id', '=', rec.product_id.id)], limit=1)
    #                 if product_id:
    #                     self.price_unit = product_id.standard_price
    #                     self.name = product_id.name
    #                     if product_id.uom_po_id:
    #                         self.product_uom = product_id.uom_po_id.id
    #
