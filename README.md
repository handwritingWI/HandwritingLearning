# Using Deep Neural Networks in Writer Identification and Analysis

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

This repo contains the code and resources for our project focused on Writer Identification from images of individual handwritten words. We initially based our work on the GR-RNN model (https://github.com/shengfly/writer-identification), but have since enhanced it into a Transformer architecture to achieve better performance. 

## Dataset

The dataset can be downloaded from kaggle. 
Modern handwritten words, CERUG - https://www.kaggle.com/datasets/adityamajithia/cerug-en
Historical handwritten words, ICDAR2017 - https://www.kaggle.com/datasets/adityamajithia/icdar17-widewords

## Code

The code to reproduce the results presented in the paper is located in the 'py_files' folder.

## Instructions on running the code

### Download Datasets:
Download the required datasets and note the file paths.

### Prepare the Code:
Download all the Python scripts in the 'py_files' folder to a single directory.

### Set Dataset Paths:
Open the train_cte_cerug.py, train_cte_cerug_dataaug.py, and train_CTE_ICDAR17.py files, and update the train and test paths to point to the correct locations.

### Run the Code:
Commands for the execution of the Python scripts from terminal:
python train_cte_cerug.py
python train_cte_cerug_dataaug.py
python train_CTE_ICDAR17.py 


## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         graphology and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── graphology   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes graphology a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------

