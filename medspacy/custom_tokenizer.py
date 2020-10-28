from spacy.symbols import IS_PUNCT

import re
import string

from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex


def create_medspacy_tokenizer(nlp):
    """Generates a custom tokenizer to augment the default spacy tokenizer 
        for situations commonly seen in clinical text.
        This includes:
            * Punctuation infixes.  
                For example, this allows the following examples to be more aggresively tokenized as :
                    "Patient complains of c/o" -> [..., 'c', '/', 'o']
                    "chf+cp" -> ['chf', '+', 'cp']
       @param nlp: Spacy language model
    """

    # augment the defaults
    # this is not quite correct.  We do not want to break on uppercase and we do not
    # want to break on all punctuation (periods)
    # infixes = nlp.Defaults.infixes + (r'''[^a-z0-9]''',)
    # escape all the punctuation we want to allow to allow to break up tokens

    # get all python punctuation
    punctuation_chars = string.punctuation
    # remove periods so that we do not break up '1.5 mg' into '1 . 5 mg'
    punctuation_chars = punctuation_chars.replace('.', '')

    infixes = nlp.Defaults.infixes + (r'''[{}]'''.format(re.escape(punctuation_chars)),)
    prefixes = nlp.Defaults.prefixes
    suffixes = nlp.Defaults.suffixes

    # compile
    infix_re = compile_infix_regex(infixes)
    prefix_re = compile_prefix_regex(prefixes)
    suffix_re = compile_suffix_regex(suffixes)

    # Default exceptions could be extended later
    tokenizer_exceptions = nlp.Defaults.tokenizer_exceptions.copy()

    # now create this
    tokenizer = Tokenizer(
        nlp.vocab,
        tokenizer_exceptions,
        prefix_search=prefix_re.search,
        suffix_search=suffix_re.search,
        infix_finditer=infix_re.finditer,
        token_match=nlp.tokenizer.token_match,
    )

    return tokenizer