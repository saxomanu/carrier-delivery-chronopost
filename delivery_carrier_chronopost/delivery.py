##############################################################################
#
#    Author: Florian da Costa
#    Copyright (C) 2014-2015 Akretion (http://www.akretion.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class DeliveryCarrier(models.Model):
    """ Add service group """
    _inherit = 'delivery.carrier'

    def _selection_carrier_type(self):
        """ Add Chronopost carrier type """
        res = super(DeliveryCarrier, self)._selection_carrier_type()
        res.append(('chronopost', 'Chronopost'))
        return res


CHRONOPOST_OPTIONS_TYPES = [
    ('service', 'Service'),
    ('object_type', 'Type of product'),
    ('insurance', 'Insurance'),
    ('shipper_alert', 'Shipper Alert'),
    ('recipient_alert', 'Recipient Alert'),
]


class DeliveryCarrierTemplateOption(models.Model):
    """ Set name translatable and add service group """
    _inherit = 'delivery.carrier.template.option'

    chronopost_type = fields.Selection(
            CHRONOPOST_OPTIONS_TYPES,
            string="Chronopost option type") 