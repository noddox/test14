from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RetentionReportWizard(models.TransientModel):
    _name = "retention.report.wizard"
    _description = "Retention Report Wizard"

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", default=datetime.now().date())
    report_type = fields.Selection([('txt', 'IVA (TXT File)'), ('xml', 'ISLR (XML File)')],
        string="Type", required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_differance(self):
        if self.start_date > self.end_date:
            raise ValidationError(_("Start date can't be greater than end date."))

    def download_retention_report(self):
        if self.report_type == 'xml':
            return {
                'type' : 'ir.actions.act_url',
                'url': '/web/download/retention/xml/report?wizard_id=%s' % self.id,
                'target': 'self',
            }

        if self.report_type == 'txt':
            end_date = self.end_date
            if not end_date:
                end_date = datetime.now().date()

            domain = [('ret_date', '>=', self.start_date),
                      ('ret_date', '<=', end_date),
                      ('state', '=', 'confirm'),
                      ('ret_type_id.ret_type', '=', 'IVA'),
                      ('partner_type','=','supplier')]

            retention_recs = self.env['retention.retentions'].sudo().search(domain)
            return {
                'type' : 'ir.actions.act_url',
                'url': '/web/download/retention/txt/report?retention_ids=%s' % retention_recs.ids,
                'target': 'self',
            }
