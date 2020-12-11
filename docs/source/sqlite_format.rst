Working with SQLite files
=========================

Why SQLite?
-----------

* asynchronous support
* file locking
* on-the-fly sorting and retrieval

Working natively with SQLite files
----------------------------------

.. code-block:: text

    $ sqlite3 globalAveAtmos.db 

.. code-block:: text

    sqlite> .tables
    area       long_name  t_ref      units    

.. code-block:: text

    sqlite> select * from t_ref;
    1850|286.584833368
    1851|286.550367097
    1852|286.545788813
    ...
    2012|287.859330748
    2013|287.992293218
    2014|287.970241172
