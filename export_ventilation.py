# -*- coding: utf-8 

#
# Ce script date de plus d'un an, je ne sais plus ce qu'il fait
# exactement. Je crois que ça m'a généré un CSV que j'ai ensuite
# intégré dans un fichier Excel (fourni par l'AGAO ?) qui présente la
# ventilation de toutes les recettes et dépenses pour l'année 2013.
#

import datetime

from brouz import accounting
from brouz import models


models.initialize_sql('sqlite:///Brouz.db')

s = models.DBSession()


def get_treso_diff(year, month):
    month_start = datetime.date(year, month, 1)
    month_end = get_month_end(month_start)
    return sum(
        txn.signed_amount.eurocents
        for txn in s.query(models.Transaction)
                     .filter_by(composite=False)
                     .filter(models.Transaction.date>=month_start)
                     .filter(models.Transaction.date<=month_end))

def get_sum(transactions, attr='net_amount', func=None):
    if func is None:
        func = lambda txn: getattr(txn, attr)
    return sum(func(txn) for txn in transactions)

def get_month_end(month_start):
    if month_start.month == 12:
        next_month_start = datetime.date(month_start.year + 1, 1, 1)
    else:
        next_month_start = datetime.date(month_start.year, month_start.month + 1, 1)
    return next_month_start - datetime.timedelta(days=1)

def fmt(amount):
    if isinstance(amount, basestring):
        return amount
    if not amount:
        return '0,00'
    amount = unicode(amount)
    return ','.join((amount[:-2], amount[-2:]))

def apply_filters(year, month, category=None):
    q = s.query(models.Transaction)
    month_start = datetime.date(year, month, 1)
    q = q.filter(models.Transaction.date>=month_start)
    q = q.filter(models.Transaction.date<=get_month_end(month_start))
    q = q.filter_by(composite=False)
    if category is not None:
        q = q.filter_by(category=category)
    return q

lines = []
treso_start = 0 # FIXME: vérifier sur relevé de compte
for year, month in (
        (2013, 1), (2013, 2), (2013, 3), (2013, 4), (2013, 5), (2013, 6),
        (2013, 7), (2013, 8), (2013, 9), (2013, 10), (2013, 11), (2013, 12),
        (2014, 1)):

    line = []

    # Trésorerie
    # treso_diff = get_treso_diff(month)
    # treso_end = treso_start + treso_diff
    # line.append(treso_start)
    # line.append(treso_end)
    # line.append(treso_diff)
    # treso_start = treso_end

    month_filter = lambda **kwargs: apply_filters(year=year, month=month, **kwargs)

    # Recettes pro, TVA facturée, prélèvements persos
    line.append(get_sum(  # Recettes pros
        month_filter(category=models.CATEGORY_INCOME_MISC)))
    line.append(get_sum(  # TVA facturée
        month_filter(category=models.CATEGORY_INCOME_MISC),
        attr='vat'))
    line.append(get_sum(  # Prélèvemments persos
        month_filter(category=models.CATEGORY_REMUNERATION)))

    # Impôts et taxes
    line.append(get_sum(  # TVA payée
        month_filter(category=models.CATEGORY_EXPENDITURE_VAT)))
    line.append(get_sum(  # CSG déductible
        month_filter(category=models.CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG)))
    line.append(get_sum(  # CET
        month_filter(category=models.CATEGORY_EXPENDITURE_CET)))
    line.append(get_sum(  # Autres impôts
        month_filter(category=models.CATEGORY_EXPENDITURE_OTHER_TAXES)))

    # Location de matériels et de mobiliers
    line.append(get_sum(
        month_filter(category=models.CATEGORY_EXPENDITURE_HARDWARE_FURNITURE_RENTAL)))

    # Travaux, fournitures et services extérieurs
    line.append(get_sum(  # Petit outillage
        month_filter(category=models.CATEGORY_EXPENDITURE_SMALL_FURNITURE)))
    line.append(get_sum(  # Honoraires ne constituant pas de rétrocessions
        month_filter(category=models.CATEGORY_EXPENDITURE_FEES_NO_RETROCESSION)))
    line.append(get_sum(  # Primes d'assurance
        month_filter(category=models.CATEGORY_EXPENDITURE_INSURANCE_PREMIUM)))

    # Transports et déplacements
    line.append(0)        # Frais de voiture
    line.append(get_sum(  # Déplacements professionnels
        month_filter(category=models.CATEGORY_EXPENDITURE_TRAVEL_EXPENSES),
        func=accounting.get_meal_deductible))

    # Charges sociales personnelles
    line.append(get_sum(  # Obligatoires
        month_filter(category=models.CATEGORY_EXPENDITURE_OBLIGATORY_SOCIAL_CHARGES)))
    line.append(get_sum(  # Facultatives
        month_filter(category=models.CATEGORY_EXPENDITURE_OPTIONAL_SOCIAL_CHARGES)))

    # Frais divers de gestion
    line.append(get_sum(  # Fournitures de bureau
        month_filter(category=models.CATEGORY_EXPENDITURE_OFFICE_FURNITURE)))

    # Frais financiers
    line.append(get_sum(
        month_filter(category=models.CATEGORY_EXPENDITURE_BANKING_CHARGES)))

    # Total des dépenses déductibles
    line.append('=SOMME(H%d:U%d)' % (5 + month, 5 + month))

    # Charges non déductibles
    line.append(get_sum(  # CSG et CRDS non déductibles
        month_filter(category=models.CATEGORY_EXPENDITURE_NON_DEDUCTIBLE_CSG)))
    line.append(get_sum(  # Frais de bouche non déductibles
        month_filter(category=models.CATEGORY_EXPENDITURE_TRAVEL_EXPENSES),
        func=lambda txn: txn.net_amount - accounting.get_meal_deductible(txn)))

    line = u';'.join(map(fmt, line)).encode('utf-8')
    lines.append(line)

print '\n'.join(lines)
