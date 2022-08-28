# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)

_logger = logging.getLogger(__name__)


class ReportStockCardReportXlsx(models.AbstractModel):
    _name = "report.stock_card_report.report_stock_card_report_xlsx"
    _description = "Stock Card Report XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        print('enter....')
        self._define_formats(workbook)
        for product in objects.product_ids:
            print('obj = ',objects)
            print('product ...',objects.product_ids)
            for ws_params in self._get_ws_params(workbook, data, product):
                print('ws_params1 = ',ws_params)
                ws_name = ws_params.get("ws_name")
                print('ws_params2 = ',ws_params)
                ws_name = self._check_ws_name(ws_name)
                print('ws_params3 = ',ws_params)
                ws = workbook.add_worksheet(ws_name)
                generate_ws_method = getattr(self, ws_params["generate_ws_method"])
                generate_ws_method(workbook, ws, ws_params, data, objects, product)


        # for location in objects.location_ids:
        #     print('obj = ',objects)
        #     print('location ...',objects.location_ids)
        #     for ws_params in self._get_ws_params(workbook, data, product,location):
        #         print('ws_params1 = ',ws_params)
        #         ws_name = ws_params.get("ws_name")
        #         print('ws_params2 = ',ws_params)
        #         ws_name = self._check_ws_name(ws_name)
        #         print('ws_params3 = ',ws_params)
        #         ws = workbook.add_worksheet(ws_name)
        #         generate_ws_method = getattr(self, ws_params["generate_ws_method"])
        #         generate_ws_method(workbook, ws, ws_params, data, objects, product,location)








    def _get_ws_params(self, wb, data, product):
        filter_template = {
            "1_date_from": {
                "header": {"value": "Date from"},
                "data": {
                    "value": self._render("date_from"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            },
            "2_date_to": {
                "header": {"value": "Date to"},
                "data": {
                    "value": self._render("date_to"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            }
        }
        initial_template = {
            "1_ref": {
                "data": {"value": "Initial", "format": FORMATS["format_tcell_center"]},
                "colspan": 6,
            },
            "2_value": {
                "data": {
                    "value": self._render("initial_value"),
                    "format": FORMATS["format_tcell_amount_right"],
                }
            },
            "3_balance": {
                "data": {
                    "value": self._render("balance"),
                    "format": FORMATS["format_tcell_amount_right"],
                }
            },
        }
        filtered_location_template = {
            "1_filtered_location_id": {
                "data": {
                    "value": "** Location **",
                    "format": FORMATS["format_tcell_amount_right"],
                }
            },
            "2_filtered_location_id": {
                "header": {"value": "** Location **"},
                "data": {"value": self._render("filtered_location_id"),
                         "format": FORMATS["format_tcell_center"]},
                "colspan": 6,
            }
        }
        stock_card_template = {
            "1_date": {
                "header": {"value": "Date"},
                "data": {
                    "value": self._render("date"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "2_reference": {
                "header": {"value": "Reference"},
                "data": {
                    "value": self._render("reference"),
                    "format": FORMATS["format_tcell_left"],
                },
                "width": 25,
            },
            "3_location_id": {
                "header": {"value": "Location"},
                "data": {
                    "value": self._render("location_id"),
                    "format": FORMATS["format_tcell_left"],
                },
                "width": 25,
            },
            "4_location_dest_id": {
                "header": {"value": "Destination location"},
                "data": {
                    "value": self._render("location_dest_id"),
                    "format": FORMATS["format_tcell_left"],
                },
                "width": 25,
            },
            "5_input": {
                "header": {"value": "In"},
                "data": {"value": self._render("input")},
                "width": 25,
            },
            "6_output": {
                "header": {"value": "Out"},
                "data": {"value": self._render("output")},
                "width": 25,
            },
            "6_value": {
                "header": {"value": "Value"},
                "data": {"value": self._render("value")},
                "width": 25,
            },
            "8_balance": {
                "header": {"value": "Balance"},
                "data": {"value": self._render("balance")},
                "width": 25,
            },
        }

        ws_params = {
            "ws_name": product.name,
            "generate_ws_method": "_stock_card_report",
            "title": "Stock Card - {}".format(product.name)+ "                   On Hand Quantity: {}".format(product.qty_available)+" units",
            # "onhand": "Stock Card - {}".format(product.qty_available),
            "wanted_list_filter": [k for k in sorted(filter_template.keys())],
            "col_specs_filter": filter_template,
            "wanted_list_initial": [k for k in sorted(initial_template.keys())],
            "col_specs_initial": initial_template,
            "wanted_list_filtered_location": [k for k in sorted(filtered_location_template.keys())],
            "col_specs_filtered_location": filtered_location_template,
            "wanted_list": [k for k in sorted(stock_card_template.keys())],
            "col_specs": stock_card_template,
        }
        return [ws_params]

    def _stock_card_report(self, wb, ws, ws_params, data, objects, product):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        # Title
        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)
        # Filter Table
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data",
            render_space={
                "date_from": objects.date_from or "",
                "date_to": objects.date_to or "",
            },
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        row_pos += 1
        # Stock Card Table
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )
        ws.freeze_panes(row_pos, 0)
        balance = objects._get_initial(
            objects.results.filtered(lambda l: l.product_id == product and l.is_initial)
        )
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data",
            render_space={"balance": balance},
            col_specs="col_specs_initial",
            wanted_list="wanted_list_initial",
        )
        product_lines = objects.results.filtered(
            lambda l: l.product_id == product and not l.is_initial
        )
        for line in product_lines:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"filtered_location_id": line.filtered_location_id.complete_name or ''},
                col_specs="col_specs_filtered_location",
                wanted_list="wanted_list_filtered_location",
            )
            balance += line.product_in - line.product_out
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "date": line.date or "",
                    "reference": line.display_name or "",
                    "filtered_location_id": line.filtered_location_id.complete_name or '',
                    "location_id": line.location_id.complete_name or "",
                    "location_dest_id": line.location_dest_id.complete_name or "",
                    "input": line.product_in or 0,
                    "output": line.product_out or 0,
                    "value": line.value or 0,
                    "balance": balance,
                },
                default_format=FORMATS["format_tcell_amount_right"],
            )