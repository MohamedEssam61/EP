# -*- coding: utf-8 -*-
# from odoo import http


# class AddMenuExpAccount(http.Controller):
#     @http.route('/add_menu_exp_account/add_menu_exp_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/add_menu_exp_account/add_menu_exp_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('add_menu_exp_account.listing', {
#             'root': '/add_menu_exp_account/add_menu_exp_account',
#             'objects': http.request.env['add_menu_exp_account.add_menu_exp_account'].search([]),
#         })

#     @http.route('/add_menu_exp_account/add_menu_exp_account/objects/<model("add_menu_exp_account.add_menu_exp_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('add_menu_exp_account.object', {
#             'object': obj
#         })
