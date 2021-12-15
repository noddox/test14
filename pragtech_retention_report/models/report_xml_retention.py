from datetime import datetime
from odoo import api, models


class ReporXmlRetention(models.AbstractModel):
    _name = 'report.pragtech_retention_report.retentions_iva_xml_document'
    _description = 'Report XML Retention Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        record = self.env['retention.report.wizard'].browse(docids)
        start_period= record.start_date.strftime('%Y%m')
        end_date = record.end_date
        if not end_date:
            end_date = datetime.now().date()

        domain = [('ret_date', '>=', record.start_date),
                  ('ret_date', '<=', end_date),
                  ('state', '=', 'confirm'),
                  ('ret_type_id.ret_type', '=', 'ISLR'),
                  ('partner_type','=','supplier')]
        retention_recs = self.env['retention.retentions'].sudo().search(domain)
        retention_line_recs = retention_recs.mapped('ret_line_ids')
        company_rec = False
        if retention_line_recs:
            company_rec = retention_recs.mapped('company_id')[0]

        return {
            'doc_ids': docids,
            'doc_model': 'retention.report.wizard',
            'docs': record,
            'start_period': start_period,
            'retention_line_recs': retention_line_recs,
            'vat': company_rec.vat if company_rec else False,
        }