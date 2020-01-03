"""Provides a template handler that renders the menu."""
from django import template

from giphousewebsite.menus import MAIN_MENU

register = template.Library()


def _is_active(item, path):
    if "url" not in item:
        return False
    return item["url"].lower() == path.lower()


@register.inclusion_tag("menu/menu.html", takes_context=True)
def render_main_menu(context):
    """Render the main menu in this place.

    Accounts for logged-in status and locale.
    """
    path = context["request"].path

    for item in MAIN_MENU:
        active = _is_active(item, path)
        if not active and "submenu" in item:
            if callable(item["submenu"]):
                item["submenu"] = item["submenu"]()
            for subitem in item["submenu"]:
                if _is_active(subitem, path):
                    subitem["active"] = True
                    active = True
                else:
                    subitem["active"] = False
        item["active"] = active

    menu = [
        item
        for item in MAIN_MENU
        if "visible" not in item or "visible" in item and item["visible"](context.get("request"))
    ]

    return {"menu": menu, "request": context.get("request")}
