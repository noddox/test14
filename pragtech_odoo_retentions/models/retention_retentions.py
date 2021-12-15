from odoo import fields, models, api, _
import json
from odoo.exceptions import UserError


class RetentionRetions(models.Model):
    _name = 'retention.retentions'
    _description = 'Detailed Retention'
    # _rec_name = "tax_payer_type"

    name = fields.Char(string="Retention ID", default=lambda self: _('New'), required=True, copy=False)
    ret_number = fields.Char(string="Ret. Number", copy=False)
    ret_date = fields.Date(string="Ret.Date", required=True)
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
    ], default='customer', tracking=True, required=True)
    memo = fields.Char(string="Memo")
    partner_id = fields.Many2one('res.partner', string="Vendor/Customer")
    ret_behalf = fields.Boolean('Ret. On Behalf', default=False)
    check_ret = fields.Boolean('Check Retention', default=False)
    ret_type_id = fields.Many2one('ret.type', string="Ret. Type")
    ret_per = fields.Many2one("retention.iva.percentage", string="Ret %", required=True, )
    company_id = fields.Many2one('res.company', string="Company", required="True",
                                 default=lambda self: self.env.user.company_id)
    total_amount = fields.Float(string="Total Ret.Amount", compute="compute_total_ret_amount", store=True)
    ret_line_ids = fields.One2many('ret.ret.lines', 'ret_id', string="Retention Lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, default='draft')
    ret_type = fields.Char(related='ret_type_id.ret_type')
    ret_move_id = fields.Many2one('account.move', string="Ref.Move")

    @api.model
    def create(self, vals):
        # if 'company_id' in vals:
        #     self = self.with_company(vals['company_id'])
        # if vals.get('name', _('New')) == _('New'):

        #     seq_date = None
        if 'ret_date' in vals:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['ret_date']))
            yseq = str(seq_date.year)
            msseq = '{:02d}'.format(seq_date.month)
            mseq = str(msseq)
        if 'ret_type_id' in vals:

            retval = self.env['ret.type'].browse(vals['ret_type_id'])

            if retval:

                if retval.ret_type == "IVA":
                    if vals['partner_type'] == 'supplier':
                        vals['name'] = self.env['ir.sequence'].next_by_code('retention.retentions.iva1',
                                                                            sequence_date=seq_date) or _('New')
                        rt1 = self.env['ir.sequence'].next_by_code('retention.retname.iva')
                        vals['ret_number'] = yseq + mseq + rt1
                    else:
                        vals['name'] = self.env['ir.sequence'].next_by_code('retention.retentions.iva2',
                                                                            sequence_date=seq_date) or _('New')
                else:
                    if vals['partner_type'] == 'supplier':
                        vals['name'] = self.env['ir.sequence'].next_by_code('retention.retentions.islr1',
                                                                            sequence_date=seq_date) or _('New')
                        rt2 = self.env['ir.sequence'].next_by_code('retention.retname.islr')
                        vals['ret_number'] = yseq + mseq + rt2
                    else:
                        vals['name'] = self.env['ir.sequence'].next_by_code('retention.retentions.islr2',
                                                                            sequence_date=seq_date) or _('New')
        vals['check_ret'] = True

        return super(RetentionRetions, self).create(vals)

    def unlink(self):
        for trans in self:
            if trans.ret_move_id:
                raise UserError(_('You can not delete a confirmed retention Transaction'))
        return super(RetentionRetions, self).unlink()

        # return super(TransMaster, self).unlink()

    def action_retention_draft(self):
        self.state = 'draft'

    def action_retention_cancel(self):
        self.ret_move_id.mapped('line_ids').remove_move_reconcile()

        account_entry = self.ret_move_id.id
        journal_entry = self.env['account.move'].sudo().search([('id', '=', account_entry)])
        if len(journal_entry):
            journal_entry.button_cancel()
            journal_entry.line_ids = [(5, 0, 0)]
        if self.ret_type_id.ret_type == 'IVA':
            for lines in self.ret_line_ids:
                lines.move_id.iva_retention_status = 'not_created'
        else:
            for lines in self.ret_line_ids:
                lines.move_id.islr_retention_status = 'not_created'
        self.state = 'cancel'

    def action_retention_confirm(self):
        account_move = self.env['account.move']
        if self.partner_type == 'supplier':
            dbac = self.partner_id.commercial_partner_id.property_account_payable_id.id
            crac = self.ret_type_id.vend_posting_account.id
            line_ids = [
                (0, 0,
                 {'journal_id': self.ret_type_id.journal_id.id, 'partner_id': self.partner_id.commercial_partner_id.id,
                  'account_id': crac,
                  'name': "Ret_ref:-" + self.name,
                  'amount_currency': 0.0, 'credit': self.total_amount}),

            ]
            for lines in self.ret_line_ids:
                if lines.move_id:
                    line_ids.append((0, 0,
                                     {'journal_id': self.ret_type_id.journal_id.id,
                                      'partner_id': self.partner_id.commercial_partner_id.id,
                                      'account_id': dbac,
                                      'name': "Ret_ref:-" + self.name, 'amount_currency': 0.0,
                                      'debit': lines.ret_amount, 'ret_line_ref': lines.id,
                                      }), )

        else:
            crac = self.partner_id.commercial_partner_id.property_account_receivable_id.id
            dbac = self.ret_type_id.cust_posting_account.id
            line_ids = [
                (0, 0,
                 {'journal_id': self.ret_type_id.journal_id.id, 'partner_id': self.partner_id.commercial_partner_id.id,
                  'account_id': dbac,
                  'name': "Ret_ref:-" + self.name, 'amount_currency': 0.0, 'debit': self.total_amount,
                  })
            ]
            for lines in self.ret_line_ids:
                if lines.move_id:
                    line_ids.append((0, 0,
                                     {'journal_id': self.ret_type_id.journal_id.id,
                                      'partner_id': self.partner_id.commercial_partner_id.id,
                                      'account_id': crac, 'name': "Ret_ref:-" + self.name,
                                      'amount_currency': 0.0, 'credit': lines.ret_amount, 'ret_line_ref': lines.id,
                                      }), )

            # new_move = move_id.create_journal_iv_islr(self.total_amount, self.ret_type_id.cust_posting_account,
            #                                           self.partner_id.commercial_partner_id.property_account_receivable_id,
            #                                           self.ret_type_id.journal_id, "test", self.ret_date,
            #                                           self.partner_id.commercial_partner_id.id)

        # line_ids = [
        #         (0, 0,
        #          {'journal_id': self.ret_type_id.journal_id.id, 'partner_id': self.partner_id.commercial_partner_id.id, 'account_id': crac,
        #           'name': "Ret_ref:-"+self.name,
        #           'amount_currency': 0.0, 'credit': self.total_amount}),
        #         (0, 0, {'journal_id': self.ret_type_id.journal_id.id, 'partner_id': self.partner_id.commercial_partner_id.id, 'account_id': dbac,
        #                 'name': "Ret_ref:-"+self.name, 'amount_currency': 0.0, 'debit': self.total_amount,
        #                 })
        #     ]

        vals = {
            'journal_id': self.ret_type_id.journal_id.id,
            'ref': "Ret_ref:-" + self.name,
            'narration': "Ret_ref" + self.name,
            'date': self.ret_date,
            'line_ids': line_ids,
        }
        if self.ret_move_id:
            self.ret_move_id.line_ids = line_ids
            self.ret_move_id.action_post()
        else:
            account_move = self.env['account.move'].sudo().create(vals)
            print("MOVEEEEEEE", account_move)
            account_move.action_post()
            print("account move stat", account_move.state)
            self.ret_move_id = account_move.id

        for lines in self.ret_line_ids:
            print("LINE", lines)
            for ls in account_move.line_ids:
                print("LS", ls.ret_line_ref)

            ret_pay_line = account_move.line_ids \
                .filtered(lambda line: (line.account_id.user_type_id.type in (
                'receivable', 'payable') and line.ret_line_ref.id == lines.id))
            move_pay_line = lines.move_id.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            #print("ret pay line", ret_pay_line, "mphhkjb", move_pay_line)
            # errrr
            (ret_pay_line + move_pay_line).reconcile()
            if self.ret_type_id.ret_type == 'IVA':
                lines.move_id.iva_retention_status = 'created'
            else:
                lines.move_id.islr_retention_status = 'created'

        self.state = 'confirm'

    # new_pay_term_lines = account_move.line_ids \
    #         .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
    # inv_pay_term_lines = self.env['account.move.line']
    # for lines in self.ret_line_ids:
    #     if lines.move_id:
    #
    #             inv_pay_term_lines += lines.move_id.line_ids \
    #         .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
    #             if self.ret_type_id.ret_type == 'IVA':
    #                 lines.move_id.iva_retention_status = 'created'
    #             else:
    #                 lines.move_id.islr_retention_status = 'created'

    # (new_pay_term_lines + inv_pay_term_lines).reconcile()
    # self.state = 'confirm'
    # self.ret_move_id = account_move.id

    @api.depends('ret_line_ids')
    def compute_total_ret_amount(self):
        for vals in self:
            vals.total_amount = sum(vals.ret_line_ids.mapped('ret_amount'))
            print("in compute", vals.total_amount)

    @api.onchange('partner_id')
    def onchange_concept_code(self):
        if self.partner_id:
            if self.partner_type == 'customer':
                if self.company_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
                    self.ret_per = self.company_id.retention_iva_percentage_id.id
            elif self.partner_type == 'supplier':
                if self.partner_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
                    self.ret_per = self.partner_id.retention_iva_percentage_id.id

    @api.depends('ret_per')
    def onchange_ret_per(self):
        if self.state == 'draft':
            self.ret_line_ids.ret_percent = self.ret_per.ret_value

    @api.onchange('ret_type_id','partner_id')
    def onchange_ret_type_id(self):
        if self.ret_line_ids:
            self.ret_line_ids = [(5, 0, 0)]


