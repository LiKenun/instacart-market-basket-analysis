from ast import literal_eval
from dataclasses import dataclass
from functools import cache
import lzma
import numpy as np
from typing import Optional
from helpers import read_csv
from models import Suggestion


@dataclass(eq=False, frozen=True, slots=True)
class ProductRepository:
    products_data_file: str

    @cache
    def get_all_products(self) -> tuple[tuple[str], tuple[tuple[tuple[str, Optional[str]]]]]:
        with lzma.open(self.products_data_file, 'rt', format=lzma.FORMAT_XZ, encoding='utf-8') as stream:
            return tuple(zip(*((product_name, tuple(literal_eval(word_lemma_pairs)))
                               for product_name, word_lemma_pairs
                               in read_csv(stream))))


@dataclass(eq=False, frozen=True, slots=True)
class SuggestionRepository:
    suggestions_data_file: str

    # See https://tonysyu.github.io/ragged-arrays.html for the method to save/load ragged arrays with NumPy.
    def get_all_suggestions(self) -> tuple:
        with lzma.open(self.suggestions_data_file) as file:
            data = np.load(file, allow_pickle=False)
            return tuple(map(Suggestion, np.split(data['array'], data['indices'])))


__all__ = ('ProductRepository', 'SuggestionRepository')
