# -*- coding: latin-1 -*-
import random
import unittest
import time

import configure_app
configure_app.configure('tests')

from db_context import DbContext
from item_cache import ItemCache
from model_context import ModelContext
from context import MassContext
from exceptions import PrimaryKeyInInsertValues, PrimaryKeyMissingInInsertValues

from django.test.utils import setup_test_environment, teardown_test_environment
from django.db import connection

from tests.models import foo, foobar, Child, ModelWithSQLKeywordAsField, WiktionaryPage, Photo, ModelWithValidation


class TestOperations(object):
    def execute_sql(self, item_cache):
        pass


class test_model_context(unittest.TestCase):

    def setUp(self):
        setup_test_environment()

    def tearDown(self):
        teardown_test_environment()

    def test_model_context1(self):
        db_context = DbContext(connection)
        m = ModelContext(foo, db_context)


class testMassiviu(unittest.TestCase):

    def setUp(self):
        setup_test_environment()

    def tearDown(self):
        teardown_test_environment()
        foo.objects.all().delete()
        foobar.objects.all().delete()

    def test_value_validator(self):
        def value_validator(values):
            if 'name' in values and len(values.get('name')) > 20:
                values['name'] = values['name'][:20]
            return values

        with MassContext(foo, connection, value_validator) as cntx:
            cntx.insert({'name': 'Thomas'*50, 'age': 36, 'sex': 'M'})
        obj = foo.objects.first()
        self.assertEqual(len(obj.name), 20)

    def test_ItemCache(self):
        db_context = DbContext(connection)
        m = ModelContext(foo, db_context)
        x = ItemCache(m, TestOperations())
        for i in range(998):
            x.insert({'name': 'John Doe #%s' % i})
        self.assertEqual(x.item_counter, 998)
        for i in range(5):
            x.insert({'name': 'John Doe #%s' % i})
        self.assertEqual(x.item_counter, 4)

    def test_update(self):
        with MassContext(foo, connection) as cntx:
            cntx.insert({'name': 'John Doe #1'})
        self.assertEqual(foo.objects.all().count(), 1)
        id = foo.objects.first().id
        with MassContext(foo, connection) as cntx:
            cntx.update({'name': 'Thomas Weholt', 'id': id})
        self.assertEqual(foo.objects.get(id=id).name, 'Thomas Weholt')

    def test_values_factory_for_model(self):
        db_context = DbContext(connection)
        model_cnxt = ModelContext(foo, db_context)
        self.assertTrue(model_cnxt.default_values['sex'] == "M")
        self.assertTrue(model_cnxt.default_values['age'] == 20)
        self.assertTrue(model_cnxt.default_values.get('id', None) == None)

    def test_add_item(self):
        with MassContext(foo, connection) as cntx:
            cntx.insert({'name': 'Thomas', 'age': 36, 'sex': 'M'})
        self.assertTrue(foo.objects.all().count() == 1)

    def test_delete_item(self):
        with MassContext(foo, connection) as cntx:
            cntx.insert({'name': 'Thomas', 'age': 36, 'sex': 'M'})
        self.assertTrue(foo.objects.all().count() == 1)
        with MassContext(foo, connection) as cntx:
            cntx.delete(foo.objects.all()[0].id)
        self.assertTrue(foo.objects.all().count() == 0)

    def test_add_itemUsingModelDelayedExecutorUsingDefaults(self):
        with MassContext(foo, connection) as cntx:
            cntx.insert({'name': 'Thomas'})
        foo_record = foo.objects.all()[0]
        self.assertTrue(foo_record.age == 20)
        self.assertTrue(foo_record.sex == "M")

    def test_add_itemUsingCallableDefaultValue(self):
        with MassContext(foobar, connection) as cntx:
            cntx.insert({'number': 1})
        time.sleep(0.5)
        with MassContext(foobar, connection) as cntx:
            cntx.insert({'number': 2})
        item1 = foobar.objects.all()[0]
        item2 = foobar.objects.all()[1]
        self.assertTrue(item1.dt != item2.dt)

    def insertPersons(self, person_count):
        with MassContext(foo, connection) as cntx:
            for i in range(0, person_count):
                cntx.insert({'name': 'Person%s' % i, 'age': i})

    def test_reset_for_model(self):
        with MassContext(foo, connection) as cntx:
            for i in range(0, 10):
                cntx.insert({'name': 'Person%s' % i, 'age': i})
            cntx.reset()
        self.assertTrue(foo.objects.all().count() == 0)

    #
    #         # def test_sql_injection(self):
    #         # thanks to Cal Leeming @ Simplicity Media Ltd
    #         # """check out 'sqlmap',  http://sqlmap.sourceforge.net/doc/README.html#ss5.5
    #         # Here is a bunch of common injection techniques:
    #         # http://www.unixwiz.net/techtips/sql-injection.html"""
    #         # Write some tests here ...
    #
    def test_escaping_of_quotation_chars(self):
        with MassContext(foo, connection) as cntx:
            cntx.insert({'name': '"pony"'})
            cntx.insert({'name': "'pony'"})
            cntx.insert({'name': "`pony`"})
        self.assertTrue(foo.objects.all().count() == 3)

    def test_nonexisting_fields(self):
        # TODO : write some validation code and optionally crash on invalid data?
        with MassContext(foo, connection) as cntx:
            cntx.insert({'nosuchfield': 'Foo', 'anotherfield': 1, 'name': 'footest', 'age': 30})
        self.assertTrue(foo.objects.all().count() == 1)

    def test_update_only_update_specified_fields(self):
        params = {'name': 'Thomas', 'age': 36, 'sex': 'M'}
        with MassContext(foo, connection) as cntx:
            cntx.insert(params)
        object_id = foo.objects.first().id
        with MassContext(foo, connection) as cntx:
            cntx.update({'name': 'Thomas Weholt', 'id': object_id})

        updated_foo = foo.objects.all()[0]
        for k, v in {'id': object_id, 'name': 'Thomas Weholt', 'age': 36, 'sex': 'M'}.items():
            self.assertTrue(hasattr(updated_foo, k))
            self.assertTrue(getattr(updated_foo, k) == v)

    def test_bulk_update(self):
        params = {'name': 'Thomas', 'age': 36, 'sex': 'M'}
        with MassContext(foo, connection) as cntx:
            cntx.insert(params)
        object_id = foo.objects.first().id
        with MassContext(foo, connection) as cntx:
            cntx.bulk_update({'name': 'Thomas Weholt', 'id': object_id})

        updated_foo = foo.objects.first()
        for k, v in {'id': object_id, 'name': 'Thomas Weholt', 'age': 36, 'sex': 'M'}.items():
            self.assertTrue(hasattr(updated_foo, k))
            self.assertTrue(getattr(updated_foo, k) == v)

    def test_update_specific_fields(self):
        self.insertPersons(1)
        foo_id = foo.objects.first().id
        with MassContext(foo, connection) as cntx:
            cntx.update({'id': foo_id, 'name': 'Jo'})
        self.assertTrue(foo.objects.get(id=foo_id).name == 'Jo')

    def test_with_statement2(self):
        s = "was his name o'"
        self.insertPersons(10)
        with MassContext(foo, connection) as cntx:
            for item in foo.objects.all().values():
                cntx.update({'id': item.get('id'), 'name': "%s %s" % (item['name'], s)})
        self.assertTrue(s in foo.objects.all()[0].name)

    def test_implementing_subclass(self):
        with MassContext(Child, connection) as cntx:
            for i in range(100):
                cntx.insert({'name': 'Whatever', 'age': random.randint(1, 20), })

    def test_sql_keyword_escaping(self):
        # "key" is a reserved word in SQL; for successful inserts/updates,
        # it must be escaped by Massiviu
        with MassContext(ModelWithSQLKeywordAsField, connection) as cntx:
            cntx.insert(dict(key=1, where='select', update='*;'))
        record = ModelWithSQLKeywordAsField.objects.get()
        with MassContext(ModelWithSQLKeywordAsField, connection) as cntx:
            cntx.update(dict(update=';update where', id=record.pk))

    def test_pk_field_is_autofield(self):
        with MassContext(foo, connection) as cntx:
            # Django's default PK
            self.assertEqual('id', cntx.model_context.pk)
            # The PK is an AutoField
            self.assertTrue(cntx.model_context.pk_is_auto_field)
            # Raise "PrimaryKeyInInsertValues" as expected
            self.assertRaises(PrimaryKeyInInsertValues, cntx.insert, {'id': 1, 'name': u"John Doe"})

    def test_pk_field_is_not_autofield(self):
        with MassContext(WiktionaryPage, connection) as cntx:
            # The PK is still recognized
            self.assertEqual('id', cntx.model_context.pk)
            # The PK is not the AutoField generated by Django
            self.assertFalse(cntx.model_context.pk_is_auto_field)
            # Don't raise "PrimaryKeyInInsertValues" even if given
            cntx.insert({'id': 1234, 'title': u"django"})
        # Django didn't set the pk itself, else it would be "1"
        page = WiktionaryPage.objects.get(pk=1234)
        self.assertEqual(u"django", page.title)
        # Oops! didn't capitalize a proper name
        with MassContext(WiktionaryPage, connection) as cntx:
            # Forgot to give the PK
            self.assertRaises(PrimaryKeyMissingInInsertValues, cntx.update, {'title': u"Django"})
            cntx.update({'id': 1234, 'title': u"Django"})
        page = WiktionaryPage.objects.get(pk=1234)
        self.assertEqual(u"Django", page.title)


