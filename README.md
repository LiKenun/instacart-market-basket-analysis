# Shopping Assistant Project
Grocery shopping and making a shopping list can be such a drag. This machine learning-powered shopping list app helps autocomplete your shopping list by predicting items to be added. The model is trained on real transactions using [data on Instacart customers’ prior orders](https://www.kaggle.com/c/instacart-market-basket-analysis/data). The app consists of an API back end (powered by Python and Flask) and web front end (powered by HTML, JavaScript, and React). As products are added, the model tries to predict what additional items are likely to be added and suggest them.

![Screencap](https://user-images.githubusercontent.com/65802312/147989178-c2023e91-4bae-4658-b187-2e95c9358539.gif)

## What You Need to Get This Up and Running

A demo hosted on Heroku at [shopping-assistant-demo.herokuapp.com](https://shopping-assistant-demo.herokuapp.com/), but if you want it running locally there are several ways. This way has the least number of steps:

1. Get [Docker](https://www.docker.com/products/docker-desktop).
2. Run `docker-compose up` from the project root and wait for the build/start-up process to finish.
3. Visit `http://localhost/` in your web browser.

## Underneath the Hood

![Screenshot](https://user-images.githubusercontent.com/65802312/147992569-0664b770-4dd4-45dc-829f-6c164bfcc1d2.png)

### How it Works

#### Mining

The transactions data set is mined using the Apriori algorithm, an algorithm originally proposed by Rakesh Agrawal and Ramakrishnan Srikant in September 1994. The Apriori algorithm scans the transactions for frequent item sets (e.g.: bacon, egg, and cheese) and generates a set of *association rules*. Using these rules, an application can predict the likelihood of some items (*consequents*) being included in a transaction if some other items (*antecedents*) have already been included (e.g.: *bacon* and *egg* predicts *cheese*).

#### Making Predictions

To make predictions from the mined association rules, this application creates a set trie, mapping sets of antecedent items to sets of consequent items. When a list of antecedent items is provided as input, the set trie is queried for all sets which are subsets of the list, returning a set of consequent item sets which are then sorted by likelihood of inclusion.

#### Text Queries

For text query inputs, this application create a set trie mapping sets of words from the product name to products. When a text query is provided as input, the set trie is queried for all sets which are supersets of the query terms, returning a set of products which are then sorted by frequency in the transaction data. To reduce the memory usage of the set trie, words with the same root forms are collapsed into a single lemma and common stopwords are stripped out. Thus, *Chocolate Covered Strawberries* and *Strawberry Yogurt* are reduced to {*chocolate*, *cover*, *strawberry*} and {*strawberry*, *yogurt*} respectively—four unique words in total instead of five. 

This application takes care of typos and near-matches by performing fuzzy text matching. During start-up, it initializes a graph structure (provided by a library) with all the words found in the product names.

#### Predictive Text Queries

When both antecedent items and text query terms are provided, the application intersects the two sets of results. Thus, the suggestions given are all products which match the text query and have the highest likelihood of being included based on the antecedent items.

### Libraries/frameworks

This project was made possible with some great libraries:

* [Efficient-Apriori](https://github.com/tommyod/Efficient-Apriori) for mining the data set
* [Natural Language Toolkit (NLTK)](https://www.nltk.org/) to perform dimensionality reduction on product names
* [pysettrie](https://github.com/mmihaltz/pysettrie) for efficient look-up of values keyed on sets
* [Fast Autocomplete](https://github.com/seperman/fast-autocomplete) for fuzzy text queries
* [Flask](https://palletsprojects.com/p/flask/) for serving the API
* [PyToolz](https://github.com/pytoolz/toolz/) to enable functional programming patterns in Python
* [NumPy](https://numpy.org/) for efficient loading and in-memory representation of data
  * This library actually helped cut memory usage down from gigabytes down to hundreds of megabytes!
  * Load times also improved from tens of minutes to tens of seconds!
* [React](https://reactjs.org/) for the client-side user interface
* [zpaq](http://mattmahoney.net/dc/zpaq.html) compression to keep [the data file](https://github.com/LiKenun/shopping-assistant/blob/main/api/data.zpaq) from eating up precious storage
  * Files compressed with zpaq are nearly half the size of the LZMA-compressed ones!
* [Gunicorn](https://gunicorn.org/) to serve the app over HTTP

Each of those libraries/frameworks obviously depend on yet more libraries/frameworks. It’s a deep rabbit hole into which I extend my thanks…