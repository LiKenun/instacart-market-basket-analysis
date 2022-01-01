import contractions
from fast_autocomplete import AutoComplete
from functools import partial, reduce
from itertools import chain, starmap
import nltk
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tag import pos_tag
from os.path import basename
import re
from settrie import SetTrieMap
from toolz import compose_left as compose, first, juxt, mapcat, merge_sorted, second, take, \
                  thread_last as thread, unique
from typing import Callable, Collection, Iterable, Optional
from models import Product, Rule, Suggestion
from repositories import ProductRepository, RulesRepository
from helpers import create_grouper, create_sorter, star, zipapply


class LemmatizerService:
    __numeric_re = r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:(\.|,)\d+)?'
    __find_tokens: Callable[[str], Iterable[str]] = \
        compose(re.compile('|'.join((fr'(?:(?<=^)|(?<=[\s(]))(?:#|No.?\s*){__numeric_re}\+?(?=,?\s|\)|$)',
                                     fr'(?:(?<=^)|(?<=[\s(])){__numeric_re}(?:(?:\'s|["\'+])|\s*(?:%|c(?:oun)t\.?|cups?'
                                     r'|(?:fl\.?\s)?oz\.?|in(?:\.|ch(?:es)?)?|lbs?\.?|mgs?\.?|only|ounces?|p(?:ac)?k'
                                     r'|pcs?\.?|pieces?|pounds?|size|x))?(?=,?\s|\)|$)',
                                     r'[^\s!"&\'()+,\-./:;?\[\]{}®™][^\s!"()+\-/:;?\[\]{}®™]*[^\s!"\'()+,\-./:;?\[\]{}®™]')))
                  .finditer,
                partial(map, re.Match.group))

    def __init__(self):
        LemmatizerService.__ensure_nltk_data(('corpora/omw-1.4',
                                              'corpora/wordnet',
                                              'taggers/averaged_perceptron_tagger',
                                              'tokenizers/punkt'))
        self.__lemmatizer = WordNetLemmatizer()

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
                case 'CC' | 'DT' | 'FW' | 'LS' | 'MD' | 'POS' | 'PRP' | 'PRP$' | 'SYM' | 'TO' | 'UH' | 'WDT' | 'WP' | \
                     'WP$' | 'WRB':
                    yield (word,)  # These tags have no equivalent in WordNet, but the item still needs to be a tuple.
                # case '$' | '#' | '“' | '”' | '(' | ')' | ',' | '.' | ':':
                #     continue

    @staticmethod
    def __ensure_nltk_data(names: Iterable[str]) -> None:
        for name in names:
            try:
                nltk.data.find(name)
            except LookupError:
                nltk.download(basename(name))

    def create_word_set_with_lemmas(self, text: str) -> frozenset[str]:
        return thread(text,
                      LemmatizerService.__tokenize,
                      LemmatizerService.__tag,
                      juxt(compose(self.__lemmatize,  # Generate lemmas.
                                   frozenset),
                           compose(partial(map, first),  # Get original adjectives, adverbs, nouns, and verbs.
                                   partial(filter, lambda word: len(word) > 1),  # Exclude tokens of length 1.
                                   frozenset)),
                      (reduce, frozenset.union))  # Merge original tokens, lemmas, and numeric tokens into one set.

    def __lemmatize(self, words: Iterable[tuple[str] | tuple[str, str]]) -> Collection[str]:
        return thread(words,
                      (filter, lambda word_pos_pair: len(word_pos_pair) == 2),  # Exclude miscellaneous tags.
                      (starmap, self.__lemmatizer.lemmatize),
                      (filter, lambda lemma: len(lemma) > 1),  # Exclude lemmas of length 1.
                      tuple)

    @staticmethod
    def __tag(sentences: Collection[str]) -> Collection[tuple[str] | tuple[str, str]]:
        return thread(sentences,
                      pos_tag,
                      LemmatizerService.__map_to_wordnet_pos,  # Map NLTK’s tags to WordNet’s tags.
                      tuple)

    @staticmethod
    def __tokenize(text: str) -> Collection[str]:
        return thread(text,
                      contractions.fix,  # Expand contractions.
                      str.lower,
                      LemmatizerService.__find_tokens,
                      tuple)