class PerformanceTestMassiviu(unittest.TestCase):

    def setUp(self):
        setup_test_environment()

    def tearDown(self):
        foo.objects.all().delete()
        teardown_test_environment()

    def insertPersons(self, person_count):
        with MassContext(foo, connection) as cntx:
            for i in range(0, person_count):
                cntx.insert({'name': 'Person%s' % i, 'age': i})

    def test_SpeedReport_LotsOfInsertsUsingMassiviu(self):
        start_Massiviu = time.time()
        self.insertPersons(5000)
        stop_Massiviu = time.time()
        print("Using Massiviu took %s seconds." % (stop_Massiviu - start_Massiviu))

    def test_SpeedReport_LotsOfInsertsUsingOrm(self):
        start_orm = time.time()
        for i in range(0, 5000):
            foo(name='Person%s' % i, age=i).save()
        stop_orm = time.time()
        print("Using orm took %s seconds." % (stop_orm - start_orm))

    def test_SpeedReport_lotsOfGetAndUpdateUsingMassiviu(self):
        self.insertPersons(10000)
        start_Massiviu = time.time()
        with MassContext(foo, connection) as cntx:
            for item in foo.objects.all().values():
                item['name'] = "%s Doe" % item['name']
                cntx.update(item)
        stop_Massiviu = time.time()
        print("Using Massiviu took %s seconds." % (stop_Massiviu - start_Massiviu))

    def test_SpeedReport_lotsOfGetAndUpdateUsingOrm(self):
        self.insertPersons(10000)
        start_Massiviu = time.time()
        for item in foo.objects.all():
            item.name = "%s Doe" % item.name
            item.save()
        stop_Massiviu = time.time()
        print("Using orm took %s seconds." % (stop_Massiviu - start_Massiviu))

    def test_SpeedReportForUpdatesUsingMassiviu(self):
        self.insertPersons(5000)
        start_Massiviu = time.time()
        with MassContext(foo, connection) as cntx:
            for item in foo.objects.all().values():
                item['age'] += 10
                cntx.update(item)
        stop_Massiviu = time.time()
        print("Using Massiviu took %s seconds." % (stop_Massiviu - start_Massiviu))

    def test_SpeedReportForUpdatesUsingOrm(self):
        self.insertPersons(5000)
        start_orm = time.time()
        for item in foo.objects.all():
            item.name = "Person_%s" % item.id
            item.age += 10
            item.save()
        stop_orm = time.time()
        print("Using orm took %s seconds." % (stop_orm - start_orm))

    def test_deletion_queue(self):
        self.insertPersons(100)
        start = time.time()
        with MassContext(foo, connection) as cntx:
            for item in foo.objects.all().values():
                cntx.delete(item.get('id'))
        self.assertTrue(foo.objects.all().count() == 0)
        print("Took %s seconds to delete 10000 persons using Massiviu." % (time.time() - start))
        start = time.time()
        self.insertPersons(100)
        for p in foo.objects.all():
            p.delete()
        print("Took %s seconds to delete 10000 persons using orm." % (time.time() - start))

    def test_bulk_updates(self):
        camera_models = ('Nikon', 'Canon', 'Fujifilm', 'Panasonic', 'Sony', 'Leica', 'Pentax')
        with MassContext(Photo, connection) as cntx:
            for i in range(0, 1000):
                cntx.insert({'filename': 'photo%s.jpg' % i, 'camera_model': 'Not set'})

        photo_to_camera_model_mapping = {}
        for i in range(0, 1000):
            photo_to_camera_model_mapping[i] = camera_models[random.randint(0, len(camera_models) - 1)]
        photo_to_rating_mapping = {}
        for i in range(0, 1000):
            photo_to_rating_mapping[i] = random.randint(0, 6)

        pks = [p.id for p in Photo.objects.all()]
        start = time.time()
        for i in pks:
            p = Photo.objects.get(id=i)
            p.camera_model = photo_to_camera_model_mapping.get(i, 'Not set')
            p.rating = photo_to_rating_mapping.get(i, 0)
            p.save()
        print("Took %s seconds to update 999 photos using orm." % (time.time() - start))
        Photo.objects.all().update(camera_model='Not set', rating=0)
        start = time.time()
        with MassContext(Photo, connection) as cntx:
            for i in pks:
                cntx.bulk_update({
                    Photo._meta.pk.name: i,
                    'camera_model': photo_to_camera_model_mapping.get(i, 'Not set'),
                    'rating': photo_to_rating_mapping.get(i, 0)
                })
        print("Took %s seconds to update 999 photos using Massiviu." % (time.time() - start))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(test_model_context)
    unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(testMassiviu)
    unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(PerformanceTestMassiviu)
    unittest.TextTestRunner(verbosity=2).run(suite)
