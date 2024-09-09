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
├── Dataset            <- Links to download the datasets
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained model files
│
├── notebooks          <- Jupyter notebook runs
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         graphology and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│         
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment
│
├── setup.cfg          <- Configuration file for flake8
│
└── py_files           <- Source code for use in this project.
    
```

--------

