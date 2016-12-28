MassivIU "bulk" insert/update/delete for Django
=======================================================

* Version : 1.0.0 - Beta 1
* Author : Thomas Weholt <thomas@weholt.org>
* License : Modified BSD.
* Status : Beta
* Url : https://github.com/weholt/massiviu.git


Background
----------

* MassivIU is a refactoring and update to the package known as DSE (https://github.com/weholt/DSE).
 
* It now supports Django 1.10.x and Python 3.5.

* MassivIU is available for one reason - to insert/update/delete lots of data -- as fast as possible.

* MassivIU vs Django ORM: typical speed gain is around 5x-10X for updates, 3X+ for inserts.

* MassivIU is aware of default values specified in your Django models and will use those if no value is given for a field in an insert statement.

* MassivIU caches SQL-statements, both inserts, updates and delete, and executes them when a specified number of statements has been prepared or when it`s told manually to flush cached statements to the database. The actual sql execution is done using DB API cursor.executemany and this is much faster than executing SQL-statements in sequence and way faster than using the Django ORM.

* MassivIU uses a dictionary to specify what fields to work on.


Note about MySQL
----------------

* Richard Brockie made me aware of some problems with MySQL InnoDb. It seems like MassivIU doesn't insert anything, but changing table type to MyISAM solves the problem allthough doing so will create other problems because InnoDb has a lot of nice features not found in MyISAM (http://stackoverflow.com/questions/20148/myisam-versus-innodb). Like Django itself I'm recommend using PostgreSQL.


Installation
------------

    pip install massiviu

or

    git clone https://github.com/weholt/massiviu
    cd massiviu
    python setup.py install


Example usage
-------------

You got a model like::

    gender =  (('M', 'Male'), ('F', 'Female'))
    
    class Person(models.Model):
        name = models.CharField(max_length = 30)
        age = models.IntegerField(default = 30)
        sex = models.CharField(max_length = 1, choices = gender, default = 'M')

Using MassivIU::

    from django.db import connection
    from massiviu import MassContext

    with MassContext(Person, connection) as cntx:
        for name, age, sex in (('Thomas', 36, 'M'), ('Joe', 40, 'M'), ('Jane', 28, 'F')):
             cntx.insert(dict(name = name, age = age, sex = sex))

Nothing will be inserted into the database before the loop is done ( or you 
insert 1000 items ). Then the items will be inserted using cursor.executemany, 
using plain SQL - no ORM in sight.

MassivIU using default values defined in your model::
    
    with MassContext(Person, connection) as cntx:
        # Adding an item, just defining a name and using the default values from the model:
        cntx.insert({'name': 'John'})

        # Overriding the default values? Just specify a valid value
        cntx.insert({'name': 'Thomas', 'age': 36, 'sex': 'M'})

        # Update record with id = 1 and set its name to John. This will trigger 
        # a SQL-statement for this update alone, since not all columns are specified:
        cntx.update({'id': 1, 'name': 'John'})

Say you want to update all records with some calculated value, something you 
couldn't find a way to do in SQL. Using MassivIU this is easy and fast::

    with MassContext(Person, connection) as cntx:
        # Use Djangos ORM to generate dictionaries to use in MassivIU; objects.all().values().
        for item in Person.objects.all().values():
            cntx.update(dict(id=item.get('id'), somevar=calculated_value))

I've recieved some questions about transaction handling. Below is an simple example,
but I`m looking into other ways of handling transactions as well::
 
    from django.db import transaction
    import MassivIU

    def some_method():
        with transaction.commit_on_success():
            with MassContext(Person, connection) as cntx:
                for item in somelist:
                    cntx.insert({'some_column': item.some_value, 'another_column': item.another_value})    

You can also cache items to delete::

    with MassContext(Person, connection) as cntx:
        for person in person.objects.all():
            if person.likes_perl_more_than_python:
                cntx.delete(person.id) # won't trigger anything
    # here all cached items for deletions are deleted using plain SQL, no orm.
        
MassivIU caches id's and deletes them when 1000 items are cached or flush/close are called.
It uses sql similar to "delete from tablename where id in (<list of ids>)".

MassivIU provides a special bulk_update-method. It takes a dictionary of values to update,
requires a value for the primary key/id of the record, but uses the django orm's own update method
instead of plain sql to reduce number of statements to execute. This is helpful when your fields can
have a limited set of values, like EXIF-data from photos. An example::

    with MassContext(Photo, connection) as cntx:
        cntx.update({'id': 1, 'camera_model': 'Nikon', 'fnumber': 2.8, 'iso_speed': 200})
        cntx.update({'id': 2, 'camera_model': 'Nikon', 'fnumber': 11, 'iso_speed': 400})
        cntx.update({'id': 3, 'camera_model': 'Nikon', 'fnumber': 2.8, 'iso_speed': 400})
        cntx.update({'id': 4, 'camera_model': 'Canon', 'fnumber': 3.5, 'iso_speed': 200})
        cntx.update({'id': 5, 'camera_model': 'Canon', 'fnumber': 11, 'iso_speed': 800})
        cntx.update({'id': 6, 'camera_model': 'Pentax', 'fnumber': 11, 'iso_speed': 800})
        cntx.update({'id': 7, 'camera_model': 'Sony', 'fnumber': 3.5, 'iso_speed': 1600})
        # and then some thousand more lines like that

Internally MassivIU will construct a structure like this::

    bulk_updates = {
        'camera_model': {
                'Nikon': [1,2,3],
                'Canon': [4,5],
                'Pentax': [6],
                'Sony': [7],
            },
        'fnumber': {
                2.8: [1,3],
                11: [2,5,6],
                3.5: [4,7],
            },
        'iso_speed': {
                200: [1,4],
                400: [2,3],
                800: [5,6],
                1600: [7]
        }
    }

And then execute those statements using::

    # pk = the primary key field for the model, in most cases id
    for field, values in bulk_updates.iteritems():
        for value, ids in values.iteritems():
            model.objects.filter(**{"%s__in" % pk: ids}).update(**{field: value})

For huge datasets where the fields can have limited values this has a big impact on performance. So when to use
update or bulk_update depends on the data you want to process. For instance importing a contact list where most
of the fields had almost unique values would benefit from the update-method, but importing data from photos, id3-tags
from your music collection etc would process much faster using bulk_update.

By default MassivIU provides no validation and extracts no such info from your models, 
but by using the MassivIU value validator you can clean up and validate your data as they're being added::

        def value_validator(values):
            if 'name' in values and len(values.get('name')) > 20:
                values['name'] = values['name'][:20]
            return values

        with MassContext(foo, connection, value_validator) as cntx:
            cntx.insert({'name': 'Thomas'*50, 'age': 36, 'sex': 'M'})

And that's all you have to do. Your method value_validator-method will be called each time you add a set of values. 
If you want to abort if any invalid data is found just raise an exception.


Release notes 
-------------

1.0.0 Beta 1: Refactoring, renaming, updates to support django 1.10.x and python 3.5. 

Old DSE release notes to give credit to contributors 
----------------------------------------------------

4.0.0 Beta 1: cleaned up and added some new unittests. Tested using Python 3.3/2.7 and Django 1.6.x.

4.0.0-RC3 : Code clean-up. Nothing new. Preparing moving to github.

4.0.0-RC2 : Bugfix for Django 1.6 running under Python 3.x. A note on MySQL InnoDB vs MyISAM.

4.0.0-RC1 : First steps towards Python 3.x and Django 1.5 support.

4.0.0-pre : port to Python 3.x.

3.1.0 : patch from rassminus; Changed sql creation to quote all references to the table name and column labels.

3.0.0 : clean up and release.

3.0.0-BETA#3 : clean-up/validation decorator and optional cursor caching.

3.0.0-BETA#2 : fixed a few things reported by Fido Garcia.

3.0.0-BETA#1 : refactoring, removal of code, new methods for insert and update, removal of the add, execute and several other methods. UPDATE-code
        optimized.

2.1.0 : Small change; MassivIU.patch_models can now take an optional list of models to patch, like so MassivIU.patch_models(specific_models=[User, Comment]).

2.0.0 : labeled as stable. Updated docs and examples.

2.0.0-RC1 : no change in code, now released using the modified BSD license to be more compatible with django license use.

2.0.0-BETA#9 : added FileExport-class to ease debugging what is processed during testing. Writes SQL-data to file. See source/testsuite for usage.

2.0.0-BETA#4 : started refactoring MassivIU to remove all non-django specific code, mostly to gain speed and simply code.

1.0.2 : reconnect if cursor is dead.

1.0.1 : fixed issue #9 "Factory can eat up memory" reported by vangheem. When finding fields related to a table only the top row is fetched.

1.0.0 : Version bump. Added unittest for issue #8.

1.0.0-RC1 : updated README.txt. 

0.9.4 : - PEP8 and pyflake.

0.9.3 : - Fixed issue #7: MassivIU causes django-debug-toolbar to crash. Thanks to ringemup for pointing that out. Added some docstrings.

0.9.2 : - Corrected type in usage.rst and README.txt.

0.9.1 : - Refactored code even more, added usage.rst, singleton support in the singleton-package and some performance tests. Models not monkey patched be default anymore, must call MassivIU.patch_models().

0.9.0 : - Refactored code and cleaned up tests folder. Focus on getting singleton support in before 1.0.0. And more tests.

0.8.2 : - added 'pysqlite2' to _DBMAP. Thanks to David Marble for 0.8.1 and 0.8.2.

0.8.1 : - attempt to fix quoting problems with fields on postgresql.

0.8.0 : - fixed crash when more than one database connection has been configured. No ModelFactory will be triggered.

0.7.0 : - don`t remember.

0.6.0 : - added support for the with-statement.
        - added an ModelDelayedExecutor-instance to each model, so you can do Model.MassivIU.add_item
          instead of MassivIU.ModelFactory.Model.add_item.
        - renamed MassivIU.modelfactory to MassivIU.ModelFactory to be more style-compliant.

0.5.1 : just some notes on transaction handling.

0.5.0 :
    - added modelfactory. Upon first import a modelfactory will be created in the MassivIU module. It`s basically just a helper-class containing ModelDelayedExecutor-instances for all models in all apps found in INSTALLED_APPS in settings.py.
    - to change the default item limit before automatic execution of cached SQL statements to 10000 instead of the default 1000: import MassivIU; MassivIU.ITEM_LIMIT = 10000

0.4.0 :
    - fixed serious bug when using mass updates. Using cursor.executemany is only possible when values for all columns are specified. If only values for a subset of the columns is specified that will be executed as a seperate SQL-call. NOTE! Using dex.get_items() or Djangos Model.objects.values() will give you all the fields.
    - code clean-up.
    - added custom exceptions; UpdateManyException, UpdateOneException and InsertManyException.
    - added setter for the cursor-property. Thanks to jetfix (https://bitbucket.org/jetfix).
