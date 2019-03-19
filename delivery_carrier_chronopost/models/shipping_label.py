from odoo import api, fields, models


class ShippingLabel(models.Model):

    _inherit = 'shipping.label'
    _description = "Shipping Label"

    @api.model
    def _selection_file_type(self):
        """ To inherit to add file type """
        res = super(ShippingLabel, self)._selection_file_type()
        res.append(('zpl', 'ZPL'))
        return res