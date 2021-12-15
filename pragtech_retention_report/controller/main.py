import json
from odoo import http
from odoo.http import request, content_disposition


class DownloadRetentionReport(http.Controller):

    @http.route('/web/download/retention/report/<model("retention.retentions"):retentions>', type='http', auth='user')
    def download_retention_report(self, retentions, **kw):
        if not retentions:
            return None
        report_name = False
        if retentions.ret_type_id.ret_type == 'IVA':
            pdf, _ = request.env.ref('pragtech_retention_report.action_report_retentions_iva').sudo()._render_qweb_pdf([retentions.id])
            report_name = '%s - IVA.pdf' % retentions.name
        if retentions.ret_type_id.ret_type == 'ISLR':
            pdf, _ = request.env.ref('pragtech_retention_report.action_report_retentions_islr_detail').sudo()._render_qweb_pdf([retentions.id])
            report_name = '%s - IVA.pdf' % retentions.name
        if report_name:
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),('Content-Disposition', content_disposition(report_name))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        return None

    @http.route('/web/download/retention/txt/report', type='http', auth='user')
    def download_retention_txt_report(self, retention_ids, **kw):
        retention_ids = json.loads(retention_ids)
        report_name = "IVA Retention.txt"
        text_data, _ = request.env.ref('pragtech_retention_report.action_txt_report_retentions').sudo()._render_qweb_text(retention_ids)
        texthttpheaders = [('Content-Type', 'text/plain'), ('Content-Length', len(text_data)),('Content-Disposition', content_disposition(report_name))]
        temp_data = text_data.decode()
        data=temp_data.replace(',','')
        text_data = data.encode()
        return request.make_response(text_data, headers=texthttpheaders)

    @http.route('/web/download/retention/xml/report', type='http', auth='user')
    def download_retention_xml_report(self, wizard_id, **kw):
        wizard_id = json.loads(wizard_id)
        report_name = "ISLR Retention.xml"
        xml_data, _ = request.env.ref('pragtech_retention_report.action_xml_report_retentions').sudo()._render_qweb_text(wizard_id)
        xmlhttpheaders = [('Content-Type', 'application/xml'), ('Content-Length', len(xml_data)),('Content-Disposition', content_disposition(report_name))]
        temp_data = xml_data.decode()
        data = temp_data.replace(',', '')
        xml_data = data.encode()
        return request.make_response(xml_data, headers=xmlhttpheaders)
