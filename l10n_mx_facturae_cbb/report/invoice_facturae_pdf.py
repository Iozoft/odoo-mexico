# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 moylop260 - http://moylop.blogspot.com/
#    All Rights Reserved.
#    info moylop260 (moylop260@hotmail.com)
############################################################################
#    Coded by: moylop260 (moylop260@hotmail.com)
#    Launchpad Project Manager for Publication: Nhomar Hernandez - nhomar@openerp.com.ve
############################################################################
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

from report import report_sxw
import pooler
import tools
from amount_to_text_es import amount_to_text as amount_to_text_class

amount_to_text_obj = amount_to_text_class()
#amount_to_text = amount_to_text_obj.amount_to_text
amount_to_text = amount_to_text_obj.amount_to_text_cheque

###sql_delete_report = "DELETE FROM ir_act_report_xml WHERE report_name = 'account.invoice.facturae.pdf'"--Si no toma la actualizacion del reporte xml, borrarlo directamente desde la base de datos, con este script.

class account_invoice_facturae_pdf(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_invoice_facturae_pdf, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'set_global_data': self._set_global_data,
            'facturae_data_dict': self._facturae_data_dict,
            'amount_to_text': self._get_amount_to_text,
            'split_string': self._split_string,
            'company_address': self._company_address,
            'subcompany_address': self._subcompany_address,
            'get_invoice_sequence': self._get_invoice_sequence,
            'get_approval': self._get_approval,
            'get_taxes': self._get_taxes,
            'get_taxes_ret': self._get_taxes_ret,
            'float': float,
        })
        self.taxes = []
    
    def _set_global_data(self, o):
        try:
            self.setLang(o.partner_id.lang)
        except Exception, e:
            print "exception: %s"%( e )
            pass
        try:
            self._get_company_address(o.id)
        except Exception, e:
            print "exception: %s"%( e )
            pass
        try:
            self._get_facturae_data_dict(o.id)
        except Exception, e:
            print "exception: %s"%( e )
            pass
        return ""
        
    def _get_approval(self):
        return self.approval
        
    def _get_invoice_sequence(self):
        return self.sequence
    
    def _set_invoice_sequence_and_approval(self, invoice_id):
        #TinyERP Compatibility
        context = {}
        pool = pooler.get_pool(self.cr.dbname)
        invoice_obj = pool.get('account.invoice')
        sequence_obj = pool.get('ir.sequence')
        approval_obj = pool.get('ir.sequence.approval')
        #invoice = invoice_obj.browse(self.cr, self.uid, invoice_id)
        sequence_id = invoice_obj._get_invoice_sequence(self.cr, self.uid, [invoice_id])[invoice_id]
        sequence = sequence_obj.browse(self.cr, self.uid, [sequence_id])[0]
        self.sequence = sequence
        
        invoice = invoice_obj.browse(self.cr, self.uid, [invoice_id])[0]
        context.update({'number_work': invoice.number})
        approval_id = sequence_obj._get_current_approval(self.cr, self.uid, [sequence_id], context=context)[sequence_id]
        approval = approval_obj.browse(self.cr, self.uid, [approval_id])[0]
        self.approval = approval
        return sequence, approval
    
    def _get_taxes(self):
        return self.taxes
    
    def _get_taxes_ret(self):
        try:
            return self.taxes_ret
        except:
            pass
        return []
    
    def _split_string(self, string, length=100):
        if string:
            for i in range(0, len(string), length):
                string = string[:i] + ' ' + string[i:]
        return string
        
    def _get_amount_to_text(self, amount, lang, currency=""):
        if currency.upper() in ('MXP', 'MXN', 'PESOS', 'PESOS MEXICANOS'):
            sufijo = 'M. N.'
            currency = 'PESOS'
        else:
            sufijo = 'M. E.'
        #return amount_to_text(amount, lang, currency)
        amount_text = amount_to_text(amount, currency, sufijo)
        amount_text = amount_text and amount_text.upper() or ''
        return amount_text
    
    def _get_company_address(self, invoice_id):
        pool = pooler.get_pool(self.cr.dbname)
        invoice_obj = pool.get('account.invoice')
        partner_obj = pool.get('res.partner')
        address_obj = pool.get('res.partner.address')
        invoice = invoice_obj.browse(self.cr, self.uid, invoice_id)
        partner_id = invoice.company_id.parent_id and invoice.company_id.parent_id.partner_id.id or invoice.company_id.partner_id.id
        address_id = partner_obj.address_get(self.cr, self.uid, [partner_id], ['invoice'])['invoice']
        self.company_address_invoice = address_obj.browse(self.cr, self.uid, address_id)
        
        subpartner_id = invoice.company_id.partner_id.id
        if partner_id == subpartner_id:
            self.subcompany_address_invoice = self.company_address_invoice
        else:
            subaddress_id = partner_obj.address_get(self.cr, self.uid, [subpartner_id], ['invoice'])['invoice']
            self.subcompany_address_invoice = address_obj.browse(self.cr, self.uid, subaddress_id)
        return ""
    
    def _company_address(self):
        return self.company_address_invoice
    
    def _subcompany_address(self):
        return self.subcompany_address_invoice
    
    def _facturae_data_dict(self):
        return self.invoice_data_dict
    
    def _get_facturae_data_dict(self, invoice_id):
        pool = pooler.get_pool(self.cr.dbname)
        invoice_obj = pool.get('account.invoice')
        invoice_tax_obj = pool.get('account.invoice.tax')
        try:
            self._set_invoice_sequence_and_approval( invoice_id )
        except:
            print "report error: self._set_invoice_sequence_and_approval( invoice_id )"
            pass
        invoice = invoice_obj.browse(self.cr, self.uid, [invoice_id])[0]
        tax_line_ids = [tax_line.id for tax_line in invoice.tax_line]
        tax_datas = invoice_tax_obj._get_tax_data(self.cr, self.uid, tax_line_ids)
        self.taxes = tax_datas.values()
        return ""
    
report_sxw.report_sxw(
    'report.account.invoice.facturae.pdf',
    'account.invoice',
    'addons/l10n_mx_facturae_cbb/report/invoice_facturae_pdf.rml',
    header=False,
    parser=account_invoice_facturae_pdf,
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: