# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from json import dumps

import frappe
from frappe.model.document import Document

from insights.cache_utils import get_or_set_cache, make_cache_key

from .utils import convert_into_simple_filter, convert_to_expression, get_item_position


class InsightsDashboard(Document):
    @frappe.whitelist()
    def get_charts(self):
        charts = [
            row.chart for row in self.items if row.item_type == "Chart" and row.chart
        ]
        return frappe.get_all(
            "Insights Query Chart",
            filters={"name": ("not in", charts), "type": ["!=", "Pivot"]},
            fields=["name", "title", "type"],
        )

    @frappe.whitelist()
    def add_item(self, item):
        layout = get_item_position(
            item, [frappe.parse_json(item.layout) for item in self.items]
        )
        self.append(
            "items",
            {
                **item,
                "layout": dumps(layout, indent=2),
            },
        )
        self.save()

    @frappe.whitelist()
    def remove_item(self, item):
        for row in self.items:
            if row.name == item:
                self.remove(row)
                self.save()
                break

    @frappe.whitelist()
    def update_layout(self, updated_layout):
        updated_layout = frappe._dict(updated_layout)
        if not updated_layout:
            return

        for row in self.items:
            # row.name can be an interger which could get converted to a string
            if str(row.name) in updated_layout or row.name in updated_layout:
                new_layout = (
                    updated_layout.get(str(row.name))
                    or updated_layout.get(row.name)
                    or {}
                )
                row.layout = dumps(new_layout, indent=2)
        self.save()

    @frappe.whitelist()
    def update_filter(self, filter):
        filter = frappe._dict(filter)
        for row in self.items:
            if row.name == filter.name:
                row.filter_label = filter.filter_label
                row.filter_type = filter.filter_type
                row.filter_operator = filter.filter_operator
                row.filter_value = filter.filter_value
                row.filter_links = frappe.as_json(filter.filter_links)
                self.save()
                break

    @frappe.whitelist()
    def update_chart_filters(self, chart, filters):
        filters = frappe.parse_json(filters)
        for row in self.items:
            if row.name == chart:
                row.chart_filters = dumps(filters, indent=2)
                self.save()
                break

    @frappe.whitelist()
    def get_all_columns(self, query):
        # fetches all the columns for all the tables selected in the query
        return frappe.get_cached_doc("Insights Query", query).fetch_columns()

    @frappe.whitelist()
    def get_chart_filters(self, chart_name):
        _filters = []
        for row in self.items:
            if row.item_type != "Filter":
                continue
            filter_links = frappe.parse_json(row.filter_links) or {}
            if str(chart_name) in filter_links:
                _filters.append(
                    frappe._dict(
                        {
                            "value": row.filter_value,
                            "value_type": row.filter_type,
                            "operator": row.filter_operator,
                            "column": frappe._dict(filter_links[str(chart_name)]),
                        }
                    )
                )
        return _filters

    @frappe.whitelist()
    def get_chart_data(self, chart):
        row = next((row for row in self.items if row.chart == chart), None)
        if not row:
            return

        chart_filters = self.get_chart_filters(row.chart)
        if not chart_filters:
            return run_query(row.query)

        filter_conditions = []
        for chart_filter in chart_filters:
            if not chart_filter.value:
                continue
            filter_conditions.append(
                convert_to_expression(
                    chart_filter.column.table,
                    chart_filter.column.column,
                    chart_filter.operator,
                    chart_filter.value,
                    chart_filter.value_type,
                )
            )

        if not filter_conditions:
            return run_query(row.query)

        return run_query(row.query, additional_filters=filter_conditions)

    @frappe.whitelist()
    def get_columns(self, query):
        return frappe.get_cached_doc("Insights Query", query).get_columns()

    @frappe.whitelist()
    def update_markdown(self, item):
        item = frappe._dict(item)
        for row in self.items:
            if row.name == item.name:
                row.markdown = item.markdown
                self.save()
                break


def run_query(query_name, additional_filters=None):
    def get_result():
        query = frappe.get_cached_doc("Insights Query", query_name)
        if not additional_filters:
            return query.fetch_results()

        filters = frappe.parse_json(query.filters)

        new_filters = frappe.parse_json(query.filters)
        for new_filter in additional_filters:
            found = False
            # TODO: FIX: additional_filters was simple filter, got converted to expression, then again converted to simple filter
            if new_simple_filter := convert_into_simple_filter(new_filter):
                for index, exisiting_filter in enumerate(filters.conditions):
                    existing_simple_filter = convert_into_simple_filter(
                        exisiting_filter
                    )
                    if not existing_simple_filter:
                        continue
                    if existing_simple_filter["column"] == new_simple_filter["column"]:
                        new_filters.conditions[index] = new_filter
                        found = True
                        break
            if not found:
                new_filters.conditions.append(new_filter)

        query.filters = dumps(new_filters)
        return query.fetch_results()

    last_modified = frappe.db.get_value("Insights Query", query_name, "modified")
    key = make_cache_key(query_name, last_modified, additional_filters)

    query_result_expiry = frappe.db.get_single_value(
        "Insights Settings", "query_result_expiry"
    )
    query_result_expiry_in_seconds = query_result_expiry * 60
    return get_or_set_cache(key, get_result, expiry=query_result_expiry_in_seconds)
