from odoo import api, fields, models
from chronopost_api.chronopost import Chronopost
from odoo import exceptions
from chronopost_api.exception_helper import (
    InvalidSize,
    InvalidType,
    InvalidValueNotInList,
    InvalidMissingField,
    )
import logging

_logger = logging.getLogger(__name__)



class ShippingLabel(models.Model):

    _inherit = 'shipping.label'

    @api.model
    def _get_file_type_selection(self):
        """ To inherit to add file type """
        res = super(ShippingLabel, self)._get_file_type_selection()
        res.append(('zpl', 'ZPL'))
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            company = rec.company_id
            if company.chronopost_account_ids:
                chrono_config = company.chronopost_account_ids[0]
            else:
                raise exceptions.except_orm(
                    _('Error'),
                    _("You have to configurate a chronopost account "
                      "for your company"))

            trackNumber = ""
            if rec.package_id:
                trackNumber = rec.package_id.parcel_tracking
            else:
                pick = self.env['stock.picking'].browse(rec.res_id)
                if pick:
                    trackNumber = pick.parcel_tracking
            if trackNumber:
                try:
                    resp = Chronopost(service='cancel').cancel_label(
                        chrono_config.account_id.account,
                        chrono_config.account_id.password,
                        trackNumber)
                except (InvalidSize,
                        InvalidType,
                        InvalidValueNotInList,
                        InvalidMissingField) as e:
                    raise exceptions.except_orm('Error', e.message)
                label = resp['value']
                _logger.info("Retour API %r" % label)
                if label['errorCode'] != 0:
                    try:
                        error = ''.join(label['errorMessage'])
                    except:
                        error = str(label['errorCode'])
                    raise exceptions.except_orm('Webservice Error', error)
        return super(ShippingLabel, self).unlink()
