from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy.orm import mapper
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
metadata = MetaData()

TYPE_INCOME = 1
TYPE_EXPENDITURE = 2
TYPE_REMUNERATION = 3

# These English terms probably do not make much sense. Hopefully, the
# French translation does.
CATEGORY_INCOME_MISC = 1
CATEGORY_EXPENDITURE_PURCHASE = 2
CATEGORY_EXPENDITURE_VAT = 3
CATEGORY_EXPENDITURE_CET = 4
CATEGORY_EXPENDITURE_OTHER_TAXES = 5
CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG = 6
CATEGORY_EXPENDITURE_NON_DEDUCTIBLE_CSG = 7
CATEGORY_EXPENDITURE_SMALL_FURNITURE = 8
CATEGORY_EXPENDITURE_INSURANCE_PREMIUM = 9
CATEGORY_EXPENDITURE_TRAVEL_EXPENSES = 10
CATEGORY_EXPENDITURE_OBLIGATORY_SOCIAL_CHARGES = 11
CATEGORY_EXPENDITURE_OPTIONAL_SOCIAL_CHARGES = 12
CATEGORY_EXPENDITURE_CONFERENCES = 13
CATEGORY_EXPENDITURE_OFFICE_FURNITURE = 14
CATEGORY_EXPENDITURE_OTHER_MISC_EXPENSES = 15
CATEGORY_EXPENDITURE_BANKING_CHARGES = 16
CATEGORY_EXPENDITURE_FIXED_ASSETS = 17
CATEGORY_EXPENDITURE_HARDWARE_FURNITURE_RENTAL = 19
CATEGORY_EXPENDITURE_FEES_NO_RETROCESSION = 20
CATEGORY_REMUNERATION = 18

PAYMENT_MEAN_CREDIT_CARD = 1
PAYMENT_MEAN_WIRE_TRANSFER = 2
PAYMENT_MEAN_CHECK = 3
PAYMENT_MEAN_DIRECT_DEBIT = 4


class Transaction(object):

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.year = self.date.year

    @property
    def type(self):
        if self.category == CATEGORY_REMUNERATION:
            return TYPE_REMUNERATION
        if self.category in (CATEGORY_INCOME_MISC, ):
            return TYPE_INCOME
        return TYPE_EXPENDITURE

    @property
    def signed_amount(self):
        if self.type in (TYPE_EXPENDITURE, TYPE_REMUNERATION):
            return -self.amount
        return self.amount


transaction_table = Table(
    'transactions',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('party', Unicode, nullable=False),
    Column('title', Unicode, primary_key=False),
    Column('date', Date, nullable=False),
    # We could do without an additional column for the year, of
    # course, but it simplifies queries.
    Column('year', Integer, nullable=False),
    # In a composite transaction, the 'category' is in fact the
    # category of the first included transaction. We need a category
    # (even though it is meaningless) to know whether the amount is
    # positive or negative.
    Column('category', Integer, nullable=False),
    Column('amount', Float, nullable=False),
    Column('vat', Float, nullable=False),
    Column('mean', Integer, nullable=False),
    Column('invoice', Unicode, nullable=False),
    Column('composite', Boolean, nullable=False),
    Column('part_of', Integer, ForeignKey('transactions.id'), nullable=True),
    )


transaction_mapper = mapper(
    Transaction, transaction_table)


def initialize_sql(db_string, echo=False):
    engine = create_engine(db_string, echo=echo)
    DBSession.configure(bind=engine)
    metadata.bind = engine
    metadata.create_all(engine)
    return engine
