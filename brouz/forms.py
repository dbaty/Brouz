from colander import Boolean
from colander import Date
from colander import Integer
from colander import Money
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

from brouz import accounting
from brouz.i18n import _
from brouz.models import CATEGORY_EXPENDITURE_BANKING_CHARGES
from brouz.models import CATEGORY_EXPENDITURE_CET
from brouz.models import CATEGORY_EXPENDITURE_CONFERENCES
from brouz.models import CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG
from brouz.models import CATEGORY_EXPENDITURE_FEES_NO_RETROCESSION
from brouz.models import CATEGORY_EXPENDITURE_FIXED_ASSETS
from brouz.models import CATEGORY_EXPENDITURE_HARDWARE_FURNITURE_RENTAL
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
from brouz.models import PAYMENT_MEAN_CHECK
from brouz.models import PAYMENT_MEAN_CREDIT_CARD
from brouz.models import PAYMENT_MEAN_DIRECT_DEBIT
from brouz.models import PAYMENT_MEAN_WIRE_TRANSFER


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
             (str(CATEGORY_EXPENDITURE_FEES_NO_RETROCESSION),
              _('Fees that are not retrocessions')),
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
              _('Fixed assets')),
             (str(CATEGORY_EXPENDITURE_HARDWARE_FURNITURE_RENTAL),
              _('Hardware and furniture rental'))),
    (str(CATEGORY_REMUNERATION), _('Remuneration')),
    )


PAYMENT_MEANS = (('', _('Select the payment mean...')),
                 (str(PAYMENT_MEAN_CREDIT_CARD), _('Credit card')),
                 (str(PAYMENT_MEAN_WIRE_TRANSFER), _('Wire transfer')),
                 (str(PAYMENT_MEAN_CHECK), _('Check')),
                 (str(PAYMENT_MEAN_DIRECT_DEBIT), _('Direct debit'))
                 )


class PriceType(Money):
    """A custom type for ``colander`` that converts from and to
    ``accounting.Price``.
    """

    def serialize(self, node, appstruct):
        if appstruct is null:
            return null
        return accounting.numeric_eurocents_to_text_euros(appstruct)

    def deserialize(self, node, cstruct):
        v = Money.deserialize(self, node, cstruct)
        if v is not null:
            v = accounting.Price(accounting.numeric_euros_to_numeric_eurocents(v))
        return v


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
    is_meal = SchemaNode(Boolean(),
                         title=_('Meal'))
    net_amount = SchemaNode(PriceType(),
                        title=_('Amount'),
                        widget=TextInputWidget(size=8))
    vat = SchemaNode(PriceType(),
                     title=_('VAT'),
                     missing=0.0,
                     widget=TextInputWidget(size=8))


class _Lines(SequenceSchema):
    """Represent a single line within a composite transaction."""
    line = _Line(title=_('Line'))


class CompositeTransactionSchema(CSRFSchema):
    """Schema used to add a composite transaction."""
    party = SchemaNode(
        String(),
        title=_('Party'),
        widget=AutocompleteInputWidget(size=30,
                                       min_length=1,
                                       values='autocomplete/party'))
    title = SchemaNode(
        String(),
        title=_('Title'),
        widget=AutocompleteInputWidget(size=50,
                                       min_length=1,
                                       values='autocomplete/title'))
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
    # FIXME: all fields are duplicated from 'CompositeTransactionSchema'.
    # I used to be able to clone schema nodes in a previous version
    # but this does not seem to work with colander>0.9.9.
    party = SchemaNode(
        String(),
        title=_('Party'),
        widget=AutocompleteInputWidget(size=30,
                                       min_length=1,
                                       values='autocomplete/party'))
    title = SchemaNode(
        String(),
        title=_('Title'),
        widget=AutocompleteInputWidget(size=50,
                                       min_length=1,
                                       values='autocomplete/title'))
    date = SchemaNode(Date(),
                      title=_('Date'),
                      widget=DateInputWidget(size=10))
    category = SchemaNode(Integer(),
                          title=_('Category'),
                          widget=SelectWidget(values=CATEGORIES))
    is_meal = SchemaNode(Boolean(),
                         title=_('Meal'))
    net_amount = SchemaNode(PriceType(),
                        title=_('Amount'),
                        widget=TextInputWidget(size=8))
    vat = SchemaNode(PriceType(),
                     title=_('VAT'),
                     missing=0.0,
                     widget=TextInputWidget(size=8))
    mean = SchemaNode(Integer(),
                      title=_('Mean'),
                      widget=SelectWidget(values=PAYMENT_MEANS))
    invoice = SchemaNode(String(),
                         title=_('Invoice number'),
                         missing=u'')


def make_add_form(request, composite):
    if composite:
        schema = CompositeTransactionSchema()
        route_name = 'add-composite'
    else:
        schema = UniqueTransactionSchema()
        route_name = 'add-unique'
    schema = schema.bind(request=request)
    return Form(schema, request.route_url(route_name),
                buttons=(Button(title=_('Add transaction')), ))


def make_edit_form(request, transaction):
    if transaction.composite:
        schema = CompositeTransactionSchema()
    else:
        schema = UniqueTransactionSchema()
    schema = schema.bind(request=request)
    action = request.route_url('edit', transaction_id=transaction.id)
    return Form(schema, action,
                buttons=(Button(title=_('Save changes')), ))
