# Shopping Assistant Project
Grocery shopping and making a shopping list can be such a drag. This machine learning-powered shopping list app helps autocomplete your shopping list by predicting items to be added. The model is trained on real transactions using [data on Instacart customers’ prior orders](https://www.kaggle.com/c/instacart-market-basket-analysis/data). The app consists of an API back end (powered by Python and Flask) and web front end (powered by HTML, JavaScript, and React). As products are added, the model tries to predict what additional items are likely to be added and suggest them.

![Screencap](https://user-images.githubusercontent.com/65802312/147989178-c2023e91-4bae-4658-b187-2e95c9358539.gif)

## What You Need to Get This Up and Running

There are three major groups of steps to be aware of:
 1. Getting the software enviroment set up.
 2. Training a model from the data.
 3. Running the app.

### Hardware

But first, you need to have sufficiently powerful hardware to train the model. For good results, 32~64 GiB of RAM is recommended as the training algorithm will be very RAM-hungry. The resulting model will take up a few megabytes of storage depending on your training parameters.

### Software

With hardware requirements met, there are a few ways to get the app up and running. But this way has the least number of steps:

1. Get [Python 3.10](https://www.python.org/downloads/release/python-3101/).
2. Open up a terminal and `cd` to the `./api` subdirectory. Most of the work will take place entirely within it. (Do not `cd` anywhere else!)
3. Create a virtual environment using `python3 -m venv venv`. (Read more about virtual environments at [docs.python.org/3/library/venv.html](https://docs.python.org/3/library/venv.html).)
4. Run the virtual environment activation script. The script’s location/name will differ depending on your platform. `./venv/Scripts/activate` works on a Windows system. (On Linux, `Scripts` will be `bin` instead.)
5. Run `pip install -r requirements.txt` to install the required Python libraries. ([You should not have a problem unless your Python somehow does not come with pip.](https://pip.pypa.io/en/stable/installation/))
6. Get the Instacart basket analysis data set (as a 201 MB zip file containing 7 more zip files within) from Kaggle at [kaggle.com/c/instacart-market-basket-analysis/data](https://www.kaggle.com/c/instacart-market-basket-analysis/data). (You will need to create an account.)
7. Run the preprocessing script `python preprocess_instacart_market_basket_analysis_data.py`. This is the RAM-hungry training process. If the script runs out of memory, you can reduce its memory usage by raising the minimum support parameter using `--minsupport 0.0005` where `0.0005` is a real value between 0 and 1. The defaults will require 32 GiB of RAM, a few hours of CPU time, and 10 MB of storage. Thankfully, this step only has to be done once (as opposed to every time the API server is started).
8. Get [Docker](https://www.docker.com/products/docker-desktop).
9. Run `docker-compose up` from the project root and wait for the build/start-up process to finish.
10. Visit `http://localhost/` in your web browser.

## Underneath the Hood

![Screenshot](https://user-images.githubusercontent.com/65802312/147992569-0664b770-4dd4-45dc-829f-6c164bfcc1d2.png)

### Libraries/frameworks

* [Efficient-Apriori](https://github.com/tommyod/Efficient-Apriori) for mining the data set
* [Natural Language Toolkit (NLTK)](https://www.nltk.org/) to perform dimensionality reduction on product names
* [pysettrie](https://github.com/mmihaltz/pysettrie) for efficient look-up of values keyed on sets
* [Fast Autocomplete](https://github.com/seperman/fast-autocomplete) for fuzzy text queries
* [Flask](https://palletsprojects.com/p/flask/) for serving the API
* [PyToolz](https://github.com/pytoolz/toolz/) for to enable functional programming patterns in Python
* [dataclass-type-validator](https://github.com/levii/dataclass-type-validator) for …the obvious
* [React](https://reactjs.org/) for the client-side user interface

Each of those libraries/frameworks obviously depend on yet more libraries/frameworks. It’s a deep rabbit hole. 🐰
