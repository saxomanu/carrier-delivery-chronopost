odoo.define('delivery_direct_print.print_label', function (require) {
"use strict";
var form_widget = require('web.form_widgets');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;
var Dialog = require('web.Dialog')

form_widget.WidgetButton.include({
    on_click: function() {
        var self = this;
        var result = self.field_manager.datarecord.label_zpl;
         if(this.node.attrs.custom === "print_label"){
            $.ajax({
                    type: "POST",
                    dataType: "json",
                    url: "http://127.0.0.1:43415/shipping-server/ShippingServer",
                    data: {
                        "method" : "printZPLWithLanPrinter",  
                        "fluxZPL" : result
                    }, success: function(json) {
                        Dialog.confirm(self, ("Impression evoyée à l\'imprimante"),      {
                            title: _t('Impression réussie'),
                            });
                    }, error : function()  {
                        Dialog.confirm(self, ("Impression en Echec"),      {
                            title: _t('Impression en echec'),
                            });
                    }
                });
         return;
         }
         this._super();
    },
});
});