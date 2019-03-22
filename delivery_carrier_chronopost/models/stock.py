# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright (C) 2013-2015 Akretion (http://www.akretion.com)
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

from odoo import models, fields, api, _
from odoo import exceptions
from chronopost_api.chronopost import Chronopost
from datetime import datetime
from chronopost_api.exception_helper import (
    InvalidSize,
    InvalidType,
    InvalidValueNotInList,
    InvalidMissingField,
    )

import base64
import logging

_logger = logging.getLogger(__name__)


def map_exception_msg(message):
    model_mapping = {
        'skybill': 'Stock Tracking or Carrier',
        'ref': 'Stock Picking',
        'esd': 'Carrier Tracking',
        'address': 'Partner / Customer',
        'header': 'Chronopost account',
    }
    for key, val in model_mapping.items():
        message = message.replace('(model: ' + key, '\n(check model: ' + val)
    return message


class ChronopostPrepareWebservice(models.AbstractModel):
    _name = 'chronopost.prepare.webservice'

    _CHRONOPOST_PRODUCT = {
        'ch8': '75',
        'ch9': '76',
        'ch10': '02',
        'ch13': '01',
        'ch13is': '1S',
        'ch18': '16',
        'chexp': '17',
        'chcla': '44',
        'chrel': '86'
    }

    def _prepare_address(self, partner):
        address = {}
        elms = ['street', 'street2', 'zip', 'city', 'phone', 'mobile', 'email']
        for elm in elms:
            if (elm == 'phone' or elm == 'mobile') and getattr(partner, elm):
                address[elm] = getattr(partner, elm).replace(' ', '')
                # We should check this properly, but it seems chronopost
                # do not consider mobile phone. So if we give just the mobile
                # and not the phone field, then they do not have any phone
                # number. In this case, out the mobile in phone field.
                if elm == 'mobile' and not address.get('phone', False):
                    address['phone'] = getattr(partner, elm).replace(' ', '')
            else:
                address[elm] = getattr(partner, elm)
            if partner.country_id:
                address['country_code'] = partner.country_id.code
                address['country_name'] = partner.country_id.name
        return address

    def _prepare_recipient(self, picking):
        partner = picking.partner_id
        recipient_data = self._prepare_address(partner)
        recipient_data['name2'] = partner.name
        if partner.is_company and partner.child_ids:
            recipient_data['name'] = partner.child_ids[0].name
        else:
            recipient_data['name'] = ' '
        recipient_data['alert'] = int(self._get_single_option(
                                      picking, 'recipient_alert') or 0)
        return recipient_data

    def _prepare_shipper(self, picking):
        partner = picking._get_label_sender_address()
        shipper_data = self._prepare_address(partner)
        if partner.parent_id:
            shipper_data['name'] = partner.name
            shipper_data['name2'] = partner.parent_id.name
        else:
            shipper_data['name'] = ' '
            shipper_data['name2'] = partner.name
        shipper_data['civility'] = 'E'  # FIXME
        shipper_data['alert'] = int(self._get_single_option(
            picking, 'shipper_alert') or 0)
        return shipper_data

    def _prepare_customer(self, picking):
        """
        Use this method in case the shipper address is different
        from the customer address
        """
        return None

    def _prepare_basic_ref(self, picking):
        ref_data = {
            'shipperRef': picking.name,
            #TODO in the 'recipientRef' field, we are suppose to write
            # the code of the "point relais" if we deliver to a point relais
            'recipientRef': picking.partner_id.commercial_partner_id.ref
            or picking.partner_id.commercial_partner_id.name[:35],
        }
        return ref_data

    def _get_single_option(self, picking, option):
        option = [opt.code for opt in picking.option_ids
                  if opt.chronopost_type == option]
        assert len(option) <= 1
        return option and option[0]

    def _complete_skybill(self, weight, moves, rank):
        res = {}
        picking = moves[0].picking_id
        res['weight'] = weight
        product_total = int(sum(
            m.procurement_id.sale_line_id.price_subtotal if m.procurement_id.sale_line_id
            else 0 for m in moves)
            * 100)
        res['skybillRank'] = str(rank)
        if self._get_single_option(picking, 'insurance'):
            res['insuredValue'] = product_total or None
        if picking.carrier_id.name == "Chrono Express":
            res['customsValue'] = product_total or None
        return res

    def _prepare_basic_skybill(self, picking, options):
        skybill_data = {
            'productCode': self._CHRONOPOST_PRODUCT[picking.carrier_id.code],
            'shipDate': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            'shipHour': datetime.now().strftime("%H"),
            'weightUnit': 'KGM',
            #'codValue': TODO
        }
        skybill_data['bulkNumber'] = str(picking.number_of_packages)
        skybill_data['service'] = self._get_single_option(
            picking, 'service') or '0'
        skybill_data['objectType'] = self._get_single_option(
            picking, 'object_type') or 'MAR'
        return skybill_data

    def _prepare_esd(self, track):
        # TODO
        esd_data = {
            'height': 0,
            'width': 0,
            'length': 0,
            }
        return esd_data

    def _prepare_account(self, chrono_config, picking):

        sub_account = chrono_config.sub_account or False
        account = chrono_config.account_id.account
        password = chrono_config.account_id.password
        mode = chrono_config.account_id.file_format or False
        name = chrono_config.account_id.name

        header_data = {
            'accountNumber': account,
            'subAccount': sub_account,
        }
        #context['chrono_account_name'] = name
        return header_data, password, mode

    def get_chronopost_account(self, company, pick):
        """
            If your company use more than one chronopost account, implement
            your method to return the right one depending of your picking.
        """
        return NotImplementedError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _generate_chronopost_label(self, picking, package_ids=None):
        """ Generate labels and write tracking numbers received """
        chronopost_obj = self.env['chronopost.prepare.webservice']
        company = picking.company_id
        options = [o.tmpl_option_id.name for o in picking.option_ids]
        if company.chronopost_account_ids:
            if len(company.chronopost_account_ids) == 1:
                chrono_config = company.chronopost_account_ids[0]
            else:
                chrono_config = chronopost_obj.get_chronopost_account(company, picking)
        else:
            raise exceptions.except_orm(
                _('Error'),
                _("You have to configurate a chronopost account "
                  "for your company"))

        if not package_ids:
            package_label_ids = self.pack_operation_product_ids.mapped('result_package_id')
        else:
            package_label_ids = self.pack_operation_product_ids.mapped('result_package_id').filtered(lambda r: r.id in package_ids.ids)

        nb_colis = len(package_label_ids)
        if nb_colis != 0:
            self.number_of_packages = nb_colis
        else:
            self.number_of_packages = 1



        #get options
        if picking.option_ids:
            options = [o.tmpl_option_id.name for o in picking.option_ids]
        #prepare webservice datas
        recipient_data = chronopost_obj._prepare_recipient(picking)
        customer_data = chronopost_obj._prepare_customer(picking)

        header_data, password, mode = chronopost_obj._prepare_account(
            chrono_config, picking)
        shipper_data = chronopost_obj._prepare_shipper(picking)

        ref_data = chronopost_obj._prepare_basic_ref(picking)
        skybill_data = chronopost_obj._prepare_basic_skybill(picking, options)
        labels = []

        if not package_label_ids:
            moves = [move for move in picking.move_lines]
            skybill_data.update(chronopost_obj._complete_skybill(picking.shipping_weight, moves, 1))
            if chrono_config.use_esd:
                esd_data = chronopost_obj._prepare_esd(moves)
            else:
                esd_data = None
            try:
                resp = Chronopost().get_shipping_label(
                    recipient_data, shipper_data,
                    header_data, ref_data, skybill_data, password,
                    esd=esd_data, mode=mode, customer=customer_data)
            except (InvalidSize,
                    InvalidType,
                    InvalidValueNotInList,
                    InvalidMissingField) as e:
                msg = map_exception_msg(e.message)
                raise exceptions.except_orm('Error', msg)
            label = resp['value']
            _logger.info("Retour API %r" % label)
            if label['errorCode'] != 0:
                try:
                    error = ''.join(label['errorMessage'])
                except:
                    error = str(label['errorCode'])
                raise exceptions.except_orm('Webservice Error', error)

            # copy tracking number on picking if only one pack or
            # in tracking if several packs
            tracking_number = label['skybillNumber']
            self.carrier_tracking_ref = tracking_number

            file_type = 'pdf' if mode != 'ZPL' else 'zpl'
            labels.append({
                'file': base64.b64decode(label['skybill']),
                'package_id': False,
                'file_type': file_type,
                'name': tracking_number + '.' + file_type,
            })
        rank = 0
        for pack in package_label_ids:
            rank += 1
            moves = self.pack_operation_product_ids.filtered(lambda r: r.result_package_id.id == pack.id).mapped('linked_move_operation_ids.move_id')
            skybill_data.update(chronopost_obj._complete_skybill(pack.shipping_weight, moves, rank))
            if chrono_config.use_esd:
                esd_data = chronopost_obj._prepare_esd(moves)
            else:
                esd_data = None
            try:
                resp = Chronopost().get_shipping_label(
                    recipient_data, shipper_data,
                    header_data, ref_data, skybill_data, password,
                    esd=esd_data, mode=mode, customer=customer_data)
            except (InvalidSize,
                    InvalidType,
                    InvalidValueNotInList,
                    InvalidMissingField) as e:
                msg = map_exception_msg(e.message)
                raise exceptions.except_orm('Error', msg)
            label = resp['value']
            _logger.info("Retour API %r" % label)
            if label['errorCode'] != 0:
                try:
                    error = ''.join(label['errorMessage'])
                except:
                    error = str(label['errorCode'])
                raise exceptions.except_orm('Webservice Error', error)

            # copy tracking number on picking if only one pack or
            # in tracking if several packs
            tracking_number = label['skybillNumber']
            pack.parcel_tracking = tracking_number

            file_type = 'pdf' if mode != 'ZPL' else 'zpl'
            labels.append({
                'file': base64.b64decode(label['skybill']),
                'package_id': pack.id,
                'file_type': file_type,
                'name': tracking_number + '.' + file_type,
            })
            
        return labels

    def generate_shipping_labels(self, package_ids=None):
        """ Add label generation for Chronopost """
        self.ensure_one()

        picking = self

        if picking.carrier_id and picking.carrier_id.carrier_type == 'chronopost':
            return self._generate_chronopost_label(picking, package_ids=package_ids)
        return super(StockPicking, self).generate_shipping_labels(package_ids=package_ids)


class ShippingLabel(models.Model):
    """ Child class of ir attachment to identify which are labels """
    _inherit = 'shipping.label'

    def _get_file_type_selection(self):
        """ Return a concatenated list of extensions of label file format
        plus file format from super

        This will be filtered and sorted in __get_file_type_selection

        :return: list of tuple (code, name)

        """
        file_types = super(ShippingLabel, self)._get_file_type_selection()
        new_types = [('zpl', 'ZPL')]
        file_types.extend(new_types)
        return file_types
