# IW-SRAHC
>an Interactive Web-tool for Survival Risk Analysis based on Hierarchical Clustering

## How to run the web server

This web-tool is mainly finished in Python and HTML, a Linux operating system server is recommended. This deploy instruction is finished on centOS 7. In other environment and distribution versions of Linux, commands may be a little different. To run the web server, `Python3` and `MongoDB` must be installed correctly.

Make sure you have Python3 installed. The minimum version of Python is Python 3.7.x, you can confirm the version on your machine using this command:

```shell
python3 --version
```

Then download the source code of IW-SRAHC from GitHub. Choose a directory where you wish to run the server, and clone source code by using this command:

```shell
git clone https://github.com/wylapp/iwsrahc
```

and change into the directory `iwsrahc`

```shell
cd iwsrahc
```

Create a virtual environment for the server and activate it.

```shell
python3 -m virtualenv iwenv
source iwenv/bin/activate
```

If an error occurs saying that python do not have `virtualenv` module, that's very normal, Install one.

```shell
pip3 install virtualenv
```

The whole source code tree seems like this:

```
├── app
│   ├── CoreModules
│   ├── data
│   ├── docs
│   ├── plugins
│   ├── static
│   ├── templates
│   ├── uploadfiles
│   ├── utilities
│   └── views.py
├── requirements.txt
├── run.py
├── iwenv
    ├── bin
    ├── lib
    └── pyvenv.cfg
```

Then install all required packages.

```shell
pip3 install -r requirements.txt
```

Our embedded TCGA dataset was placed in `app/data` , however, it is too large and cannot be uploaded to GitHub. So you need to download it from our server and extract it into the `app/data` directory. You can download the dataset from this link: http://generalapi.top:84/index.php/s/8JZtg6SHGeqTCfT

To run the server, there's still one step, the `MongoDB` server needs more configurations. A GUI management software for MongoDB will simplify this work flow. First, you need to create a new database called `cluster_record`, then,  create two collections called `TCGA_list` and `cancers`. Download http://generalapi.top:84/index.php/s/7g4a7x3sXZQwdNG and extract the compressed file. Import two json files into the collection `cancers` and collection `TCGA_list`.

In `utilities/dburi.py`, there's an URI (universal resource index) of the `MongoDB` like this:

```python
pymongo.MongoClient("mongodb://server:port/")
```

you need to edit this URI to fit your DB server's configuration before running the web server. To run web server, use the following command:

```
python3 run.py
```

the default URL of the web-tool is `http://localhost:5000`, this can be changed in `run.py`.