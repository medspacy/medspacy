from typing import Dict

from spacy import displacy
from spacy.tokens import Doc, Span


def visualize_ent(
    doc: Doc,
    context: bool = True,
    sections: bool = True,
    jupyter: bool = True,
    colors: Dict[str, str] = None,
) -> str:
    """
    Creates a NER-style visualization for targets and modifiers in Doc.

    Args:
        doc: A spacy doc to visualize.
        context: Whether to display the modifiers generated by medSpaCy's cycontext. If the doc has not been processed
            by context, this will be automatically changed to False. Default True.
        sections: Whether to display the section titles generated by medSpaCy's sectionizer (still in development). If
            the doc has not been processed by sectionizer , this will be automatically changed to False. This may also
            have some overlap with cycontext, in which case duplicate spans will be displayed. Default True.
        jupyter: If True, will render directly in a Jupyter notebook. If False, will return the HTML. Default True.
        colors: An optional dictionary which maps labels of targets and modifiers to color strings to be rendered. If
            None, will create a generator which cycles through the default matplotlib colors for ent and modifier labels
            and uses a light gray for section headers. Default None.

    Returns:
        The visualization.
    """
    # Make sure that doc has the custom medSpaCy attributes registered
    if not hasattr(doc._, "context_graph"):
        context = False
    if not hasattr(doc._, "sections"):
        sections = False

    ents_data = []

    for target in doc.ents:
        ent_data = {
            "start": target.start_char,
            "end": target.end_char,
            "label": target.label_.upper(),
        }
        ents_data.append((ent_data, "ent"))

    if context:
        visualized_modifiers = set()
        for target in doc.ents:
            for modifier in target._.modifiers:
                if modifier in visualized_modifiers:
                    continue
                span = doc[modifier.modifier_span[0]: modifier.modifier_span[1]]
                ent_data = {
                    "start": span.start_char,
                    "end": span.end_char,
                    "label": modifier.category,
                }
                ents_data.append((ent_data, "modifier"))
                visualized_modifiers.add(modifier)
    if sections:
        for section in doc._.sections:
            category = section.category
            if category is None:
                continue
            span = doc[section.title_span[0]: section.title_span[1]]
            ent_data = {
                "start": span.start_char,
                "end": span.end_char,
                "label": f"<< {category.upper()} >>",
            }
            ents_data.append((ent_data, "section"))
    if len(ents_data) == 0:  # No data to display
        viz_data = [{"text": doc.text, "ents": []}]
        options = dict()
    else:
        ents_data = sorted(ents_data, key=lambda x: x[0]["start"])

        # If colors aren't defined, generate color mappings for each entity
        # and modifier label and set all section titles to a light gray
        if colors is None:
            labels = set()
            section_titles = set()
            for (ent_data, ent_type) in ents_data:
                if ent_type in ("ent", "modifier"):
                    labels.add(ent_data["label"])
                elif ent_type == "section":
                    section_titles.add(ent_data["label"])
            colors = _create_color_mapping(labels)
            for title in section_titles:
                colors[title] = "#dee0e3"
        ents_display_data, _ = zip(*ents_data)
        viz_data = [
            {
                "text": doc.text,
                "ents": ents_display_data,
            }
        ]

        options = {
            "colors": colors,
        }
    return displacy.render(
        viz_data, style="ent", manual=True, options=options, jupyter=jupyter
    )


def _create_color_mapping(labels):
    mapping = {}
    color_cycle = _create_color_generator()
    for label in labels:
        if label not in mapping:
            mapping[label] = next(color_cycle)
    return mapping


def _create_color_generator():
    """Create a generator which will cycle through a list of
    default matplotlib colors"""
    from itertools import cycle

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    return cycle(colors)


