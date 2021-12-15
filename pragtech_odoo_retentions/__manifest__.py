{
    'name': 'Odoo Retentions',
    'version': '14.2.0',
    'category': 'Invoicing',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'depends': ['sale','account', 'web_domain_field'],
    'summary': 'A Retention, like a Payment, it is a instrument than affect the Due Balance of a Invoice / Bill.',
    'description': '''

''',
    'data': [
        # 'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/concept_code_data.xml',

        'views/res_company_view.xml',
        'views/res_user_view.xml',
        # 'views/account_retention_view.xml',
        'views/retention_view.xml',
        'views/retention_configuration_view.xml',
        'views/tax_unit_view.xml',
        'views/retention_islr_percentage_views.xml',
        'views/account_retention_view.xml',
        'views/res_partner_view.xml',
        'views/account_move.xml',
        'wizard/iva_retention_wizard_view.xml',
        'wizard/line_concept_code_wizard_view.xml',
        'wizard/invoice_move_wizard.xml',
        'views/retention_detailed_views.xml',

    ],

    'license': 'OPL-1',
    'currency': 'USD',
    'price': '',
    'installable': True,
    'auto_install': False,
}
