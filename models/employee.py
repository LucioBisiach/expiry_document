# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


import logging
_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = 'hr.employee'

    expiry_count = fields.Integer(compute='_expiry_count', string='# Vencimientos')



    def act_show_expiry(self):
        self.ensure_one()
        domain = [
            ('employee', '=', self.id)]
        return {
            'name': _('Vencimientos'),
            'domain': domain,
            'res_model': 'expiry.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Clickear para crear un nuevo Vencimiento
                        </p>'''),
            'limit': 80,
            'context': "{'default_employee': '%s'}" % self.id
        }
