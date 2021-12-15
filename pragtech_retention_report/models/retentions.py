from odoo import models


class Retentions(models.Model):
    _inherit = "retention.retentions"

    def print_retention_report(self):
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/download/retention/report/%s'% self.id,
            'target': 'self',
        }
