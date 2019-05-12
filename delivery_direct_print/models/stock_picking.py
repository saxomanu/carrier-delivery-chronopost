# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class Report(models.Model):
    _inherit = 'report'

    @api.model
    def get_label(self, docids, report_name):
        """ Generate a PDF and returns it.
        If the action configured on the report is server, it prints the
        generated document as well.
        """
        labels = self.env['shipping.label'].search([
            ('res_id', 'in', docids),
            ('res_model', '=', 'stock.picking')])
        document = ""
        for label in labels:
            document += label.datas.decode('base64')

        report = self._get_report_from_name(report_name)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']
        can_print_report = self._can_print_report(behaviour, printer, document)

        if can_print_report:
            printer.print_document(report_name, document, report.report_type)

        return document


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_label(self):
        # report = self.env['report']
        # report.get_pdf(self.ids, 'tevah_stock_reports.report_delivery_bl_client_jsi')
        # report.get_label(self.ids, 'stock.report_ship_label')
        labels = self.env['shipping.label'].search([
            ('res_id', 'in', self.ids),
            ('res_model', '=', 'stock.picking')])
        document = ""
        for label in labels:
            if label.datas:
                _logger.info(label.with_context(bin_size=False).datas)
                _logger.info(label.with_context(bin_size=False).datas.decode('base64'))
                document += label.datas.decode('base64')
        for rec in self:
            rec.label_zpl = document

    label_zpl = fields.Text(compute='_get_label')

    @api.multi
    def print_delivery(self):
        # report = self.env['report']
        # report.get_pdf(self.ids, 'tevah_stock_reports.report_delivery_bl_client_jsi')
        # report.get_label(self.ids, 'stock.report_ship_label')
        labels = self.env['shipping.label'].search([
            ('res_id', 'in', self.ids),
            ('res_model', '=', 'stock.picking')])
        document = ""
        for label in labels:
            document += label.datas.decode('base64')
        return document