def visualize_dep(doc: Doc, jupyter: bool = True) -> str:
    """
    Create a dependency-style visualization for ConText targets and modifiers in doc. This will show the relationships
    between entities in doc and contextual modifiers.

    Args:
        doc: The spacy Doc to visualize.
        jupyter: Whether it is being rendered in a jupyter notebook.

    Returns:
        The visualization.
    """
    token_data = []
    token_data_mapping = {}
    for token in doc:
        data = {"text": token.text, "tag": "", "index": token.i}
        token_data.append(data)
        token_data_mapping[token] = data

    # Merge phrases
    targets_and_modifiers = [*doc._.context_graph.targets]
    targets_and_modifiers += [*doc._.context_graph.modifiers]

    for obj in targets_and_modifiers:
        if isinstance(obj, Span):
            first_token = obj[0]
            data = token_data_mapping[first_token]
            data["tag"] = obj.label_
            if len(obj) > 1:
                idx = data["index"]
                for other_token in obj[1:]:
                    # Add the text to the display data for the first word
                    # and remove the subsequent token
                    data["text"] += " " + other_token.text
                    # Remove this token from the list of display data
                    token_data.pop(idx + 1)
                for other_data in token_data[idx + 1:]:
                    other_data["index"] -= len(obj) - 1
        else:
            span_tup = obj.modifier_span
            first_token = doc[span_tup[0]]
            data = token_data_mapping[first_token]
            data["tag"] = obj.category
            if span_tup[1] - span_tup[0] > 1:
                span = doc[span_tup[0]: span_tup[1]]
                idx = data["index"]
                for other_token in span[1:]:
                    # Add the text to the display data for the first word
                    # and remove the subsequent token
                    data["text"] += " " + other_token.text
                    # Remove this token from the list of display data
                    token_data.pop(idx + 1)
                for other_data in token_data[idx + 1:]:
                    other_data["index"] -= len(span) - 1

        # if len(span) == 1:
        #     continue
        #
        # idx = data["index"]
        # for other_token in span[1:]:
        #     # Add the text to the display data for the first word
        #     # and remove the subsequent token
        #     data["text"] += " " + other_token.text
        #     # Remove this token from the list of display data
        #     token_data.pop(idx + 1)
        #
        # # Lower the index of the following tokens
        # for other_data in token_data[idx + 1 :]:
        #     other_data["index"] -= len(span) - 1

    dep_data = {"words": token_data, "arcs": []}
    # Gather the edges between targets and modifiers
    for target, modifier in doc._.context_graph.edges:
        target_data = token_data_mapping[target[0]]
        modifier_data = token_data_mapping[doc[modifier.modifier_span[0]]]
        dep_data["arcs"].append(
            {
                "start": min(target_data["index"], modifier_data["index"]),
                "end": max(target_data["index"], modifier_data["index"]),
                "label": modifier.category,
                "dir": "right"
                if target > doc[modifier.modifier_span[0] : modifier.modifier_span[1]]
                else "left",
            }
        )
    return displacy.render(dep_data, manual=True, jupyter=jupyter)


class MedspaCyVisualizerWidget:
    def __init__(self, docs):

        """Create an IPython Widget Box displaying medspaCy's visualizers.
        The widget allows selecting visualization style ("Ent", "Dep", or "Both")
        and a slider for selecting the index of docs.

        For more information on IPython widgets, see:
            https://ipywidgets.readthedocs.io/en/latest/index.html

        Parameters:
            docs: A list of docs processed by a medspaCy pipeline

        """

        import ipywidgets as widgets

        self.docs = docs
        self.slider = widgets.IntSlider(
            value=0,
            min=0,
            max=len(docs) - 1,
            step=1,
            description="Doc:",
            disabled=False,
            continuous_update=False,
            orientation="horizontal",
            readout=True,
            readout_format="d",
        )
        self.radio = widgets.RadioButtons(options=["Ent", "Dep", "Both"])
        self.layout = widgets.Layout(
            display="flex", flex_flow="column", align_items="stretch", width="100%"
        )
        self.radio.observe(self._change_handler)
        self.slider.observe(self._change_handler)
        self.next_button = widgets.Button(description="Next")
        self.next_button.on_click(self._on_click_next)
        self.previous_button = widgets.Button(description="Previous")
        self.previous_button.on_click(self._on_click_prev)
        self.output = widgets.Output()
        self.box = widgets.Box(
            [
                widgets.HBox([self.radio, self.previous_button, self.next_button]),
                self.slider,
                self.output,
            ],
            layout=self.layout,
        )

        self.display()
        with self.output:
            self._visualize_doc()

    def display(self):
        """Display the Box widget in the current IPython cell."""
        from IPython.display import display as ipydisplay

        ipydisplay(self.box)

    def _change_handler(self, change):

        with self.output:
            self._visualize_doc()

    def _visualize_doc(self):
        self.output.clear_output()
        doc = self.docs[self.slider.value]
        if self.radio.value.lower() in ("dep", "both"):
            visualize_dep(doc)
        if self.radio.value.lower() in ("ent", "both"):
            visualize_ent(doc)

    def _on_click_next(self, b):
        if self.slider.value < len(self.docs) - 1:
            self.slider.value += 1

    def _on_click_prev(self, b):
        if self.slider.value > 0:
            self.slider.value -= 1

    def set_docs(self, docs):
        "Replace the list of docs to be visualized."
        self.docs = docs
        self._visualize_doc(self.docs[0])
