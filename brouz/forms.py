import itertools

from colander import Date
from colander import Float
from colander import Integer
from colander import null
from colander import Schema
from colander import SchemaNode
from colander import SequenceSchema
from colander import String

from deform.form import Button
from deform.form import Form
from deform.widget import AutocompleteInputWidget
from deform.widget import DateInputWidget
from deform.widget import OptGroup
from deform.widget import SelectWidget
from deform.widget import SequenceWidget
from deform.widget import TextInputWidget

from pyramid_deform import CSRFSchema

from brouz.i18n import _
from brouz.models import CATEGORY_EXPENDITURE_BANKING_CHARGES
from brouz.models import CATEGORY_EXPENDITURE_CET
from brouz.models import CATEGORY_EXPENDITURE_CONFERENCES
from brouz.models import CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG
from brouz.models import CATEGORY_EXPENDITURE_FIXED_ASSETS
from brouz.models import CATEGORY_EXPENDITURE_INSURANCE_PREMIUM
from brouz.models import CATEGORY_EXPENDITURE_NON_DEDUCTIBLE_CSG
from brouz.models import CATEGORY_EXPENDITURE_OBLIGATORY_SOCIAL_CHARGES
from brouz.models import CATEGORY_EXPENDITURE_OFFICE_FURNITURE
from brouz.models import CATEGORY_EXPENDITURE_OPTIONAL_SOCIAL_CHARGES
from brouz.models import CATEGORY_EXPENDITURE_OTHER_MISC_EXPENSES
from brouz.models import CATEGORY_EXPENDITURE_OTHER_TAXES
from brouz.models import CATEGORY_EXPENDITURE_PURCHASE
from brouz.models import CATEGORY_EXPENDITURE_SMALL_FURNITURE
from brouz.models import CATEGORY_EXPENDITURE_TRAVEL_EXPENSES
from brouz.models import CATEGORY_EXPENDITURE_VAT
from brouz.models import CATEGORY_INCOME_MISC
from brouz.models import CATEGORY_REMUNERATION
from brouz.models import PAYMENT_MEANS


CATEGORIES = (
    ('', _('Select the category...')),
    (str(CATEGORY_INCOME_MISC), _('Income')),
    OptGroup(_('Expenditure'),
             (str(CATEGORY_EXPENDITURE_PURCHASE), _('Purchase')),
             (str(CATEGORY_EXPENDITURE_VAT), _('VAT')),
             (str(CATEGORY_EXPENDITURE_CET), _('CET')),
             (str(CATEGORY_EXPENDITURE_OTHER_TAXES),
              _('Other taxes')),
             (str(CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG),
              _('Deductible CSG')),
             (str(CATEGORY_EXPENDITURE_NON_DEDUCTIBLE_CSG),
              _('Non-deductible CSG')),
             (str(CATEGORY_EXPENDITURE_SMALL_FURNITURE),
              _('Small furniture')),
             (str(CATEGORY_EXPENDITURE_INSURANCE_PREMIUM),
              _('Insurance premium')),
             (str(CATEGORY_EXPENDITURE_TRAVEL_EXPENSES),
              _('Travel expenses')),
             (str(CATEGORY_EXPENDITURE_OBLIGATORY_SOCIAL_CHARGES),
              _('Obligatory social charges')),
             (str(CATEGORY_EXPENDITURE_OPTIONAL_SOCIAL_CHARGES),
              _('Optional social charges')),
             (str(CATEGORY_EXPENDITURE_CONFERENCES),
              _('Conferences')),
             (str(CATEGORY_EXPENDITURE_OFFICE_FURNITURE),
              _('Office furniture')),
             (str(CATEGORY_EXPENDITURE_OTHER_MISC_EXPENSES),
              _('Other miscellaneous expenses')),
             (str(CATEGORY_EXPENDITURE_BANKING_CHARGES),
              _('Banking charges')),
             (str(CATEGORY_EXPENDITURE_FIXED_ASSETS),
              _('Fixed assets'))),
    (str(CATEGORY_REMUNERATION), _('Remuneration')),
    )


def clone(node, counter):
    cloned = node.clone()
    cloned._order = next(counter)
    return cloned


class PermissiveFloat(Float):
    """A custom type for ``colander`` that removes spaces and replaces
    commas by dots in a string.

    Colander uses ``float(s)`` to deserialize 'Float' nodes. This
    works if and only if ``s`` uses a dot to indicate the decimal
    part, which is not the case in French where a comma is used. Also,
    we remove spaces (which may appear if the value comes from a
    spreadsheet).
    """
    def deserialize(self, node, cstruct):
        if cstruct is not null:
            cstruct = cstruct.replace(',', '.').replace(' ', '')
        return Float.deserialize(self, node, cstruct)


class _Line(Schema):
    title = SchemaNode(
        String(),
        title=_('Title'),
        widget=AutocompleteInputWidget(size=50,
                                       min_length=1,
                                       values='autocomplete/title'))
    category = SchemaNode(Integer(),
                          title=_('Category'),
                          widget=SelectWidget(values=CATEGORIES))
    amount = SchemaNode(PermissiveFloat(),
                        title=_('Amount'),
                        widget=TextInputWidget(size=8))
    vat = SchemaNode(PermissiveFloat(),
                     title=_('VAT'),
                     missing=0.0, widget=TextInputWidget(size=8))


class _Lines(SequenceSchema):
    """Represent a single line within a composite transaction."""
    line = _Line(title=_('Line'))


class CompositeTransactionSchema(CSRFSchema):
    """Schema used to add a composite transaction."""
    __counter = itertools.count(7)
    party = SchemaNode(
        String(),
        title=_('Party'),
        widget=AutocompleteInputWidget(size=30,
                                       min_length=1,
                                       values='autocomplete/party'))
    title = clone(_Line.title, __counter)
    date = SchemaNode(Date(),
                      title=_('Date'),
                      widget=DateInputWidget(size=10))
    mean = SchemaNode(Integer(),
                      title=_('Mean'),
                      widget=SelectWidget(values=PAYMENT_MEANS))
    invoice = SchemaNode(String(),
                         title=_('Invoice number'),
                         missing=u'')
    lines = _Lines(title=_('Lines'),
                   widget=SequenceWidget(
                       add_subitem_text_template=_('Add a line'),
                       min_len=1))


class UniqueTransactionSchema(CSRFSchema):
    """Schema used to add a unique transaction (i.e. a transaction
    that is not composite).
    """
    # All fields are clones of fields of the schemas defined above to
    # make the maintenance easier.
    __counter = itertools.count()
    party = clone(CompositeTransactionSchema.party, __counter)
    title = clone(_Line.title, __counter)
    date = clone(CompositeTransactionSchema.date, __counter)
    category = clone(_Line.category, __counter)
    amount = clone(_Line.amount, __counter)
    vat = clone(_Line.vat, __counter)
    mean = clone(CompositeTransactionSchema.mean, __counter)
    invoice = clone(CompositeTransactionSchema.invoice, __counter)


def make_unique_transaction_form(request, button_title):
    schema = UniqueTransactionSchema().bind(request=request)
    return Form(schema,
                buttons=(Button(title=button_title), ))


def make_composite_transaction_form(request, button_title):
    schema = CompositeTransactionSchema().bind(request=request)
    return Form(schema,
                buttons=(Button(title=button_title), ))
