"""This module will contain helper functions and classes for common clinical processing tasks
which will be done in conjunction with cycontext.
"""


def is_modified_by(span, modifier_label):
    for modifier in span._.modifiers:
        if modifier.category.upper() == modifier_label.upper():
            return True
    return False
