
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
