# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class expiryDocument(models.Model):
    _name = 'expiry.document'

    name = fields.Char(string="Name", required=True)

    type_expiry = fields.Selection([ 
        ('employee', 'Employee'),
        ('fleet', 'Fleet'),
        ('company', 'Company')], string="Expiry Type", required=True)

    date_stop = fields.Date(string="Next Expiration", readonly=True)
    alert_days = fields.Integer(string="Días de Aviso")
    remaining_days = fields.Integer(string="Remaining Days", readonly=True)

    vehicle = fields.Many2one('fleet.vehicle',string="Vehicle")
    employee = fields.Many2one('hr.employee', string="Employee")

    expiry_ids = fields.One2many('expiry.document.list', 'relation_expiry_document', string="Lista Vencimientos")

class expiryDocumentList(models.Model):
    _name = 'expiry.document.list'

    name = fields.Char(compute="_get_name_and_relationship", string="Nombre")
    relationship = fields.Char(compute="_get_name_and_relationship", string="Relación")
    date_start = fields.Date(string="Fecha de Emisión")
    date_stop = fields.Date(string="Fecha de Vencimiento")
    date_payment = fields.Date(string="Fecha de Pago")
    remaining_days = fields.Integer (compute="_get_remaining_days_and_status", string="Dias Restantes", default=0)
    today = fields.Datetime(compute="_get_today", string="Hoy")

    state = fields.Selection([
        ('sinfecha','Sin Fecha de Vencimiento'),
        ('pendiente','Pendiente'),
        ('proximo','Proximo a Vencer'),
        ('pagado','Pagado'),
        ('vencido','Vencido')], string="Estado", compute="_get_remaining_days_and_status")

    relation_expiry_document = fields.Many2one('expiry.document', invisible=True, string="Relacion")
    rem_pdf = fields.Binary(string="Archivo")
    rem_pdf_filename = fields.Char(string="Nombre")

    def _get_name_and_relationship(self):
        for rec in self:
            rec.name = rec.relation_expiry_document.name
            if rec.relation_expiry_document.type_expiry == 'fleet':
                rec.relationship = rec.relation_expiry_document.vehicle.name
                # _logger.info('HOY %s', self.today)
            else:
                if rec.relation_expiry_document.type_expiry == 'employee':
                    rec.relationship = rec.relation_expiry_document.employee.name
                else:
                    rec.relationship = " "

    @api.depends('date_stop')
    def _get_remaining_days_and_status(self):
        for record in self:
            if record.date_stop:
                date_stop = record.date_stop
                today = datetime.now().strftime('%Y-%m-%d')
                numero_de_dias = (
                        fields.Date.from_string(date_stop) -
                        fields.Date.from_string(today)).days
                if numero_de_dias > 0:
                    record.remaining_days = numero_de_dias
                else:
                    record.remaining_days = numero_de_dias
                if record.date_payment:
                    record.state = 'pagado'
                    record.remaining_days = 0
                else: 
                    if record.remaining_days > record.relation_expiry_document.alert_days:
                        record.state = 'pendiente'
                    else:
                        if record.remaining_days < 0:
                            record.state = 'vencido'
                        else:
                            record.state = 'proximo'
                            
            else:
                record.remaining_days = 0
                record.state = 'sinfecha'

    def _get_today(self):
        today = datetime.now().strftime('%Y-%m-%d')
        # _logger.info("IR CRON %s ", today)
        for rec in self:
            rec.today = today
        

    def mail_reminder(self):
        for i in self:
            #Preguntamos si el estado del vencimiento es proximo("Proximo a Vencer")
            if i.state == 'proximo':
                # Definimos el contenido del mail. y agregamos los campos que queremos que se vean, en este caso seleccionamos el nombre, la fecha, y el nombre del empleado.
                mail_content = "  Hola  " + i.relation_expiry_document.employee.name + ", tu documento " + i.name + " vence el " + \
                                str(i.date_stop) + ". No olvides de renovarlo."
                # Definimos el titulo del mail, quien lo envia, el cuerpo (que lo compleamos anteriormente, y el mail de quien lo va a recibir).
                main_content = {
                    'subject': _('Documento-%s Vence el %s') % (i.name, i.date_stop),
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': i.relation_expiry_document.employee.work_email,
                }
                # Por ultimo, creamos el mail con el contenido definido y se envia.
                self.env['mail.mail'].create(main_content).send()
            else:
                if i.state == 'vencido':
                    mail_content = "  Hola  " + i.relation_expiry_document.employee.name + ", tu documento " + i.name + " venció el " + \
                                    str(i.date_stop) + ". No olvides de renovarlo."
                    main_content = {
                        'subject': _('Documento-%s Vencido %s') % (i.name, i.date_stop),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.relation_expiry_document.employee.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()




    
