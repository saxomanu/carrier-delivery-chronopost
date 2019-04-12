# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 201 Ezytail
#    @author Emmanuel HURET <huret.emmanuel@infoatoutprix.fr>
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
###############################################################################


{
    'name': 'Direct print label',
    'version': '0.1',
    'author': "Ezytail",
    'maintener': 'Ezytail',
    'category': 'Warehouse',
    'summary': "Direct print label",
    'description': """
Direct print label
=============================================


Implémentation de l'impression du bon de livraison + etiquettes de transport

""",
    'website': 'http://www.ezytail.com/',
    'depends': [
        'base_delivery_carrier_label',
        'base_report_to_printer',
    ],
    'data': [
        'views/stock_picking_views.xml',
        'datas/report.xml',
    ],

    'license': 'AGPL-3',
    'installable': True,

}
