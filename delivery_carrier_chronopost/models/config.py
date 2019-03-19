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


from odoo import models, fields, api


class CarrierAccount(models.Model):
    _inherit = 'carrier.account'

    def _selection_carrier_type(self):
        """ To inherit to add carrier type like Chronopost, Postlogistics..."""
        res = super(CarrierAccount, self)._selection_carrier_type()
        res.append(('chronopost', 'Chronopost'))
        return res

    def _selection_file_format(self):
        """ To inherit to add carrier type like Chronopost, Postlogistics..."""
        res = super(CarrierAccount, self)._selection_file_format()
        res.extend((('SPD', 'SPD'),
                   ('PPR', 'PPR'),
                   ('THE', 'THE')))
        return res


class ChronopostAccount(models.Model):
    _name = 'chronopost.account'
    _description = 'Chronopost Account'
    _inherits = {'carrier.account': 'account_id'}
    _rec_name = 'account_id'
    
    account_id = fields.Many2one('carrier.account', 'Main Account',
            ondelete="cascade", required=True)
    sub_account = fields.Char('Sub Account Number', size=3)
    company_id = fields.Many2one('res.company', 'Company')
    use_esd = fields.Boolean('Use ESD')
 
#class ChronopostConfig(orm.Model):
#    _name = 'chronopost.config'
#    _inherit = ['res.config.settings', 'abstract.config.settings']
#    _prefix = 'chronopost_'
#    _companyObject = ResCompany
