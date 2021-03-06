import datetime

from deform.exception import ValidationFailure

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.renderers import render_to_response

from brouz import accounting
from brouz import enums
from brouz.forms import make_add_form
from brouz.forms import make_edit_form
from brouz.i18n import _
from brouz.models import CATEGORY_EXPENDITURE_BANKING_CHARGES
from brouz.models import CATEGORY_EXPENDITURE_CET
from brouz.models import CATEGORY_EXPENDITURE_CONFERENCES
from brouz.models import CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG
from brouz.models import CATEGORY_EXPENDITURE_FEES_NO_RETROCESSION
from brouz.models import CATEGORY_EXPENDITURE_FIXED_ASSETS
from brouz.models import CATEGORY_EXPENDITURE_HARDWARE_FURNITURE_RENTAL
from brouz.models import CATEGORY_EXPENDITURE_INSURANCE_PREMIUM
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
from brouz.models import DBSession
from brouz.models import Transaction
from brouz.utils import TemplateAPI


def home(request):
    session = DBSession()
    lines = session.query(Transaction).filter_by(part_of=None, composite=False)
    lines = lines.union(session.query(Transaction).filter_by(composite=True))
    lines = lines.order_by(Transaction.date,
                           Transaction.party,
                           Transaction.title)
    balances = [accounting.Price(2494978)]
    for line in lines:
        balances.append(balances[-1] + line.signed_amount)
    balance = sum((line.signed_amount for line in lines), accounting.Price(0))
    api = TemplateAPI(request, 'home')
    bindings = {'api': api,
                'lines': lines,
                'balance': balance,
                'balances': balances}
    return render_to_response('templates/home.pt', bindings)


def add_unique_form(request, form=None):
    if form is None:
        form = make_add_form(request, composite=False)
    api = TemplateAPI(request, 'add')
    bindings = {'api': api,
                'form': form}
    return render_to_response('templates/add.pt', bindings)


def add_unique(request):
    form = make_add_form(request, composite=False)
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return add_unique_form(request, e)
    data['composite'] = False
    data['part_of'] = None
    data['net_amount'] = data['net_amount'].eurocents
    data['vat'] = data['vat'].eurocents
    transaction = Transaction(**data)
    session = DBSession()
    session.add(transaction)
    request.session.flash(_('The transaction has been added.'), 'success')
    return HTTPSeeOther(request.route_url('home'))


def add_composite_form(request, form=None):
    if form is None:
        form = make_add_form(request, composite=True)
    api = TemplateAPI(request, 'add')
    bindings = {'api': api,
                'form': form}
    return render_to_response('templates/add.pt', bindings)


def add_composite(request):
    form = make_add_form(request, composite=True)
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return add_unique_form(request, e)
    total_net_amount = sum(l['net_amount'] for l in data['lines'])
    total_vat = sum(l['vat'] for l in data['lines'])
    composite = Transaction(party=data['party'],
                            title=data['title'],
                            date=data['date'],
                            category=data['lines'][0]['category'],
                            is_meal=False,
                            net_amount=total_net_amount.eurocents,
                            vat=total_vat.eurocents,
                            mean=data['mean'],
                            invoice=data['invoice'],
                            composite=True,
                            part_of=None)
    session = DBSession()
    session.add(composite)
    session.flush()  # set transaction.id
    for line in data['lines']:
        t = Transaction(party=data['party'],
                        title=line['title'],
                        date=data['date'],
                        category=line['category'],
                        is_meal=line['is_meal'],
                        net_amount=line['net_amount'].eurocents,
                        vat=line['vat'].eurocents,
                        mean=data['mean'],
                        invoice=data['invoice'],
                        composite=False,
                        part_of=composite.id)
        session.add(t)
    request.session.flash(_('The transaction has been added.'), 'success')
    return HTTPSeeOther(request.route_url('home'))


def edit_form(request, form=None):
    if form is None:
        session = DBSession()
        transaction_id = request.matchdict['transaction_id']
        transaction = session.query(Transaction).\
            filter_by(id=transaction_id).one()
        form = make_edit_form(request, transaction)
        if transaction.composite:
            data = transaction.__dict__
            data['lines'] = []
            for txn in session.query(Transaction).\
                    filter_by(part_of=transaction_id).all():
                data['lines'].append(txn.__dict__)
        else:
            data = transaction.__dict__
    api = TemplateAPI(request, 'add')
    bindings = {'api': api,
                'form': form,
                'data': data}
    return render_to_response('templates/edit.pt', bindings)


