# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockCardView(models.TransientModel):
    _name = "stock.card.view"
    _description = "Stock Card View"
    _order = "date"

    date = fields.Datetime()
    product_id = fields.Many2one(comodel_name="product.product")
    product_qty = fields.Float()
    value = fields.Float()
    product_uom_qty = fields.Float()
    product_uom = fields.Many2one(comodel_name="uom.uom")
    reference = fields.Char()
    filtered_location_id = fields.Many2one(comodel_name="stock.location")
    location_id = fields.Many2one(comodel_name="stock.location")
    location_dest_id = fields.Many2one(comodel_name="stock.location")
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()
    picking_id = fields.Many2one(comodel_name="stock.picking")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.reference
            if rec.picking_id.origin:
                name = "{} ({})".format(name, rec.picking_id.origin)
            result.append((rec.id, name))
        return result


class StockCardReport(models.TransientModel):
    _name = "report.stock.card.report"
    _description = "Stock Card Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(comodel_name="product.product")
    # location_id = fields.Many2one(comodel_name="stock.location", required=False)
    location_ids = fields.Many2many(
        comodel_name="stock.location", string="Select Multi Location"
    )
    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="stock.card.view",
        relation="stock_card_view_card_report", column1="report_id", column2="view_id",
        help="Use compute fields, so there is nothing store in database",
    )

    def get_on_hand_quantity(self, location_id, product_id):
        where = ""
        if location_id:
            where += """ sq.location_id = %s""" % location_id.id
        if product_id:
            if where:
                where += """ and sq.product_id = %s""" % product_id.id
            else:
                where += """ sq.product_id = %s""" % product_id.id

        self._cr.execute(
            """
           SELECT sum(sq.quantity) as quantity
            FROM stock_quant sq
            WHERE %s
        """ % where
        )
        stock_card_results = self._cr.dictfetchall()
        return sum(map(lambda rec: (rec.get('quantity') or 0), stock_card_results))

    def result_per_location(self, location_id):
        date_from = self.date_from or "0001-01-01"
        self.date_to = self.date_to or fields.Date.context_today(self)
        self._cr.execute(
            """
            SELECT move.date, move.product_id, move.product_qty,
                move.product_uom_qty, move.product_uom, move.reference,
                move.location_id, move.location_dest_id,
                case when move.location_dest_id in %s
                    then move.product_qty end as product_in,
                case when move.location_id in %s
                    then move.product_qty end as product_out,
                case when move.date < %s then True else False end as is_initial,
                move.picking_id,
                COALESCE (svl.value, 0.0) as value
            FROM stock_move move
            LEFT JOIN stock_valuation_layer svl on svl.stock_move_id = move.id and svl.product_id=move.product_id 
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) <= %s
            ORDER BY move.date, move.reference
        """,
            (
                tuple(location_id.ids),
                tuple(location_id.ids),
                date_from,
                tuple(location_id.ids),
                tuple(location_id.ids),
                tuple(self.product_ids.ids),
                self.date_to,
            ),
        )
        stock_card_results = self._cr.dictfetchall()
        ReportLine = self.env["stock.card.view"]
        self.results = [(6, 0, [ReportLine.create(line).id for
                                line in stock_card_results])]

    def initial_per_location(self, product_id, location_id, initial=False, price=False):
        date_from = self.date_from or "0001-01-01"
        self.date_to = self.date_to or fields.Date.context_today(self)
        self._cr.execute(
            """
            SELECT 
                case when move.location_dest_id in %s
                    then move.product_qty end as product_in,
                case when move.location_id in %s
                    then move.product_qty end as product_out,
                COALESCE (svl.value, 0.0) as value
            FROM stock_move move
            LEFT JOIN stock_valuation_layer svl on svl.stock_move_id = move.id and svl.product_id=move.product_id 
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) < %s
            ORDER BY move.date, move.reference
        """,
            (
                tuple(location_id.ids),
                tuple(location_id.ids),
                tuple(location_id.ids),
                tuple(location_id.ids),
                tuple(product_id.ids),
                date_from,
            ),
        )
        stock_card_results = self._cr.dictfetchall()
        if initial:
            return sum(map(lambda rec: (rec.get('product_in') or 0)-(rec.get('product_out') or 0), stock_card_results))
        if price:
            return sum(map(lambda rec: (rec.get('value') or 0), stock_card_results))

    def _compute_results(self):
        self.ensure_one()
        for location_id in self.location_ids:
            self.result_per_location(location_id)

    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        return product_input_qty - product_output_qty

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
                report_type == "xlsx"
                and self.env.ref("stock_card_report.action_stock_card_report_xlsx")
                or self.env.ref("stock_card_report.action_stock_card_report_pdf")
        )
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "stock_card_report.report_stock_card_report_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
