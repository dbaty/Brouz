import datetime

from deform.exception import ValidationFailure

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.renderers import render_to_response

from brouz.forms import make_composite_transaction_form
from brouz.forms import make_unique_transaction_form
from brouz.models import CATEGORY_EXPENDITURE_BANKING_CHARGES
from brouz.models import CATEGORY_EXPENDITURE_CET
from brouz.models import CATEGORY_EXPENDITURE_CONFERENCES
from brouz.models import CATEGORY_EXPENDITURE_DEDUCTIBLE_CSG
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
from brouz.i18n import _
from brouz.utils import TemplateAPI


def home(request):
    session = DBSession()
    lines = session.query(Transaction).filter_by(part_of=None, composite=False)
    lines = lines.union(session.query(Transaction).filter_by(composite=True))
    lines = lines.order_by(Transaction.date,
                           Transaction.party,
                           Transaction.title)
    balance = sum(i.signed_amount for i in lines)
    # FIXME: paginate
    api = TemplateAPI(request, 'home')
    bindings = {'api': api,
                'lines': lines,
                'balance': balance}
    return render_to_response('templates/home.pt', bindings)


def add_unique_form(request, form=None):
    if form is None:
        form = make_unique_transaction_form(request, _('Add transaction'))
    api = TemplateAPI(request, 'add')
    bindings = {'api': api,
                'form': form}
    return render_to_response('templates/add.pt', bindings)


def add_unique(request):
    form = make_unique_transaction_form(request, _('Add transaction'))
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return add_unique_form(request, e)
    data['composite'] = False
    data['part_of'] = None
    transaction = Transaction(**data)
    session = DBSession()
    session.add(transaction)
    request.session.flash(_('The transaction has been added.'), 'success')
    return HTTPSeeOther(request.route_url('home'))


def add_composite_form(request, form=None):
    if form is None:
        form = make_composite_transaction_form(request, _('Add transaction'))
    api = TemplateAPI(request, 'add')
    bindings = {'api': api,
                'form': form}
    return render_to_response('templates/add.pt', bindings)


def add_composite(request):
    form = make_composite_transaction_form(request, _('Add transaction'))
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return add_unique_form(request, e)
    total_amount = sum(l['amount'] for l in data['lines'])
    total_vat = sum(l['vat'] for l in data['lines'])
    composite = Transaction(party=data['party'],
                            title=data['title'],
                            date=data['date'],
                            category=data['lines'][0]['category'],
                            amount=total_amount,
                            vat=total_vat,
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
                        amount=line['amount'],
                        vat=line['vat'],
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
        if transaction.composite:
            form = make_composite_transaction_form(request, _('Save changes'))
            data = None  # 'FIXME'
            raise NotImplementedError
        else:
            form = make_unique_transaction_form(request, _('Save changes'))
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
    if transaction.composite:
        form = make_composite_transaction_form(request, _('Save changes'))
    else:
        form = make_unique_transaction_form(request, _('Save changes'))
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return edit_form(request, e)
    if transaction.composite:
        raise NotImplementedError
    else:
        data['composite'] = False
        data['part_of'] = None
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
    report['clients'] = session.execute(
        'SELECT party, SUM(amount) AS sum '
        'FROM transactions '
        'WHERE category=%d '
        'AND year=%d '
        'GROUP BY party '
        'ORDER BY sum DESC' % (CATEGORY_INCOME_MISC, year))
    report['providers'] = session.execute(
        'SELECT party, SUM(amount) AS sum '
        'FROM transactions '
        'WHERE category NOT IN (%d, %d) '
        'AND composite = 0 '
        'AND part_of IS NULL '
        'AND year=%d '
        'GROUP BY party '
        'ORDER BY sum DESC' % (
            CATEGORY_INCOME_MISC, CATEGORY_REMUNERATION, year))
    report['remuneration'] = session.query(
        Transaction.date, Transaction.amount).\
        filter_by(category=CATEGORY_REMUNERATION, year=year).\
        order_by(Transaction.date)
    report['total_remuneration'] = sum(
        r.amount for r in report['remuneration'])
    bindings = {'api': TemplateAPI(request, 'reports'),
                'year': year,
                'previous_year': previous_year,
                'next_year': next_year,
                'report': report}
    return render_to_response('templates/reports.pt', bindings)


def _get_sum_of_lines(lines, category):
    return sum(line.amount for line in lines if line.category == category)


def _calculate_report(lines):
    # Les commentaires correspondent aux intitules exacts de la
    # declaration 2035-1K (2012).
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
    # Petit outillage
    bh_small_furniture = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_SMALL_FURNITURE)
    # Primes d'assurance
    bh_insurance_premium = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_INSURANCE_PREMIUM)
    # Total : travaux, fournitures et services exterieurs
    bh = bh_small_furniture + bh_insurance_premium
    # Autres frais de deplacements (voyages...)
    bj_travel_expenses = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_TRAVEL_EXPENSES)
    # Total : transports et deplacements
    bj = bj_travel_expenses
    # Charges sociales personnelles obligatoires
    bt = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_OBLIGATORY_SOCIAL_CHARGES)
    # Charges sociales personnelles facultatives
    bu = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_OPTIONAL_SOCIAL_CHARGES)
    # Total charges sociales personnelles
    bk = bt + bu
    # Frais de reception, de representation et de congres
    bm_conferences = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_CONFERENCES)
    # Fournitures de bureau, frais de documentation, de correspondance
    # et de telephone
    bm_office = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_OFFICE_FURNITURE)
    # Autres frais divers de gestion
    bm_other = _get_sum_of_lines(
        lines, CATEGORY_EXPENDITURE_OTHER_MISC_EXPENSES)
    # Total : frais divers de gestion
    bm = bm_conferences + bm_office + bm_other
    # Frais financiers
    bn = _get_sum_of_lines(lines, CATEGORY_EXPENDITURE_BANKING_CHARGES)
    # Total (BR)
    total_expenditure = ba + bd + jy + bs + bv + bh + bj + bk + bm + bn
    report = {'aa': aa,
              'total_income': total_income,
              'ba': ba,
              'bd': bd,
              'jy': jy,
              'bs': bs,
              'bv': bv,
              'bh_small_furniture': bh_small_furniture,
              'bh_insurance_premium': bh_insurance_premium,
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
              'total_expenditure': total_expenditure,
              }
    return report


def autocomplete(request):
    field = request.matchdict['field']
    field = getattr(Transaction, field)
    session = DBSession()
    return [i[0] for i in session.query(field).filter(
            field.like('%%%s%%' % request.GET['term'])).distinct()]