def edit(request):
    session = DBSession()
    transaction_id = request.matchdict['transaction_id']
    transaction = session.query(Transaction).\
        filter_by(id=transaction_id).one()
    form = make_edit_form(request, transaction)
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return edit_form(request, e)
    if transaction.composite:
        raise NotImplementedError
    else:
        data['composite'] = False
        data['part_of'] = None
        data['net_amount'] = data['net_amount'].eurocents
        data['vat'] = data['vat'].eurocents
        transaction.update(**data)
    request.session.flash(_('The transaction has been modified.'), 'success')
    return HTTPSeeOther(request.route_url('home'))


def delete(request):
    transaction_id = request.matchdict['transaction_id']
    if request.POST.get('confirm') != '1':
        msg = _('You did not confirm that you want to delete '
                'this transaction.')
        request.session.flash(msg, 'error')
        url = request.route_url('edit', transaction_id=transaction_id)
        return HTTPSeeOther(url)
    session = DBSession()
    transaction = session.query(Transaction).\
        filter_by(id=transaction_id).one()
    # FIXME: If transaction is composite, we should delete the related
    # transactions: filter_by(part_of=transaction_id)
    session.delete(transaction)
    request.session.flash(_('The transaction has been deleted.'), 'success')
    return HTTPSeeOther(request.route_url('home'))


def reports(request):
    try:
        year = int(request.matchdict['year'])
    except KeyError:  # no matchdict
        year = datetime.datetime.now().year
    session = DBSession()
    if session.query(Transaction.date).\
            filter_by(year=year - 1).first() is None:
        previous_year = None
    else:
        previous_year = year - 1
    if session.query(Transaction.date).\
            filter_by(year=year + 1).first() is None:
        next_year = None
    else:
        next_year = year + 1
    lines = session.query(Transaction).\
        filter_by(year=year, composite=False).all()
    report = _calculate_report(lines)
    _update_report_with_fixed_assets(report, year, session)
    _update_report_with_vat(report, lines)
    report['vat_installments'] = accounting.calculate_vat_installments(
        session.query(Transaction), year)
    # FIXME: move these to separate function(s)?
    report['clients'] = ((party, accounting.Price(net_amount))
        for party, net_amount in session.execute(
        'SELECT party, SUM(net_amount) AS sum '
        'FROM transactions '
        'WHERE category=%d '
        'AND year=%d '
        'GROUP BY party '
        'ORDER BY sum DESC' % (CATEGORY_INCOME_MISC, year)))
    report['providers'] = ((party, accounting.Price(net_amount))
        for party,  net_amount, in session.execute(
        'SELECT party, SUM(net_amount) AS sum '
        'FROM transactions '
        'WHERE category NOT IN (%s, %s) '
        'AND composite = 0 '
        'AND part_of IS NULL '
        'AND year=%d '
        'GROUP BY party '
        'ORDER BY sum DESC' % (
            CATEGORY_INCOME_MISC, CATEGORY_REMUNERATION, year)))
    report['remuneration'] = [(date, accounting.Price(net_amount))
        for date, net_amount in session.query(
        Transaction.date, Transaction.net_amount).\
        filter_by(category=CATEGORY_REMUNERATION, year=year).\
        order_by(Transaction.date)]
    report['total_remuneration'] = sum(
        r[1] for r in report['remuneration'])
    bindings = {'api': TemplateAPI(request, 'reports'),
                'year': year,
                'previous_year': previous_year,
                'next_year': next_year,
                'report': report}
    return render_to_response('templates/reports.pt', bindings)


