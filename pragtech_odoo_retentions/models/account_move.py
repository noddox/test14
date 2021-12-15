from odoo import fields, models, api, _
from datetime import date

import logging

_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from datetime import date


class AccountMoveInherit(models.Model):
    _inherit = "account.move"
    cnt_num = fields.Char(string='Control Number')
    iva_retention_status = fields.Selection(selection=[
        ('not_created', 'Not created'),
        ('created', 'Created'),
        ('not_applied', 'No Applica'),
    ], string='IVA Status', required=True, readonly=True, copy=False, tracking=True,
        default='not_created')

    islr_retention_status = fields.Selection(selection=[
        ('not_created', 'Not created'),
        ('created', 'Created'),
        ('not_applied', 'No Applica'),
    ], string='ISLR Status ', required=True, readonly=True, copy=False, tracking=True,
        default='not_created')
    retention_boolean = fields.Boolean('Show retention iva %', default=False, compute='compute_retention_boolean')
    islr_retention_boolean = fields.Boolean('Show retention ISLR %', default=False,
                                            compute='onchange_islr_retention_status')

    @api.depends('islr_retention_status')
    def onchange_islr_retention_status(self):
        if self.islr_retention_status and self.islr_retention_status == 'created':
            self.islr_retention_boolean = True
        else:
            self.islr_retention_boolean = False

    @api.depends('partner_id')
    def compute_retention_boolean(self):
        if self.move_type:
            if self.move_type == 'in_invoice':
                if self.partner_id.tax_payer_type_id:
                    if self.partner_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
                        if self.iva_retention_status != 'created':
                            self.retention_boolean = True
                            self.iva_retention_status = 'not_created'
                        else:
                            self.retention_boolean = False
                            self.iva_retention_status = 'created'
                    else:
                        self.retention_boolean = False
                        self.iva_retention_status = 'not_applied'
                else:
                    self.retention_boolean = False
                    self.iva_retention_status = 'not_applied'
            elif self.move_type == 'out_invoice':
                if self.company_id.tax_payer_type_id:
                    if self.company_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
                        if self.iva_retention_status != 'created':
                            self.retention_boolean = True
                            self.iva_retention_status = 'not_created'
                        else:
                            self.retention_boolean = False
                            self.iva_retention_status = 'created'
                    else:
                        self.retention_boolean = False
                        self.iva_retention_status = 'not_applied'
                else:
                    self.retention_boolean = False
                    self.iva_retention_status = 'not_applied'
            else:
                self.retention_boolean = False
        else:
            self.retention_boolean = False

    # @api.onchange('partner_id')
    # def onchange_vendor_id(self):
    #     if self.move_type:
    #         if self.move_type=='in_invoice':
    #             if self.partner_id.tax_payer_type_id:
    #                 if self.partner_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
    #                     if self.iva_retention_status != 'created':
    #                         self.retention_boolean = True
    #                         self.iva_retention_status = 'not_created'
    #                     else:
    #                         self.retention_boolean = False
    #                         self.iva_retention_status = 'created'
    #                 else:
    #                     self.retention_boolean = False
    #                     self.iva_retention_status = 'not_applied'
    #             else:
    #                 self.retention_boolean = False
    #                 self.iva_retention_status = 'not_applied'
    #
    #         if self.move_type == 'out_invoice':
    #             if self.company_id.tax_payer_type_id:
    #                 if self.company_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
    #                     if self.iva_retention_status != 'created':
    #                         self.retention_boolean = True
    #                         self.iva_retention_status = 'not_created'
    #                     else:
    #                         self.retention_boolean = False
    #                         self.iva_retention_status = 'created'
    #                 else:
    #                     self.retention_boolean = False
    #                     self.iva_retention_status = 'not_applied'
    #             else:
    #                 self.retention_boolean = False
    #                 self.iva_retention_status = 'not_applied'
    #         else:
    #             self.retention_boolean = False
    #     else:
    #         self.retention_boolean = False

    def button_iva_retention(self):
        if self.state == 'posted':
            if self.move_type == 'in_invoice':
                view_id = self.env.ref('pragtech_odoo_retentions.create_iva_retention_wizard_view_form', False).id,
                move_lines = self.env['account.move.line'].search(
                    [('move_id', '=', self.id), ('tax_line_id', '!=', False)])

                taxable_amount = 0
                for line in move_lines:
                    taxable_amount = taxable_amount + line.tax_base_amount

                return {
                    'name': _("IVA Retention"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'iva.invoice.retention.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'move_id': self.id,
                        'default_retention_iva_percentage_id': self.partner_id.retention_iva_percentage_id.id,
                        'default_iva_taxable_amount': taxable_amount,
                        'default_iva_tax_amount': self.amount_tax,
                        'default_ret_date': self.invoice_date,

                    }
                }
            if self.move_type == 'out_invoice':
                view_id = self.env.ref('pragtech_odoo_retentions.create_iva_retention_wizard_view_form', False).id,
                move_lines = self.env['account.move.line'].search(
                    [('move_id', '=', self.id), ('tax_line_id', '!=', False)])

                taxable_amount = 0
                for line in move_lines:
                    taxable_amount = taxable_amount + line.tax_base_amount

                return {
                    'name': _("IVA Retention"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'iva.invoice.retention.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'move_id': self.id,
                        'default_retention_iva_percentage_id': self.company_id.retention_iva_percentage_id.id,
                        'default_iva_taxable_amount': taxable_amount,
                        'default_iva_tax_amount': self.amount_tax,
                        'default_ret_date': self.invoice_date,

                    }
                }
        else:
            raise UserError("Please confirm the bill to proceed.")

    def button_islr_retention(self):
        if self.state == 'posted':
            if self.move_type == 'in_invoice':
                view_id = self.env.ref('pragtech_odoo_retentions.islr_account_move_wizard', False).id,
                move_lines = self.env['account.move.line'].search(
                    [('move_id', '=', self.id), ('tax_line_id', '!=', False)])

                taxable_amount = 0
                for line in self.invoice_line_ids:
                    if line.islr_retention_line_status == 'insert_islr':
                        raise UserError("ISLR insert for invoice lines not complete")

                    taxable_amount = taxable_amount + line.tax_base_amount

                return {
                    'name': _("ISLR Retention"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'account.move.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_move_id': self.id,
                        'default_invoice_line_ids': self.invoice_line_ids.ids,
                        'default_person_type_code': self.partner_id.person_type_code_id.id,
                        'default_iva_taxable_amount': taxable_amount,
                        'default_iva_tax_amount': self.amount_tax,
                        'default_ret_date': self.invoice_date,

                    }
                }
            if self.move_type == 'out_invoice':
                view_id = self.env.ref('pragtech_odoo_retentions.islr_account_move_wizard', False).id,
                move_lines = self.env['account.move.line'].search(
                    [('move_id', '=', self.id), ('tax_line_id', '!=', False)])

                taxable_amount = 0
                for line in self.invoice_line_ids:
                    if line.islr_retention_line_status == 'insert_islr':
                        raise UserError("ISLR insert for invoice lines not complete")

                    taxable_amount = taxable_amount + line.tax_base_amount

                return {
                    'name': _("ISLR Retention"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'account.move.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_move_id': self.id,
                        'default_invoice_line_ids': self.invoice_line_ids.ids,
                        'default_person_type_code': self.company_id.person_type_name.id,
                        'default_iva_taxable_amount': taxable_amount,
                        'default_iva_tax_amount': self.amount_tax,
                        'default_ret_date': self.invoice_date,

                    }
                }
        else:
            raise UserError("Please confirm the Invoice/Bill to proceed.")

    def create_journal_iv_islr(self, rt_amount, db_acc, cr_acc, journal_id, desc, rtdate,pid):
        print("TTTTTTTTTTTTTTTTTTTTTTTTTT",rt_amount, db_acc, cr_acc, journal_id, desc, rtdate,pid)

        line_ids = [
            (0, 0,
             {'journal_id': journal_id.id, 'partner_id':pid, 'account_id': db_acc.id,
              'name': desc,
              'amount_currency': 0.0, 'debit': rt_amount}),
            (0, 0, {'journal_id': journal_id.id, 'partner_id':pid, 'account_id': cr_acc.id,
                    'name': desc, 'amount_currency': 0.0, 'credit': rt_amount,
                    })
        ]

        vals = {
            'journal_id': journal_id.id,
            'ref': desc,
            'narration': desc,
            'date': rtdate,
            'line_ids': line_ids,
        }
        account_move = self.env['account.move'].sudo().create(vals)
        account_move.post()
        return account_move

    def iva2(self):
        ret_lines = self.env['ret.ret.lines'].search([('move_id','=',self.id)])
        retention = ret_lines.ret_id.filtered(lambda r: r.ret_type == 'IVA')
        action = {
            'name': _('Retention'),
            'type': 'ir.actions.act_window',
            'res_model': 'retention.retentions',
        }
        if len(retention) ==1:
            action.update({
                'view_mode': 'form',
                'res_id': retention.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', retention.ids)],
            })
        return action

    def islr2(self):
        ret_lines = self.env['ret.ret.lines'].search([('move_id', '=', self.id)])
        retention = ret_lines.ret_id.filtered(lambda r: r.ret_type == 'ISLR')
        action = {
            'name': _('Retention'),
            'type': 'ir.actions.act_window',
            'res_model': 'retention.retentions',
        }
        if len(retention) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': retention.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', retention.ids)],
            })
        return action


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    # concept_code = fields.Many2one("retention.islr.concept", string="Concept Code",default=lambda self: self.env[
    #                                    'retention.islr.concept'].search([('concept_code', '=', '0')],limit=1))

    concept_code = fields.Many2one("retention.islr.concept", string="Concept Code", )
    ret_line_ref = fields.Many2one('ret.ret.lines', string="Model")


    islr_retention_line_status = fields.Selection(selection=[
        ('not_created', 'ISLR Not created'),
        ('created', 'ISLR Created'),
        ('not_applied', 'ISLR Not applicable'),
        ('insert_islr', 'Insert ISLR'),
    ], string='ISLR retention status ', required=True, readonly=True, copy=False, tracking=True,
        default='insert_islr')
    retention_line_boolean = fields.Boolean('Show retention iva %', default=False, compute='onchange_vendor_id')

    @api.onchange('concept_code')
    def onchange_concept_code(self):
        zero_concept_id = self.env['retention.islr.concept'].search([('concept_code', '=', '0')], limit=1)
        if self.concept_code.id and self.concept_code.id == zero_concept_id.id:
            self.islr_retention_line_status = 'not_applied'
        if self.concept_code.id and self.concept_code.id != zero_concept_id.id:
            self.islr_retention_line_status = 'not_created'

    @api.onchange('tax_ids')
    def onchange_set_concept_code(self):
        zero_concept_id = self.env['retention.islr.concept'].search([('concept_code', '=', '0')], limit=1)
        if not self.tax_ids:
            self.islr_retention_line_status = 'not_applied'
            self.concept_code = zero_concept_id.id
            print("\n\n\n\n islr_retention_line_Status", self.islr_retention_line_status, self)
            self._origin.write({'concept_code':zero_concept_id.id,'islr_retention_line_status' : 'not_applied'})

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMoveLineInherit, self).create(vals_list)
        # res = super(models.Model, self).create(vals_list)
        zero_concept_id = self.env['retention.islr.concept'].search([('concept_code', '=', '0')], limit=1)
        for line in res:
            if line and not line.tax_ids:
                line.islr_retention_line_status = 'not_applied'
                line.concept_code = zero_concept_id.id

        return res


    def write(self, vals_list):
        # # res = super(models.Model, self).write(vals_list)
        zero_concept_id = self.env['retention.islr.concept'].search([('concept_code', '=', '0')], limit=1)
        if vals_list.get('tax_ids', False):
            if vals_list['tax_ids'][0][-1]:
                self.islr_retention_line_status = 'insert_islr'
            else:
                self.islr_retention_line_status = 'not_applied'
                self.concept_code = zero_concept_id.id
            # self.write({'concept_code':zero_concept_id.id,'islr_retention_line_status' : 'not_applied'})
        return super(AccountMoveLineInherit, self).write(vals_list)

        # return super(models.Model, self).write(vals_list)

    def button_insert_concept_code(self):

        view_id = self.env.ref('pragtech_odoo_retentions.insert_concept_code_wizard_view_form', False).id,

        return {
            'name': _("Add Concept Code"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'line.concept.code.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'move_line_id': self.id,

            }
        }



