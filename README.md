# Shopping Assistant Project
Grocery shopping and making a shopping list can be such a drag. This machine learning-powered shopping list app helps autocomplete your shopping list by predicting items you are likely to add. The model is trained on real transactions using [data on Instacart customers’ prior orders](https://www.kaggle.com/c/instacart-market-basket-analysis/data). The app consists of an API back end (powered by Python and Flask) and web front end (powered by HTML, JavaScript, and React). As products are added to the list, the model tries to predict what additional items are likely to be added and suggest them.

![Screencap](https://user-images.githubusercontent.com/65802312/147989178-c2023e91-4bae-4658-b187-2e95c9358539.gif)

## What You Need to Get This Up and Running

There are two ways to run this locally. (Both have been tested on Ubuntu 23.04.)

### The Easiest Way

1. Get [Docker](https://docs.docker.com/engine/install/) or [Docker Desktop](https://docs.docker.com/desktop/).
2. Run `docker-compose up` from the project root and wait for the build/start-up process to finish.
3. Visit `http://localhost/` in your web browser.

### The Getting Your Hands Dirty Way

With Python 3.11 and Node.js 20 installed, do it all yourself! These instructions assume your terminal is opened up at the project root and that you can solve any other miscellaneous problems along the way.

#### Running the API

1. Create a Python venv under the `api` directory and activate it.
    1. `python3 -m venv api/venv`; and then
    2. `source api/venv/bin/activate`
2. Install the required Python packages with `pip install -r ./requirements.txt`.
3. Place the products table (`products.tsv`) and model (`suggestions.npz`) in the `api` directory. There are two ways to do so:
    1. `zpaq x api/data.zpaq -to api`, which unpacks those two files into the required directory; or
    2. Train a model yourself. See the subheading directly below for training options.
4. `cd api && flask run --no-debugger` to run the API server.

#### Training or Association Rule Mining

If you choose not to use the pre-trained model, do this before running the API server.

Download [`instacart-market-basket-analysis.zip` from Kaggle](https://www.kaggle.com/c/instacart-market-basket-analysis/data) and run the `api/preprocess_instacart_market_basket_analysis_data.py` script on it.

The script is tunable. Running the script with either the `-h` or `--help` arguments will show its usage text:

    usage: preprocess_instacart_market_basket_analysis_data.py [-h] [--input PATH] [--exclusions PATH] [--minsupport PERCENTAGE]
                                                               [--minconf PERCENTAGE] [--output PATH]

    Mines association rules from Instacart’s market basket analysis data. Download it from: https://www.kaggle.com/c/instacart-market-
    basket-analysis/data

    options:
      -h, --help            show this help message and exit
      --input PATH          the Instacart market basket analysis data set
      --exclusions PATH     a list of product identifiers to exclude
      --minsupport PERCENTAGE
                            the minimum support (as a percentage of transactions) for any rule under consideration
      --minconf PERCENTAGE  the minimum confidence for any rule under consideration
      --output PATH         the output directory to store the association rules and product list

`preprocess_instacart_market_basket_analysis_data.py --minsupport 0.0001 -- minconf 0.10` will:

1. Read the contents of `instacart-market-basket-analysis.zip` in the current directory.
2. Train on the data. 
    * The combination of items under consideration must appear in 0.01% of all transactions.
    * The candidate rule must be true at least 10% of the time.
3. Save `products.tsv` and `suggestions.npz` to the current directory.
    * `products.tsv` will contain product names decomposed down to their lemmas.
    * `suggestions.npz` will contain a pair of NumPy integer arrays which encode the association rules.

The training may require a lot of RAM and/or time depending on the training options and the computational resources available at your disposal. You’ve been warned!

#### The Frontend

5. `npm install` the packages.
6. `npm run start`.
7. Your browser should be automatically started and/or have a tab opened up to `http://localhost/`.

## Underneath the Hood

![Screenshot](https://user-images.githubusercontent.com/65802312/147992569-0664b770-4dd4-45dc-829f-6c164bfcc1d2.png)

### How it Works

#### Data

All that’s needed is a list of *transactions*. Think of each transaction as being the receipt you get after paying for your groceries at the supermarket. The data is essentially a huge pile of many, *many* such receipts.

#### Mining

It is then mined using the Apriori algorithm, an algorithm originally proposed by Rakesh Agrawal and Ramakrishnan Srikant in September 1994. The Apriori algorithm tries to find frequent item sets (e.g.: bacon, egg, and cheese) and generates a set of *association rules* from what it learns. Using these rules, an application can predict the likelihood of some items (*consequents*) being picked if some other items (*antecedents*) have already been picked. For example, having *bacon* and *eggs* in your shopping cart predicts the likely imminent inclusion of *cheese*.

The generated rules each comprise:

1. `antecedent_items` ($A$): the antecedents―the predictors of the consequent (e.g., *bacon* and *eggs*)
2. `consequent_item` ($B$): the consequent―something the antecedents predict (e.g., *cheese*)
3. `transaction_count`: the total number of transactions (e.g., 1,000,000 receipts in total)
4. `item_set_count`: the number of transactions containing the item set―the antecedents and consequent (e.g., 200,000 have *bacon*, *egg*, and *cheese*)
5. `antecedent_count`: the number of transactions containing the antecedents (e.g., 300,000 have *bacon* and *egg*)
6. `consequent_count`: the number of transactions containing the consequent (e.g., 400,000 have *cheese*)

The counts are used to derive the following metrics:

* The rule’s *support* tells you how frequently the set of items appears in the dataset. It’s important to prune infrequent sets from further consideration.
    * The simple definition: $$P(A \cap B)$$
    * `= item_set_count / transaction_count`
* The rule’s *confidence* tells you how often a the rule is true. Divide the support for the set of items by the support for just the antecedents. Rules which are not true very often are also pruned.
    * The simple definition: $$\frac{P(A \cap B)}{P(A)}$$
    * `= item_set_count / transaction_count / (antecedent_count / transaction_count)`
    * `= item_set_count / antecedent_count`
* The rule’s *lift* tells you how much more likely the consequent is, given the antecedents, compared to its baseline probability. Divide the support for the set of items by both the support of the antecedents and consequent. Equivalently, divide the confidence by the support of the consequent.
    * The simple definition: $$\frac{P(A \cap B)}{P(A) \cdot P(B)}$$
    * `= item_set_count / transaction_count / (antecedent_count / transaction_count * (consequent_count / transaction_count))`
    * `= item_set_count / antecedent_count / (consequent_count / transaction_count)`
    * `= item_set_count * transaction_count / (antecedent_count * consequent_count)`

Given the rule that *bacon* and *egg* predict *cheese*, derived from a data set with 1,000,000 transactions, 400,000 which have *cheese*, 300,000 which have both *bacon* and *egg*, and 200,000 which have all three, the following metrics can be computed using its above definitions:

* Support: $$\frac{200000}{1000000} = 0.20$$
* Confidence: $$\frac{0.20}{\frac{300000}{1000000}} \approx \frac{0.20}{0.30} \approx 0.67$$
* Lift: $$\frac{0.67}{\frac{400000}{1000000}} \approx \frac{0.67}{0.40} \approx 1.67$$

#### Making Predictions

To make predictions from the mined association rules, this application creates a set trie, mapping sets of antecedent items to sets of consequent items. When a list of antecedent items is provided as input, the set trie is queried for all sets which are subsets of the list, returning a set of consequent item sets which are then sorted in descending order by likelihood of being chosen.

#### Text Queries

For text query inputs, this application create a set trie mapping sets of words from the product name to products. When a text query is provided as input, the set trie is queried for all sets which are supersets of the query terms, returning a set of products which are then sorted by frequency in the transaction data. To reduce the memory usage of the set trie, words with the same root forms are collapsed into a single lemma and common stopwords are stripped out. Thus, *Chocolate Covered Strawberries* and *Strawberry Yogurt* are reduced to {*chocolate*, *cover*, *strawberry*} and {*strawberry*, *yogurt*} respectively—four unique words in total instead of five. 

This application takes care of typos and near-matches by performing fuzzy text matching. During start-up, it initializes a graph structure with all the words found in the product names.

#### Predictive Text Queries

When both antecedent items and text query terms are provided, the application intersects the two sets of results. Thus, the suggestions given are all products which match the text query and have the highest likelihood of being chosen based on the antecedent items.

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