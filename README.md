# Dublin Bus Django App

A web app for predicting and displaying accurate bus travel times within the Dublin Bus network in Ireland.

## Technologies

- Django 3.2.4
- MySQL
- Bootstrap v5
- Jupyter Notebooks

## Instalation

### Backend

1. Make sure you have Anaconda or Miniconda installed. Miniconda is a minimal installer for conda. This will be useful to set up a virtual environment to install the requirements.

- To install Miniconda follow [link these instructions!(https://docs.conda.io/en/latest/miniconda.html)] acording to your operating system.

2. Use the package and environment manager [conda](https://docs.conda.io/en/latest/) to create a virtual environment with Python 3.8.

```bash
conda create --name <name_of_environment> python=3.8
```

3. Activate the environment.

```bash
conda activate <name_of_environment>
```

4. In the root folder of this project, install the `requirements.txt` file which has all the packages required for running the app.

```bash
pip install -r requirements.txt
```

#### Linting & formatting backend code

We use [Black](https://github.com/psf/black) to lint and format our Python code.
When `requirements.txt` is installed, Black will automatically be installed in the selected virtual environment.

If you change the backend code, please run the following command before committing new changes:

```bash
black .
```

### Frontend

#### Linting & formatting frontend code

We use `prettier` to lint frontend code (Javascript, HTML and CSS)
To run `prettier`:

1. Install node.js and npm (https://nodejs.org/en/ v14) (they come in the same installer);
2. Run `npm install -g prettier`
3. `sudo` might be needed to have write permissions
4. Run `prettier --write .` on the project folder

If you change the frontend/template code, please run the following command before committing new changes:

```bash
prettier --write .
```

## Running the Django app locally

To run the app locally execute the following commands:

```bash
cd dublinbus
python manage.py runserver
```
