# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_created = fields.Boolean(string="", defult=False)



class Expense(models.Model):
    _name = 'expense.expense'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'expense_expense'
    _rec_name = 'seq'

    name = fields.Text(string="Ref", required=False, )
    journal_entry_id = fields.Many2one(comodel_name="account.move", string="Journal Entry",copy=False )
    expense_date = fields.Date(string="Expense Date", required=False, tracking=True)
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal", required=True, tracking=True,
                                 domain="[('type', 'in', ['bank','cash'])]")
    expenses_ids = fields.One2many(comodel_name="expense.line", inverse_name="invoice_id", string="Expenses",
                                   tracking=True)
    total = fields.Float(string="Total", tracking=True)
    tax = fields.Float(string="Taxes", compute="_get_tax", tracking=True)
    state = fields.Selection(selection=
                             [('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ], required=False, default='draft', tracking=True)
    amount_taxed = fields.Float(string="Un Taxed Amount", tracking=True)
    seq = fields.Char(readonly=True, copy=False, )

    def unlink(self):
        error_message = _('You cannot delete a expense which is in %s state')
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}

        if self.user_has_groups('base.group_user'):
            if any(hol.state not in ['draft'] for hol in self):
                raise UserError(error_message % state_description_values.get(self[:1].state))
        return super(Expense, self).unlink()

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.journal_entry_id.button_draft()

    # @api.onchange("journal_id","type")
    # def Onchange(self):
    #     for rec in self:
    #         return {'domin'}

    @api.model
    def create(self, vals):
        if vals.get('seq', _('New')) == _('New'):
            vals['seq'] = self.env['ir.sequence'].next_by_code(
                'expense.sequence', ) or _('New')
        result = super(Expense, self).create(vals)
        return result

    def get_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def get_confirm(self):
        for rec in self:
            lines = []
            taxx = 0
            for line in rec.expenses_ids:
                for tax in line.tax_ids.invoice_repartition_line_ids:
                    if tax.account_id:
                        taxx = tax.account_id.id
                lines.append([0, 0, {
                    'account_id': line.account_id.id,
                    'name': line.name,
                    'debit': line.price_subtotal,
                }])
            if taxx:
                lines.append([0, 0, {
                    'account_id': taxx,
                    'name': 'tax',
                    'debit': rec.tax,
                }])
            lines.append([0, 0, {
                'account_id': rec.journal_id.default_account_id.id,
                'name': rec.name,
                'credit': rec.total,
            }])

            if rec.journal_entry_id.is_created == False:
                invoice = self.env['account.move'].sudo().create({
                    'is_created': True,
                    'move_type': 'entry',
                    'ref': rec.name,
                    'date': rec.expense_date,
                    'journal_id': rec.journal_id.id,
                    'line_ids': lines,
                })
                rec.journal_entry_id = invoice.id
                invoice.action_post()

                # 'line_ids': [(0, 0, {
                #         'account_id': rec.account_id.id,
                #         'name': rec.name,
                #         'debit': rec.price_unit,
                #     }), (0, 0, {
                #         'account_id': rec.account_id.id,
                #         'name': rec.name,
                #         'credit': rec.price_unit,
                #     })],
                # })
                # rec.journal_entry_id = invoice.id
            else:
                rec.journal_entry_id.date = rec.expense_date
                rec.journal_entry_id.journal_id = rec.journal_id
                rec.journal_entry_id.ref = rec.name
                rec.journal_entry_id.line_ids = False
                rec.journal_entry_id.line_ids = lines
                rec.journal_entry_id.action_post()
            rec.state = 'confirm'

    @api.depends("expenses_ids")
    def _get_tax(self):
        subtotal = 0
        for rec in self:
            n = 0
            taxes = 0
            for line in rec.expenses_ids:
                t = 0
                for any_line in line.tax_ids:
                    t = t + any_line.amount
                taxes = (t / 100) * line.quantity * line.price_unit
                line.price_subtotal = line.quantity * line.price_unit
                subtotal = subtotal + line.price_subtotal
                n = n + taxes
            rec.tax = n
            rec.amount_taxed = subtotal
            rec.total = rec.tax + rec.amount_taxed


class ExpenseLine(models.Model):
    _name = 'expense.line'
    _description = 'expense_line'

    invoice_id = fields.Many2one(comodel_name="expense.expense", )
    product_ids = fields.Many2one(comodel_name="product.product", string="Product", )
    name = fields.Char(string="Label", )
    account_id = fields.Many2one(comodel_name="account.account", string="Account", required=True,
                                 related='product_ids.property_account_expense_id', readonly=False, store=True)
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account ",
                                          required=False, )
    quantity = fields.Float(string="Quantity", required=False, default="1")
    price_unit = fields.Float(string="Price", required=True, )
    tax_ids = fields.Many2many(comodel_name="account.tax", string="Taxes", )
    price_subtotal = fields.Float(string="Subtotal", required=False, )
    # tax_value = fields.Float(string="Taxes Value", )
    # subtotal = fields.Float(string="Subtotal Go To Debit Or Credit", required=True, )


class receive(models.Model):
    _name = 'receive.receive'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'receive_receive'
    _rec_name = 'seq'

    name = fields.Text(string="Ref", required=False, )
    journal_entry_id = fields.Many2one(comodel_name="account.move", string="Journal Entry", )
    receive_date = fields.Date(string="receive Date", required=False, tracking=True,copy=False)
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal", required=True, tracking=True,
                                 domain="[('type', 'in', ['bank','cash'])]")
    receives_ids = fields.One2many(comodel_name="receive.line", inverse_name="invoice_id", string="receives",
                                   tracking=True)
    total = fields.Float(string="Total", tracking=True)
    tax = fields.Float(string="Taxes", compute="_get_tax", tracking=True)
    state = fields.Selection(selection=
                             [('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ], required=False, default='draft', tracking=True)
    amount_taxed = fields.Float(string="Un Taxed Amount", tracking=True)
    seq = fields.Char(readonly=True, copy=False, )

    def unlink(self):
        error_message = _('You cannot delete a receive which is in %s state')
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}

        if self.user_has_groups('base.group_user'):
            if any(hol.state not in ['draft'] for hol in self):
                raise UserError(error_message % state_description_values.get(self[:1].state))
        return super(receive, self).unlink()

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.journal_entry_id.button_draft()

    # @api.onchange("journal_id","type")
    # def Onchange(self):
    #     for rec in self:
    #         return {'domin'}

    @api.model
    def create(self, vals):
        if vals.get('seq', _('New')) == _('New'):
            vals['seq'] = self.env['ir.sequence'].next_by_code(
                'receive.sequence', ) or _('New')
        result = super(receive, self).create(vals)
        return result

    def get_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def get_confirm(self):
        for rec in self:
            lines = []
            taxx = 0
            for line in rec.receives_ids:
                for tax in line.tax_ids.invoice_repartition_line_ids:
                    if tax.account_id:
                        taxx = tax.account_id.id
                lines.append([0, 0, {
                    'account_id': line.account_id.id,
                    'name': line.name,
                    'credit': line.price_subtotal,
                }])
            if taxx:
                lines.append([0, 0, {
                    'account_id': taxx,
                    'name': 'tax',
                    'credit': rec.tax,
                }])
            lines.append([0, 0, {
                'account_id': rec.journal_id.default_account_id.id,
                'name': rec.name,
                'debit': rec.total,
            }])

            if rec.journal_entry_id.is_created == False:
                invoice = self.env['account.move'].sudo().create({
                    'is_created': True,
                    'move_type': 'entry',
                    'ref': rec.name,
                    'date': rec.receive_date,
                    'journal_id': rec.journal_id.id,
                    'line_ids': lines,
                })
                rec.journal_entry_id = invoice.id
                invoice.action_post()

                # 'line_ids': [(0, 0, {
                #         'account_id': rec.account_id.id,
                #         'name': rec.name,
                #         'debit': rec.price_unit,
                #     }), (0, 0, {
                #         'account_id': rec.account_id.id,
                #         'name': rec.name,
                #         'credit': rec.price_unit,
                #     })],
                # })
                # rec.journal_entry_id = invoice.id
            else:
                rec.journal_entry_id.date = rec.receive_date
                rec.journal_entry_id.journal_id = rec.journal_id
                rec.journal_entry_id.ref = rec.name
                rec.journal_entry_id.line_ids = False
                rec.journal_entry_id.line_ids = lines
                rec.journal_entry_id.action_post()
            rec.state = 'confirm'

    @api.depends("receives_ids")
    def _get_tax(self):
        subtotal = 0
        for rec in self:
            n = 0
            taxes = 0
            for line in rec.receives_ids:
                t = 0
                for any_line in line.tax_ids:
                    t = t + any_line.amount
                taxes = (t / 100) * line.quantity * line.price_unit
                line.price_subtotal = line.quantity * line.price_unit
                subtotal = subtotal + line.price_subtotal
                n = n + taxes
            rec.tax = n
            rec.amount_taxed = subtotal
            rec.total = rec.tax + rec.amount_taxed


class receiveLine(models.Model):
    _name = 'receive.line'
    _description = 'receive_line'

    invoice_id = fields.Many2one(comodel_name="receive.receive", )
    product_ids = fields.Many2one(comodel_name="product.product", string="Product", )
    name = fields.Char(string="Label", )
    account_id = fields.Many2one(comodel_name="account.account", string="Account", required=True,
                                 related='product_ids.property_account_expense_id', readonly=False, store=True)
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account ",
                                          required=False, )
    quantity = fields.Float(string="Quantity", required=False, default="1")
    price_unit = fields.Float(string="Price", required=True, )
    tax_ids = fields.Many2many(comodel_name="account.tax", string="Taxes", )
    price_subtotal = fields.Float(string="Subtotal", required=False, )
    # tax_value = fields.Float(string="Taxes Value", )
    # subtotal = fields.Float(string="Subtotal Go To Debit Or Credit", required=True, )


