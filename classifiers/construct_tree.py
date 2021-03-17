from classifiers.pair_classifier.pair_classifier import PairClassifier
from classifiers.tz_classifier.tz_classifier import TzLineTypeClassifier
from docx_parser.document_parser import DOCXParser
from tree_constructor import DocumentTreeConstructor


pair_classifier = PairClassifier.load_pickled(config={})
tz_classifier = TzLineTypeClassifier.load_pickled(config={})

docx_parser = DOCXParser()
docx_parser.parse("../data/1611572467_467.docx")
lines = docx_parser.get_lines_with_meta()

tree_constructor = DocumentTreeConstructor(comparator=pair_classifier, line_type_classifier=tz_classifier)
tree = tree_constructor.construct_tree(lines, with_type=True)

print(tree)
