from fast_autocomplete import AutoComplete
from functools import partial
from itertools import chain, filterfalse, groupby, starmap
import nltk
from nltk.corpus import stopwords, wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tag import pos_tag
from os.path import basename
import re
from settrie import SetTrieMap
import sys
from time import ctime, time
from toolz import compose_left as compose, identity, mapcat, merge_sorted, take, thread_last as thread, unique
from typing import Callable, Iterable, Optional
from models import Product, Suggestion
from repositories import ProductRepository, RulesRepository
from helpers import create_grouper, create_sorter, first, second, zipapply

class LemmatizerService:
    __numeric_re = r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:(\.|,)\d+)?'
    tokenize: Callable[[str], Iterable[str]] = \
        compose(re.compile('|'.join((fr'(?:(?<=^)|(?<=[\s(]))(?:#|No.?\s*){__numeric_re}\+?(?=,?\s|\)|$)',
                                     fr'(?:(?<=^)|(?<=[\s(])){__numeric_re}(?:(?:\'s|["\'+])|\s*(?:%|c(?:oun)t\.?|cups?'
                                     r'|(?:fl\.?\s)?oz\.?|in(?:\.|ch(?:es)?)?|lbs?\.?|mgs?\.?|only|ounces?|p(?:ac)?k'
                                     r'|pcs?\.?|pieces?|pounds?|size|x))?(?=,?\s|\)|$)',
                                     r'[^\s!"&()+,\-./:;?\[\]{}][^\s!"()+\-/:;?\[\]{}]*[^\s!"()+,\-./:;?\[\]{}®™]')))
                  .finditer,
                partial(map, re.Match.group))

    def __init__(self):
        LemmatizerService.__ensure_nltk_data(('corpora/omw-1.4',
                                              'corpora/stopwords',
                                              'corpora/wordnet',
                                              'taggers/averaged_perceptron_tagger',
                                              'tokenizers/punkt'))
        is_stopword = frozenset(stopwords.words('english')).__contains__
        lemmatizer = WordNetLemmatizer()

        def lemmatize_tagged_words(tagged_words: Iterable[tuple[str, Optional[str]]]) \
                -> Iterable[tuple[str, Optional[str]]]:
            for word, pos in tagged_words:
                if pos is not None and word != (lemma := lemmatizer.lemmatize(word, pos)):
                    yield lemma, word  # The lemmatized form takes precedence over the original.
                else:
                    yield word, None

        self.lemmatize: Callable[[str], Iterable[tuple[str, Optional[str]]]] = \
            compose(str.lower,
                    LemmatizerService.tokenize,
                    partial(filterfalse, is_stopword),
                    tuple,  # The next function does not work with Iterables, so it needs to be converted into a tuple.
                    pos_tag,  # Tag each token (or “word”) with a part of speech (POS).
                    LemmatizerService.__map_to_wordnet_pos,  # Map NLTK’s POS tags to WordNet’s tags.
                    lemmatize_tagged_words,
                    create_sorter(first),
                    unique)

    @staticmethod
    def __map_to_wordnet_pos(words: Iterable[tuple[str, str]]) -> Iterable[tuple[str] | tuple[str, str]]:
        for word, pos in words:
            match pos:
                case 'JJ' | 'JJR' | 'JJS' | 'PDT' | 'RP':
                    yield word, wn.ADJ
                case 'CD' | 'NN' | 'NNS' | 'NNP' | 'NNPS':
                    yield word, wn.NOUN
                case 'VB' | 'VBD' | 'VBG' | 'VBN' | 'VBP' | 'VBZ':
                    yield word, wn.VERB
                case 'EX' | 'IN' | 'RB' | 'RBR' | 'RBS':
                    yield word, wn.ADV
                case _:  # Other tags have no equivalent in WordNet.
                    yield word, None

    @staticmethod
    def __ensure_nltk_data(names: Iterable[str]) -> None:
        for name in names:
            try:
                nltk.data.find(name)
            except LookupError:
                nltk.download(basename(name))