class ProductLookupService:
    def __init__(self, product_repository: ProductRepository, rules_repository: RulesRepository,
                 lemmatizer_service: LemmatizerService) -> None:
        create_word_set_with_lemmas = lemmatizer_service.create_word_set_with_lemmas

        # Index of product identifiers to product names
        product_names: tuple[str] = product_repository.get_all_products()

        # Association rules
        rules: tuple[Rule] = rules_repository.get_all_rules()

        # Products sorted by product identifier, where each product is found at the index equal to its identifier
        products: tuple[Optional[Product]] = \
            thread(rules,
                   (mapcat, lambda rule: ((item, rule.measure)  # Extract product identifier and all its Measures.
                                          for item in rule.consequent_items)),
                   create_sorter(lambda pair: (-pair[0], pair[1]), True),  # Sort by product identifier and Measure.
                   create_grouper(first),  # Group by product identifier.
                   (starmap, lambda item, pairs: (item, Product(item, product_names[item], tuple(map(second, pairs))))),
                   dict,
                   lambda dictionary: tuple(dictionary.get(index)  # Unused products will be represented by None
                                            for index in range(len(product_names))))  # at their respective indices.
        del product_names

        # Default product suggestions sorted in descending order of support (lift being exactly 1.0 for all Suggestions)
        default_suggestions: tuple[Suggestion] = \
            thread(products,
                   (filter, None),  # Filter out Nones.
                   (map, lambda product: (product, product.measures[-1])),  # Use the last Measure.
                   (starmap, Suggestion),  # The created Suggestions will have the maximum support for the Product.
                   sorted,
                   tuple)

        # Function to get a Product by its integer identifier
        get_product_by_identifier = products.__getitem__

        # Index of sets of suggestions by antecedent items (maps sets of Products to sorted sets of Suggestions)
        suggestions_by_antecedent_items: SetTrieMap = \
            thread(rules,
                   (filter, lambda rule: len(rule.antecedent_items) > 0),  # Ignore rules without antecedent items.
                   create_grouper(lambda rule: rule.antecedent_items),  # Group by antecedent items.
                   (map, partial(zipapply, (partial(map, get_product_by_identifier),
                                            compose(partial(mapcat, lambda rule: ((get_product_by_identifier(item),
                                                                                   rule.measure,
                                                                                   rule.antecedent_items)
                                                                                  for item in rule.consequent_items)),
                                                    partial(starmap, Suggestion),
                                                    sorted,
                                                    tuple)))),
                   SetTrieMap)
        del rules

        # Index of sets of products by words in product names (maps sets of words to sorted sets of Suggestions)
        suggestions_by_word: SetTrieMap = \
            thread(products,
                   (filter, None),  # Filter out Nones.
                   (map, lambda product: (create_word_set_with_lemmas(product.name),
                                          Suggestion(product, product.measures[-1], rank=1))),
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

        # Single empty dictionary instance to avoid allocating dictionaries for the Autocomplete initializer
        empty_dictionary = {}

        # Autocompletion engine for text queries using words from product names
        autocompleter: AutoComplete = \
            thread(suggestions_by_word.keys(),
                   chain,
                   (reduce, set.union),
                   (map, lambda word: (word, empty_dictionary)),
                   dict,
                   AutoComplete)

        self.__autocomplete = autocompleter.search
        self.__default_suggestions = default_suggestions
        self.__get_product_by_identifier = get_product_by_identifier
        self.__get_suggestions_by_antecedent_items = partial(suggestions_by_antecedent_items.itersubsets, mode='values')
        self.__get_suggestions_by_words = get_suggestions_by_words
        self.__has_suggestions_by_antecedent_items = partial(suggestions_by_antecedent_items.hassubset)
        self.__tokenize = lemmatizer_service.create_word_set_with_lemmas

    def __get_basket_suggestions(self, basket: frozenset[Product]) -> Optional[Iterable[Suggestion]]:
        if not self.__has_suggestions_by_antecedent_items(basket):
            return None
        return thread(basket,
                      self.__get_suggestions_by_antecedent_items,
                      (star, merge_sorted))

    def __get_products_from_query(self, query: str) -> Optional[Iterable[Suggestion]]:
        terms = self.__tokenize(query)
        if not terms:
            return None
        suggestion_sets = thread(terms,
                                 (map, self.__autocomplete),
                                 (map, self.__get_suggestions_by_words))
        results = first(suggestion_sets)
        for suggestions in suggestion_sets:
            results.intersection_update(suggestions)
        return sorted(results)

    def get_suggestions(self, basket: Iterable[int] = frozenset(), query: str = '') -> list[Suggestion]:
        query = query.strip()
        if query:
            query_suggestions = self.__get_products_from_query(query)
        else:
            query_suggestions = None
        if basket:
            basket_products = frozenset(map(self.__get_product_by_identifier, basket))
            basket_suggestions = self.__get_basket_suggestions(basket_products)
        else:
            basket_suggestions = basket_products = None
        match not query_suggestions, not basket_suggestions:
            case True, True:
                suggestions = self.__default_suggestions
            case True, False:
                suggestions = chain(basket_suggestions, self.__default_suggestions)
            case False, True:
                suggestions = query_suggestions
            case _:
                suggestions = chain(query_suggestions, basket_suggestions)
        pipeline = [partial(unique, key=lambda suggestion: suggestion.product)]
        if basket_products:
            pipeline.append(partial(filter, lambda suggestion: suggestion.product not in basket_products))
        pipeline.append(partial(take, 10))
        pipeline.append(list)
        return compose(*pipeline)(suggestions)


__all__ = ('LemmatizerService', 'ProductLookupService')
