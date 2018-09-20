
## Building flatc

To build the flatbuffers compiler (`flatc`) from sources:

```console
sudo apt install cmake

git clone https://github.com/google/flatbuffers.git
cd flatbuffers

git checkout master
git checkout v1.9.0

cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release
make
```

To check:

```console
oberstet@crossbar1:~/scm/3rdparty/flatbuffers$ ./flatc --version
flatc version 1.9.0 (Sep 20 2018 16:29:50)
```

## Building Demos

Source: https://github.com/crossbario/zlmdb/blob/master/zlmdb/flatbuffers/demo2.fbs

```
oberstet@crossbar1:~/scm/crossbario/zlmdb$ make flatc_version
/home/oberstet/scm/3rdparty/flatbuffers/flatc --version
flatc version 1.9.0 (Sep 20 2018 16:29:50)
oberstet@crossbar1:~/scm/crossbario/zlmdb$ make generate_flatbuffers_demos
/home/oberstet/scm/3rdparty/flatbuffers/flatc --python -o zlmdb/flatbuffers/ zlmdb/flatbuffers/demo1.fbs
/home/oberstet/scm/3rdparty/flatbuffers/flatc --python -o zlmdb/flatbuffers/ zlmdb/flatbuffers/demo2.fbs
oberstet@crossbar1:~/scm/crossbario/zlmdb$ find zlmdb/flatbuffers/demo/
zlmdb/flatbuffers/demo/
zlmdb/flatbuffers/demo/Date.py
zlmdb/flatbuffers/demo/User.py
zlmdb/flatbuffers/demo/survey
zlmdb/flatbuffers/demo/survey/Gender.py
zlmdb/flatbuffers/demo/survey/IceCreamOfTheDayReply.py
zlmdb/flatbuffers/demo/survey/Moo.py
zlmdb/flatbuffers/demo/survey/__init__.py
zlmdb/flatbuffers/demo/survey/IceCreamOfTheDaySurvey.py
zlmdb/flatbuffers/demo/Rating.py
zlmdb/flatbuffers/demo/accelstorage
zlmdb/flatbuffers/demo/accelstorage/AccelSeries.py
zlmdb/flatbuffers/demo/accelstorage/AccelBatch.py
zlmdb/flatbuffers/demo/accelstorage/AccelSeriesRejected.py
zlmdb/flatbuffers/demo/accelstorage/AccelSample.py
zlmdb/flatbuffers/demo/accelstorage/NoSuchSeries.py
zlmdb/flatbuffers/demo/accelstorage/__init__.py
zlmdb/flatbuffers/demo/accelstorage/TimeRange.py
zlmdb/flatbuffers/demo/Tag.py
zlmdb/flatbuffers/demo/__init__.py
oberstet@crossbar1:~/scm/crossbario/zlmdb$
```
