# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

__version__ = "0.1.0-beta"


def notify(**kwargs):
    frappe.publish_realtime(
        event="insights_notification",
        message={
            "message": kwargs.get("message"),
            "title": kwargs.get("title"),
            "type": kwargs.get("type"),
            "user": frappe.session.user,
        },
    )