def _calculate_report(lines):
    # Les commentaires correspondent aux intitules exacts de la
    # declaration 2035-1K (2012).
    def _get_sum_of_lines(lines, category, compute=None):
        total = 0
        if compute is None:
            compute = lambda line: line.net_amount
        for line in lines:
            if line.category == category:
                total += compute(line)
        return accounting.RoundedPrice(total)
    # Recettes encaissees y compris les remboursements de frais
    aa = _get_sum_of_lines(lines, CATEGORY_INCOME_MISC)
    total_income = aa
    # Achats
    ba = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_PURCHASE)
    # TVA
    bd = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_VAT)
    # Contribution economique territoriale (CET)
    #   =   Contribution fonciere des entreprises (CFE)
    #     + CVAE (nulle si CA < 150.000 EUR environ)
    jy = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_CET)
    # Autres impots
    bs = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_OTHER_TAXES)
    # CSG deductible
    bv = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG)
    # Location de materiel et de mobilier
    bg = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_HARDWARE_FURNITURE_RENTAL)
    # Petit outillage
    bh_small_furniture = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_SMALL_FURNITURE)
    # Primes d'assurance
    bh_insurance_premium = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_INSURANCE_PREMIUM)
    # Honoraires ne constituant pas des retrocessions
    bh_fees_no_retrocession = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_FEES_NO_RETROCESSION)
    # Total : travaux, fournitures et services exterieurs
    bh = accounting.sum_rounded_prices(
        bh_small_furniture, bh_insurance_premium, bh_fees_no_retrocession)
    # Autres frais de deplacements (voyages...)
    bj_travel_expenses = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_TRAVEL_EXPENSES, accounting.get_meal_deductible)
    # Total : transports et deplacements
    bj = accounting.sum_rounded_prices(bj_travel_expenses)
    # Charges sociales personnelles obligatoires
    bt = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_OBLIGATORY_SOCIAL_CHARGES)
    # Charges sociales personnelles facultatives
    bu = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_OPTIONAL_SOCIAL_CHARGES)
    # Total charges sociales personnelles
    bk = accounting.sum_rounded_prices(bt, bu)
    # Frais de reception, de representation et de congres
    bm_conferences = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_CONFERENCES)
    # Fournitures de bureau, frais de documentation, de correspondance
    # et de telephone
    bm_office = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_OFFICE_FURNITURE)
    # Autres frais divers de gestion
    bm_other = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_OTHER_MISC_EXPENSES)
    # Total : frais divers de gestion
    bm = accounting.sum_rounded_prices(bm_conferences, bm_office, bm_other)
    # Frais financiers
    bn = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_BANKING_CHARGES)
    # Total (BR)
    total_expenditure = accounting.sum_rounded_prices(
        ba, bd, jy, bs, bv, bg, bh, bj, bk, bm, bn)
    report = {'aa': aa,
              'total_income': total_income,
              'ba': ba,
              'bd': bd,
              'jy': jy,
              'bs': bs,
              'bv': bv,
              'bh_small_furniture': bh_small_furniture,
              'bh_fees_no_retrocession': bh_fees_no_retrocession,
              'bh_insurance_premium': bh_insurance_premium,
              'bg': bg,
              'bh': bh,
              'bj_travel_expenses': bj_travel_expenses,
              'bj': bj,
              'bt': bt,
              'bu': bu,
              'bk': bk,
              'bm_conferences': bm_conferences,
              'bm_office': bm_office,
              'bm_other': bm_other,
              'bm': bm,
              'bn': bn,
              'total_expenditure': total_expenditure}
    return report


def _update_report_with_fixed_assets(report, year, session):
    """Update report with fixed assets ("immobilisations et
    amortissements").
    """
    assets = []
    for transaction in session.query(Transaction).\
            filter_by(category=CATEGORY_EXPENDITURE_FIXED_ASSETS,
                      composite=False):
        amortization = accounting.calculate_amortization(transaction)
        this_year_index = year - transaction.year
        past = accounting.RoundedPrice(sum(amortization[:this_year_index]))
        try:
            this_year = amortization[this_year_index]
        except IndexError:
            this_year = 0  # already amortized
        asset = {'title': transaction.title,
                 'date': transaction.date,
                 'amount': accounting.RoundedPrice(abs(transaction.signed_amount)),
                 'vat': accounting.RoundedPrice(transaction.vat),
                 'base': accounting.RoundedPrice(abs(transaction.signed_amount) - transaction.vat),
                 'past': past,
                 'this_year': this_year}
        assets.append(asset)
    report['fixed_assets'] = {
        'assets': assets,
        'total_amount': accounting.RoundedPrice(sum(a['amount'] for a in assets)),
        'total_base': accounting.RoundedPrice(sum(a['base'] for a in assets)),
        'total_past': accounting.RoundedPrice(sum(a['past'] for a in assets)),
        'total_this_year': accounting.RoundedPrice(sum(a['this_year'] for a in assets))}


# FIXME: is this really needed? Should we not use 'calculate_vat_installments()' instead?
def _update_report_with_vat(report, lines):
    """Update report with total VAT for incomes and expenditures (not
    including fixed assets.
    """
    report['vat_incomes'] = accounting.RoundedPrice(
        sum(
            accounting.Price(l.vat) for l in lines if l.type == enums.TYPE_INCOME))
    report['vat_expenditures'] = accounting.RoundedPrice(
        sum(
            accounting.Price(l.vat) for l in lines if l.type == enums.TYPE_EXPENDITURE))
    report['vat_expenditures_fixed_assets'] = accounting.RoundedPrice(
        sum(
            accounting.Price(l.vat) for l in lines if l.category == CATEGORY_EXPENDITURE_FIXED_ASSETS))
    report['vat_expenditures_without_fixed_assets'] = accounting.RoundedPrice(
        sum(
            accounting.Price(l.vat) for l in lines if l.type == enums.TYPE_EXPENDITURE and \
                l.category != CATEGORY_EXPENDITURE_FIXED_ASSETS))


def autocomplete(request):
    field = request.matchdict['field']
    field = getattr(Transaction, field)
    session = DBSession()
    return [i[0] for i in session.query(field).filter(
            field.like('%%%s%%' % request.GET['term'])).distinct()]
