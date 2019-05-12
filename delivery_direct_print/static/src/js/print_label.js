odoo.define('delivery_direct_print.print_label', function (require) {
"use strict";
var form_widget = require('web.form_widgets');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;
form_widget.WidgetButton.include({
    on_click: function() {
        var self = this;
         if(this.node.attrs.custom === "print_label"){
            self._super().then(
            function(result) {
            var printWindow = window.open();
            printWindow.document.open('text/plain')
            printWindow.document.write(result);
            printWindow.document.close();
            printWindow.focus();
            printWindow.print();
            printWindow.close();})
         return;
         }
         this._super();
    },
});
});