class ProductLookupService:
    def __init__(self, product_repository: ProductRepository, rules_repository: RulesRepository,
                 lemmatizer_service: LemmatizerService) -> None:
        get_time_as_string = compose(time, ctime)
        lemmatize = lemmatizer_service.lemmatize

        # Index of product identifiers to product names
        print(f'[{get_time_as_string()}] Loading product names from {product_repository.products_data_file}…',
              file=sys.stderr)
        product_names = product_repository.get_all_products()

        # Single empty dictionary instance to avoid allocating dictionaries for the Autocomplete initializer
        empty_dictionary = {}

        # Autocompletion engine for text queries using words from product names
        synonyms = dict(map(lambda group: (group[0], list(unique(filter(None, map(lambda pair: pair[1], group[1]))))), groupby(sorted(chain.from_iterable(lemmatize(product) for product in product_names), key=lambda pair: pair if pair[1] else (pair[0], '')), lambda pair: pair[0])))
        autocompleter = \
            thread(synonyms,
                   (map, lambda word: (word, empty_dictionary)),
                   dict,
                   partial(AutoComplete, synonyms=synonyms))

        # Products sorted by product identifier, where each product is found at the index equal to its identifier
        products = tuple(Product(index, name)
                         for index, name in enumerate(product_names))
        del product_names
        print(f'[{get_time_as_string()}]  Loaded {len(products):,} products.',
              file=sys.stderr)

        # Association rules
        print(f'[{get_time_as_string()}] Loading association rules from {rules_repository.rules_data_file}…',
              file=sys.stderr)
        rules = rules_repository.get_all_rules()
        print(f'[{get_time_as_string()}]  Loaded {len(rules):,} association rules.',
              file=sys.stderr)

        # Index of sets of suggestions by antecedent items (maps sets of Products to sorted sets of Suggestions)
        print(f'[{get_time_as_string()}] Creating association rule-based suggestions indexed by antecedent item sets…',
              file=sys.stderr)
        suggestions_by_antecedent_items = \
            thread(rules,
                   (map, lambda rule: (tuple(map(products.__getitem__, rule.antecedent_items)),  # below as: rule[0],
                                       tuple(map(products.__getitem__, rule.consequent_items)),  #   │       rule[1],
                                       rule.measure)),                                           #   ▼   and rule[2]
                   create_grouper(first),
                   (map, partial(zipapply, (identity,
                                            compose(partial(mapcat, lambda rule: ((item, rule[2], rule[0])
                                                                                  for item in rule[1])),
                                                    partial(starmap, Suggestion),
                                                    sorted,
                                                    tuple)))),
                   SetTrieMap)
        del rules

        # Default product suggestions sorted in descending order of support (lift being exactly 1.0 for all Suggestions)
        default_suggestions = suggestions_by_antecedent_items.get(())

        # Index of sets of products by words in product names (maps sets of words to sorted sets of Suggestions)
        print(f'[{get_time_as_string()}] Creating search index by product name…',
              file=sys.stderr)
        suggestions_by_word = \
            thread(default_suggestions,
                   (map, lambda suggestion: (tuple(unique(map(first, lemmatize(suggestion.product.name)))),
                                             suggestion)),
                   create_sorter(first),  # Sort by Product word set.
                   create_grouper(first),  # Group by Product word set; it’s possible that several Products share a set.
                   (starmap, lambda words, pairs: (words, tuple(sorted(map(second, pairs))))),
                   SetTrieMap)

        def get_suggestions_by_words(words: Iterable[str]) -> set[Suggestion]:
            result = set()
            for word in words:
                for suggestions in suggestions_by_word.itersupersets(word, 'values'):
                    result.update(suggestions)
            return result

        self.__autocomplete: Callable[[str], list[str]] = autocompleter.search
        self.__default_suggestions: tuple[Suggestion, ...] = default_suggestions
        self.__get_product_by_identifier = products.__getitem__
        self.__get_suggestions_by_antecedent_items = partial(suggestions_by_antecedent_items.itersubsets, mode='values')
        self.__get_suggestions_by_words = get_suggestions_by_words
        self.__has_suggestions_by_antecedent_items = partial(suggestions_by_antecedent_items.hassubset)

        print(f'[{get_time_as_string()}] Product look-up service initialization completed.',
              file=sys.stderr)

    def __get_basket_suggestions(self, basket: frozenset[Product]) -> Optional[Iterable[Suggestion]]:
        if not self.__has_suggestions_by_antecedent_items(basket):
            return None
        return merge_sorted(*self.__get_suggestions_by_antecedent_items(basket))

    def __get_products_from_query(self, query: str) -> Optional[Iterable[Suggestion]]:
        if not query:
            return None
        terms = LemmatizerService.tokenize(query)
        suggestion_sets = (self.__get_suggestions_by_words(word)
                           for word in (self.__autocomplete(term)
                                        for term in terms))
        try:
            results = next(suggestion_sets)
        except StopIteration:
            return frozenset()
        for suggestions in suggestion_sets:
            results.intersection_update(suggestions)
        return results

    def get_suggestions(self, basket: Iterable[int] = frozenset(), query: str = '') -> list[Suggestion]:
        # Determine what to get suggestions for; execute only the code necessary to fulfill the request.
        query_suggestions = self.__get_products_from_query(query.strip())
        if basket:
            basket_products = frozenset(map(self.__get_product_by_identifier, basket))
            basket_suggestions = self.__get_basket_suggestions(basket_products)
        else:
            basket_suggestions = basket_products = None

        # Grab the relevant suggestions based on the request and whether results are available.
        match query_suggestions is None, basket_suggestions is None:
            case True, True:  # No query, and basket suggestions came up empty
                suggestions = self.__default_suggestions
            case True, False:  # No query, but there were some basket suggestions
                suggestions = chain(basket_suggestions, self.__default_suggestions)
            case False, True:  # Possible query results, but basket suggestions came up empty
                suggestions = sorted(query_suggestions)
            case _:  # Possible query results, and also basket suggestions
                query_products = frozenset(map(lambda suggestion: suggestion.product, query_suggestions))
                suggestions = filter(lambda suggestion: suggestion.product in query_products,
                                     chain(basket_suggestions, self.__default_suggestions))

        # Filter for 10 unique products.
        unique_suggestions = unique(suggestions, lambda suggestion: suggestion.product)
        if basket_products:
            unique_suggestions = filter(lambda suggestion: suggestion.product not in basket_products,
                                        unique_suggestions)
        return list(take(10, unique_suggestions))


__all__ = ('LemmatizerService', 'ProductLookupService')
