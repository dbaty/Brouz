# FIXME: add tests

from brouz.tests.base import TestCaseForViews


class TestHome(TestCaseForViews):

    def _call_fut(self, request):
        from brouz.views import home
        return home(request)

    # FIXME: add tests


class TestAddUniqueForm(TestCaseForViews):

    def _call_fut(self, request):
        from brouz.views import add_unique_form
        return add_unique_form(request)

    # FIXME: add tests


class TestAddUnique(TestCaseForViews):

    def _call_fut(self, request):
        from brouz.views import add_unique
        return add_unique(request)

    def test_add_unique_basics(self):
        from datetime import date
        from brouz.models import CATEGORY_EXPENDITURE_PURCHASE
        from brouz.models import PAYMENT_MEAN_CREDIT_CARD
        from brouz.models import Transaction
        from brouz.models import TYPE_EXPENDITURE
        post = {'party': u'Party',
                'title': u'Title',
                'date': '2011-01-01',
                'category': unicode(CATEGORY_EXPENDITURE_PURCHASE),
                'amount': '1234.56',
                'vat': '123.45',
                'mean': unicode(PAYMENT_MEAN_CREDIT_CARD),
                'invoice': u'INVOICE-01'}
        request = self._make_request(post=post)
        request.POST['csrf_token'] = request.session.get_csrf_token()
        self._call_fut(request)
        self.assertEqual(len(request.get_flash('success')), 1)
        self.assertEqual(len(request.get_flash('error')), 0)
        t = self.session.query(Transaction).one()
        self.assertEqual(t.party, post['party'])
        self.assertEqual(t.title, post['title'])
        self.assertEqual(t.date, date(2011, 1, 1))
        self.assertEqual(t.year, 2011)
        self.assertEqual(t.category, int(post['category']))
        self.assertEqual(t.type, TYPE_EXPENDITURE)
        self.assertEqual(t.amount, float(post['amount']))
        self.assertEqual(t.vat, float(post['vat']))
        self.assertEqual(t.mean, int(post['mean']))
        self.assertEqual(t.invoice, post['invoice'])
        self.assertEqual(t.composite, False)
        self.assertEqual(t.part_of, None)


class TestAddCompositeForm(TestCaseForViews):
    pass  # FIXME


class TestAddComposite(TestCaseForViews):

    def _call_fut(self, request):
        from brouz.views import add_composite
        return add_composite(request)

    def test_add_composite_basics(self):
        from datetime import date
        from brouz.models import CATEGORY_EXPENDITURE_PURCHASE
        from brouz.models import CATEGORY_EXPENDITURE_SMALL_FURNITURE
        from brouz.models import PAYMENT_MEAN_CREDIT_CARD
        from brouz.models import Transaction
        from brouz.models import TYPE_EXPENDITURE
        post = (('party', u'Party'),
                ('title', u'Title of the composite'),
                ('date', '2011-01-01'),
                ('mean', unicode(PAYMENT_MEAN_CREDIT_CARD)),
                ('invoice', u'INVOICE-01'),
                ('__start__', 'lines:sequence'),
                ('__start__', 'line:mapping'),
                ('title', u'Item 1'),
                ('category', unicode(CATEGORY_EXPENDITURE_PURCHASE)),
                ('amount', '100.00'),
                ('vat', '19.60'),
                ('__end__', 'line:mapping'),
                ('__start__', 'line:mapping'),
                ('title', u'Item 2'),
                ('category', unicode(CATEGORY_EXPENDITURE_SMALL_FURNITURE)),
                ('amount', '200.00'),
                ('vat', '11.00'),
                ('__end__', 'line:mapping'),
                ('__end__', 'lines:sequence'),
                )
        request = self._make_request(post=post)
        request.POST['csrf_token'] = request.session.get_csrf_token()
        self._call_fut(request)
        self.assertEqual(len(request.get_flash('success')), 1)
        self.assertEqual(len(request.get_flash('error')), 0)
        c = self.session.query(Transaction).\
            filter_by(composite=True).one()
        self.assertEqual(c.party, u'Party')
        self.assertEqual(c.title, u'Title of the composite')
        self.assertEqual(c.date, date(2011, 1, 1))
        self.assertEqual(c.year, 2011)
        self.assertEqual(c.category, CATEGORY_EXPENDITURE_PURCHASE)
        self.assertEqual(c.type, TYPE_EXPENDITURE)
        self.assertEqual(c.amount, 300.0)
        self.assertEqual(c.vat, 30.60)
        self.assertEqual(c.mean, PAYMENT_MEAN_CREDIT_CARD)
        self.assertEqual(c.invoice, u'INVOICE-01')
        t1 = self.session.query(Transaction).filter_by(title=u'Item 1').one()
        self.assertEqual(t1.title, u'Item 1')
        self.assertEqual(t1.category, CATEGORY_EXPENDITURE_PURCHASE)
        self.assertEqual(t1.amount, 100.0)
        self.assertEqual(t1.vat, 19.6)
        t2 = self.session.query(Transaction).filter_by(title=u'Item 2').one()
        self.assertEqual(t2.title, u'Item 2')
        self.assertEqual(t2.category, CATEGORY_EXPENDITURE_SMALL_FURNITURE)
        self.assertEqual(t2.amount, 200.0)
        self.assertEqual(t2.vat, 11.0)
        for t in (t1, t2):
            self.assertEqual(t.composite, False)
            self.assertEqual(t.part_of, c.id)
            self.assertEqual(t.party, c.party)
            self.assertEqual(t.date, c.date)
            self.assertEqual(t.year, c.year)
            self.assertEqual(t.type, c.type)
            self.assertEqual(t.mean, c.mean)
            self.assertEqual(t.invoice, c.invoice)
