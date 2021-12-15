from odoo import fields, models, api,_
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta


class OdooTaxPayerType(models.Model):
    _name = 'tax.payer.type'
    _description = 'Tax Payer Type'
    _rec_name = "tax_payer_type"


    tax_payer_type = fields.Char(string='Name')


class OdooRetentionIvaPercentage(models.Model):
    _name = 'retention.iva.percentage'
    _description = 'Retention IVA Percentage'
    _rec_name = "ret_percentage"

    # amount_mva = fields.Float(string='IVA Percent', digits=0, required=True,
    #                           help="", default=0)
    ret_percentage = fields.Char(string='IVA Percent', digits=0, required=True,
                              help="", default=0)
    ret_value = fields.Float(string='IVA Percent Value',
                                  help="", default=0)


class OdooTaxUnit(models.Model):
    _name = 'tax.unit'
    _description = 'Tax Unit'
    _rec_name = "tax_unit_amount"

    type = fields.Char( string="Type")
    init_date = fields.Date(string='Start Date', default=date.today(),
                            required=True)
    end_date = fields.Date(string='End Date',default= date.today()+ relativedelta(years=20))
    tax_unit_amount =fields.Float(string='Tax Unit Amount',required=True)
    gov_doc_number = fields.Char('Govt Doc Number')



class OdooRetentionIslrFactor(models.Model):
    _name = 'retention.islr.factor'
    _description = 'Retention ISLR Factor'
    _rec_name = "factor_value"

    init_date = fields.Date(string='Start Date', default=date.today(),
                            required=True)
    factor_value =fields.Float(string='Factor Value')
    end_date = fields.Date(string='End Date',
                           default= date.today()+ relativedelta(years=20)
                           )



class OdooRetentionIslrPersonType(models.Model):
    _name = 'retention.islr.person.type'
    _description = 'Retention ISLR Person Type'
    _rec_name = "name"

    person_type_code = fields.Char(string='Person Type Code')
    name = fields.Char(string='Person Type Name')



class OdooRetentionIslrConcept(models.Model):
    _name = 'retention.islr.concept'
    _description = 'Retention ISLR Concept'
    _rec_name = "name"


    concept_code = fields.Char(string='Concept Code',required=True)
    name = fields.Char(string='Name',required=True)
    name_full = fields.Char(string='Name Full',required=True)
    numeral = fields.Integer(string='Numeral',required=True)
    literal = fields.Integer(string='Literal',required=True)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     res = super(OdooRetentionIslrConcept, self).name_search(name='', args=None, operator='ilike', limit=100)
    #
    #     ids = self.search(args + ['|', ('name', operator, name), ('concept_code', operator, name)], limit=limit)
    #     return ids.name_get()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search((args + ['|', ('concept_code', 'ilike', name), ('name', 'ilike', name)]),
                               limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()




class OdooRetentionIslrPercentage(models.Model):
    _name = 'retention.islr.percentage'
    _description = 'Retention ISLR Percentage'
    _rec_name = "person_type_code"

    person_type_code = fields.Many2one("retention.islr.person.type", string="Person Type Code",required=True)
    concept_code = fields.Many2one("retention.islr.concept", string="Name and Full name",required=True)
    ret_percentage =fields.Float(string='Retention Percentage')
    ret_portion =fields.Float(string='Retention Portion')
    sw_has_subtract = fields.Float(string='Has Subtract')




class OdooRetType(models.Model):
    _name = 'ret.type'
    _description = 'Retention Type'
    _rec_name = "name"

    ret_type = fields.Char(string='Retention Type')
    name = fields.Char(string='Retention Name')
    cust_posting_account = fields.Many2one("account.account", string="Posting Account for Invoices")
    vend_posting_account = fields.Many2one("account.account", string="Posting Account for Bills")
    journal_id = fields.Many2one("account.journal", string="Posting Journal")
    ret_tax_id = fields.Many2one("account.tax", string="Related Tax")





class OdooRetention(models.Model):
    _name = 'invoice.retention'
    _description = 'Retention ISLR Percentage'
    _rec_name = "move_type"

    move_type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt')])
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer/Vendor",
        store=True, readonly=False, ondelete='restrict',
        domain="['|', ('parent_id','=', False), ('is_company','=', True)]",
        check_company=True)
    # payment_type = fields.Selection([
    #     ('outbound', 'Send Money'),
    #     ('inbound', 'Receive Money'),
    # ], string='Payment Type', default='inbound', required=True)
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
    ], default='customer', tracking=True, required=True)
    ret_type = fields.Many2one("ret.type", string="Retention Type")
    ret_date = fields.Date(string='Retention Date', default=date.today(),
                            required=True)
    taxable_amount = fields.Float('Taxable Amount',copy=False)
    tax_amount = fields.Float('Tax Amount',copy=False)

    ret_percentage = fields.Many2one("retention.islr.percentage", string="Retention Percent")
    ret_iva_percentage = fields.Many2one("retention.iva.percentage", string="IVA Retention Percent")

    ret_amount= fields.Float('Retention Amount',copy=False)
    subtract_amount = fields.Float(string='Subtract Amount',default=0)
    net_retention  = fields.Float(string='Net Retention')
    bill_number = fields.Char(string="Bill Number")
    bill_date = fields.Date(string='Bill Date')
    move_ref  = fields.Many2one("account.move", string="Move Ref")


    # @api.depends('is_internal_transfer')
    # def _compute_partner_id(self):
    #     for pay in self:
    #         if pay.is_internal_transfer:
    #             pay.partner_id = pay.journal_id.company_id.partner_id
    #         elif pay.partner_id == pay.journal_id.company_id.partner_id:
    #             pay.partner_id = False
    #         else:
    #             pay.partner_id = pay.partner_id