class RetentionRetentionsLines(models.Model):
    _name = 'ret.ret.lines'
    _description = "Retention Lines"

    ret_date = fields.Date(string="Date")
    move_id = fields.Many2one('account.move', string="Invoice")
    ctrl_num = fields.Char(related='move_id.cnt_num')
    taxed_amount = fields.Float(string="Taxable Amount", compute='compute_tax')
    tax_amount = fields.Float(string="IVA Tax Amount", compute='compute_tax')
    ret_percent = fields.Float(string="Ret.%", compute='compute_ret_percentage')
    # ret_percent =fields.Many2one("retention.iva.percentage", string="Ret%", required=True)
    ret_amount = fields.Float(string="Ret.Amount", compute='compute_ret_amount', )
    ret_id = fields.Many2one('retention.retentions', string="Retention")
    code_id = fields.Many2one('retention.islr.concept', string="Concept Code")
    sub_amount = fields.Float(string="Subtract Amt")
    partner_id = fields.Many2one('res.partner', related='ret_id.partner_id')
    domain_new = fields.Char(string="domain", compute='compute_move_id_domain')
    move_line_id = fields.Many2one('account.move.line', string="Invoice Lines")
    ret_percentage = fields.Many2one("retention.islr.percentage", string="Retention Percent")
    sw_has_subtract = fields.Float(string='Has Subtract')
    ret_behalf = fields.Boolean('Ret. On Behalf', default=False, related='ret_id.ret_behalf')
    ret_behalf_partner = fields.Many2one('res.partner', string="Ret on behalf of:")

    @api.depends('ret_id.partner_id')
    def compute_move_id_domain(self):
        for vals in self:
            if vals.ret_id:
                if not vals.ret_id.ret_type_id:
                    raise UserError("Select retention Type")
                if vals.ret_id.partner_id:
                    if vals.ret_id.partner_id.supplier_rank >= 1:
                        vals.domain_new = json.dumps(
                            [('move_type', '=', 'in_invoice'), ('partner_id', '=', vals.ret_id.partner_id.id)])
                        if vals.ret_id.ret_type_id:
                            if vals.ret_id.ret_type_id.ret_type == 'IVA':
                                vals.domain_new = json.dumps(
                                    [('move_type', '=', 'in_invoice'), ('partner_id', '=', vals.ret_id.partner_id.id),
                                     ('iva_retention_status', '!=', 'created')])
                    else:
                        vals.domain_new = json.dumps(
                            [('move_type', '=', 'out_invoice'), ('partner_id', '=', vals.ret_id.partner_id.id)])
                else:
                    vals.domain_new = json.dumps([('move_type', 'in', ('out_invoice', 'in_invoice'))])
            else:
                vals.domain_new = json.dumps([('move_type', 'in', ('out_invoice', 'in_invoice'))])

    @api.depends('move_id', 'move_line_id')
    def compute_tax(self):
        for vals in self:
            vals.tax_amount = 0.0
            vals.taxed_amount = 0.0
            if vals.move_id:
                if vals.ret_id.ret_type_id.ret_type == 'IVA':
                    vals.taxed_amount = sum(
                        vals.move_id.invoice_line_ids.filtered(lambda x: x.tax_ids).mapped('price_subtotal'))
                    vals.tax_amount = sum(vals.move_id.invoice_line_ids.mapped('price_total')) - sum(
                        vals.move_id.invoice_line_ids.mapped('price_subtotal'))

            if vals.move_line_id:
                if vals.ret_id.ret_type_id.ret_type == 'ISLR':
                    vals.taxed_amount = vals.move_line_id.price_subtotal
                    vals.tax_amount = vals.move_line_id.price_total - vals.move_line_id.price_subtotal

    # @api.depends('move_line_id')
    # def onchange_move_line_id(self):
    #     for vals in self:
    #         if vals.move_line_id:

    @api.depends('ret_percent', 'tax_amount')
    def compute_ret_amount(self):
        print("inside compute_ret_amount")
        for vals in self:
            print(vals.ret_id, vals.ret_percent, vals.tax_amount)
            if vals.ret_percent > 0 and vals.tax_amount > 0:
                if vals.ret_id.ret_type_id.ret_type == 'IVA':
                    print("tax amount", vals.tax_amount, "taxed_amount", vals.taxed_amount)
                    vals.ret_amount = (vals.tax_amount * vals.ret_percent) / 100
                    print("ret amount", vals.ret_amount)
                if vals.ret_id.ret_type_id.ret_type == 'ISLR':
                    islr_factor = self.env['retention.islr.factor'].search([('init_date', '<', vals.ret_id.ret_date),
                                                                            ('end_date', '>', vals.ret_id.ret_date)],
                                                                           order='id desc')[0]
                    tax_unit = self.env['tax.unit'].search([('init_date', '<', vals.ret_id.ret_date),
                                                            ('end_date', '>', vals.ret_id.ret_date)], order='id desc')[
                        0]
                    if vals.ret_percent:
                        islr_retention_ammount = (vals.taxed_amount * vals.ret_percent) / 100
                        sw_has_subtract = vals.sw_has_subtract
                        subtract_amount = 0
                        if islr_factor and tax_unit:
                            subtract_amount = (
                                                      sw_has_subtract * vals.ret_percent * islr_factor.factor_value * tax_unit.tax_unit_amount) / 100
                        vals.sub_amount = subtract_amount
                        vals.ret_amount = islr_retention_ammount - subtract_amount




            else:
                vals.ret_amount = 0.0

    @api.depends('ret_id.partner_id', 'ret_id.ret_type_id', 'code_id', 'ret_id.ret_per')
    def compute_ret_percentage(self):
        for vals in self:
            vals.ret_percent = 0.0
            if vals.ret_id.ret_type_id.ret_type == 'IVA':
                vals.ret_percent = vals.ret_id.ret_per.ret_value
                # if vals.ret_id.partner_type == 'supplier':
                #     if vals.partner_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
                #         # vals.write({
                #         #     'ret_percent': vals.partner_id.retention_iva_percentage_id.ret_value
                #         # })
                #         vals.ret_percent = vals.partner_id.retention_iva_percentage_id.ret_value
                # else:
                #     if vals.ret_id.company_id.tax_payer_type_id.tax_payer_type == 'Contribuyente Especial':
                #         # vals.write({
                #         #     'ret_percent': vals.partner_id.retention_iva_percentage_id.ret_value
                #         # })
                #         vals.ret_percent = vals.ret_id.company_id.retention_iva_percentage_id.ret_value

            if vals.ret_id.ret_type_id.ret_type == 'ISLR':
                if vals.ret_id.partner_type == 'supplier':
                    ret_percentage = self.env['retention.islr.percentage'].search(
                        [('person_type_code', '=', vals.partner_id.person_type_code_id.id),
                         ('concept_code', '=', vals.code_id.id)], limit=1)
                    if ret_percentage:
                        vals.ret_percent = ret_percentage.ret_percentage
                        vals.sw_has_subtract = ret_percentage.sw_has_subtract
                        print("calculate", vals.sw_has_subtract)
                else:
                    ret_percentage = self.env['retention.islr.percentage'].search(
                        [('person_type_code', '=', vals.ret_id.company_id.person_type_name.id),
                         ('concept_code', '=', vals.code_id.id)], limit=1)
                    if ret_percentage:
                        vals.ret_percent = ret_percentage.ret_percentage
                        vals.sw_has_subtract = ret_percentage.sw_has_subtract

    def get_tax_percentage(self):
        for line in self:
            invoice_lines = line.move_id.invoice_line_ids.filtered(lambda l: l.tax_ids)
            if invoice_lines:
                return invoice_lines[0].tax_ids[0].amount
