{
    'name': "Retention Reports",
    'summary': """
        PDF Reports of retentions.""",
    'description': """
        PDF Reports of retentions.
    """,
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'category': 'Report',
    'version': '14.0.1.4.0',
    'depends': ['pragtech_odoo_retentions', 'report_xml'],
    'data': [
        'security/ir.model.access.csv',
        'data/retention_report_paperformat.xml',
        'wizard/retention_report_wizard_views.xml',
        'views/assets.xml',
        'views/retentions_report_layout.xml',
        'views/retentions_iva_report.xml',
        'views/retentions_views.xml',
        'views/retentions_islr_detail_report.xml',
        'views/retentions_txt_report.xml',
        'views/retentions_iva_xml_report.xml',
    ],
}
