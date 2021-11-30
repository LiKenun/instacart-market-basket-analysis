from collections import defaultdict
from fast_autocomplete import AutoComplete
from functools import reduce
from itertools import chain
import re
from sortedcontainers import SortedSet
from toolz import peek, take, thread_last, unique
from typing import Any, Callable, Iterable
from models import Product, Rule, Suggestion
from repositories import ProductRepository, RulesRepository


class ProductLookupService:
    __tokenize = re.compile(r'[\w\d]+').findall

    @staticmethod
    def __create_autocompleter(index: Iterable[str]) -> AutoComplete:
        return AutoComplete({word: {} for word in index})

    @staticmethod
    def __create_word_index(products: set[Product]) -> dict[str, set[Product]]:
        name_index = defaultdict(set)
        for product in products:
            for word in ProductLookupService.__tokenize(product.name.casefold()):
                name_index[word].add(product)
        return name_index

    def __get_basket_suggestions(self, basket: set[Product]) -> SortedSet[Suggestion]:
        return thread_last(self.__suggestions_by_base_items.keys(),
                           (filter, basket.issuperset),  # Match association rules.
                           (map, self.__suggestions_by_base_items.get),  # Get suggested products.
                           chain.from_iterable,  # Combine all of the sets of suggestions.
                           self.__default_suggestions.union,  # Merge with default suggestions.
                           (filter, lambda suggestion: suggestion.product not in basket),
                           SortedSet)

    def __get_products_from_query(self, basket: set[Product], query: str) -> set[Product]:
        matching_term_sets = (set(chain.from_iterable(self.__autocompleter.search(term)))
                              for term in ProductLookupService.__tokenize(query.casefold()))
        products = set(self.__all_products)
        for matching_term_set in matching_term_sets:
            products &= reduce(set.union, map(self.__suggestions_by_word.get, matching_term_set))
        return products - basket  # Make sure to remove items that are already in the basket!

    @staticmethod
    def __intersect_query_and_suggestions(products: set[Product], suggestions: SortedSet[Suggestion]) -> Iterable[Suggestion]:
        for suggestion in suggestions:
            if suggestion.product in products:
                yield suggestion

    @staticmethod
    def __split_rule_set(rules: SortedSet[Rule], key: Callable[[Rule], Any] = None) -> tuple[SortedSet[Rule], SortedSet[Rule]]:
        threshold = Rule((Product(0, ''),), (), 0, 0, 0, 0)  # Divides the rules based on whether they have any base products
        null_base_rules = SortedSet(rules.irange(maximum=threshold, inclusive=(True, False)), key=key)
        nonnull_base_rules = SortedSet(rules.irange(minimum=threshold, inclusive=(False, True)), key=key)
        return null_base_rules, nonnull_base_rules

    def __init__(self, product_repository: ProductRepository, rules_repository: RulesRepository):
        # Get and split rules into two sets.
        rules = rules_repository.get_all_rules()
        null_base_rules, nonnull_base_rules = ProductLookupService.__split_rule_set(rules)

        # Initialize a default set of suggestions—for when the basket is empty.
        default_suggestions = SortedSet(map(lambda rule: Suggestion(rule.additional[0], rule.base, rule.confidence, rule.lift),
                                            null_base_rules))

        # Create an index of sets of suggestions by base items.
        suggestions_by_base_items: dict[tuple[Product, ...], set[Suggestion]] = {}
        for rule in nonnull_base_rules:
            for product in rule.additional:
                suggestions_by_base_items.setdefault(rule.base, set()) \
                                         .add(Suggestion(product, rule.base, rule.confidence, rule.lift))

        # Create a index of sets of suggestions by word from the product names.
        products = product_repository.get_all_products()
        suggestions_by_word = ProductLookupService.__create_word_index(products)

        # Initialize the autocompleter with the set of products.
        autocompleter = ProductLookupService.__create_autocompleter(suggestions_by_word.keys())

        # Initialize private instance variables.
        self.__all_products = products
        self.__products_by_id = {product.id: product for product in products}
        self.__autocompleter = autocompleter
        self.__default_suggestions = default_suggestions
        self.__suggestions_by_base_items = suggestions_by_base_items
        self.__suggestions_by_word = suggestions_by_word

    def get_suggestions(self, basket: Iterable[int], query: str) -> list[dict]:
        # Compile a set of products already in the basket.
        products_in_basket = set(map(self.__products_by_id.get, basket))

        # Compile a set of potential suggestions sorted by confidence.
        basket_suggestions = self.__get_basket_suggestions(products_in_basket)

        # Compile a set of products from the supplied text query. There may be no results.
        queried_products = self.__get_products_from_query(products_in_basket, query)

        if not basket_suggestions:  # There are no matching products from basket analysis.
            results = queried_products  # Use the text query results instead.
        else:
            first_result, results = peek(ProductLookupService.__intersect_query_and_suggestions(queried_products, basket_suggestions))
            if not first_result:  # Matching products from basket analysis and text query results are disjoint.
                results = queried_products  # Use the text query results instead.
        return thread_last(unique(results, lambda suggestion: suggestion.product),
                           (take, 10),  # Take the top 10 only.
                           list)
