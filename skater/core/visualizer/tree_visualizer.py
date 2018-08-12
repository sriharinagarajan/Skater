from sklearn.externals.six import StringIO
from sklearn.tree import export_graphviz
import pydotplus
import numpy as np

from skater.util import exceptions
try:
    from matplotlib.colors import rgb2hex
    import matplotlib.pyplot as plt
except ImportError:
    raise (exceptions.MatplotlibUnavailableError("matplotlib is required but unavailable on the system."))


# reference: http://wingraphviz.sourceforge.net/wingraphviz/language/colorname.htm
# TODO: Make the color scheme for regression and classification homogeneous
color_schemes = ['aliceblue', 'antiquewhite', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue',
                 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue',
                 'cornsilk', 'crimson', 'cyan', 'darkgoldenrod', 'darkgreen', 'darkkhaki', 'darkolivegreen', 'darkorange',
                 'darkorchid', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey',
                 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue', 'firebrick',
                 'floralwhite', 'forestgreen', 'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green',
                 'greenyellow', 'grey', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory', 'khaki', 'lavender',
                 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrod',
                 'lightgoldenrodyellow', 'lightgray', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen',
                 'lightskyblue', 'lightslateblue', 'lightslategray', 'lightslategrey', 'lightsteelblue', 'lightyellow',
                 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid',
                 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise',
                 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy',
                 'navyblue', 'oldlace', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise',
                 'palevioletred', 'papayawhip', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown',
                 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'skyblue',
                 'slateblue', 'slategray', 'slategrey', 'snow', 'springgreen', 'steelblue', 'tan', 'thistle', 'tomato',
                 'turquoise', 'violet', 'violetred', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']


def _get_colors(num_classes, random_state=1):
    np.random.seed(random_state)
    color_index = np.random.randint(0, len(color_schemes), num_classes)
    colors = np.array(color_schemes)[color_index]
    return colors


def _generate_graph(est, est_type='classifier', classes=None, features=None,
                    enable_node_id=True, coverage=True):
    dot_data = StringIO()
    # class names are needed only for "Classification" for "Regression" it is set to None
    c_n = classes if est_type == 'classifier' else None
    export_graphviz(est, out_file=dot_data, filled=True, rounded=True,
                    special_characters=True, feature_names=features,
                    class_names=c_n, node_ids=enable_node_id, proportion=coverage)
    graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
    return graph


def _set_node_properites(estimator, estimator_type, graph_instance, color_names, default_color):
    # Query and assign properties to each node
    nodes = graph_instance.get_node_list()
    for node in nodes:
        if node.get_name() not in ('node', 'edge'):
            if estimator_type == 'classifier':
                values = estimator.tree_.value[int(node.get_name())][0]
                # 1. Color only the leaf nodes, One way to identify leaf nodes is to check on the values which
                #    should represent a distribution only for one class
                # 2. mixed nodes get the default color
                node.set_fillcolor(color_names[np.argmax(values)]) if max(values) == sum(values) \
                    else node.set_fillcolor(default_color)
            else:
                # if the estimator type is a "regressor", then the intensity of the color is defined by the
                # population coverage for a particular value
                percent = estimator.tree_.n_node_samples[int(node.get_name())] / float(estimator.tree_.n_node_samples[0])
                rgba = plt.cm.get_cmap(color_names)(percent)
                hex_code = rgb2hex(rgba)
                node.set_fillcolor(hex_code)
                graph_instance.set_colorscheme(color_names)
    return graph_instance


# https://stackoverflow.com/questions/48085315/interpreting-graphviz-output-for-decision-tree-regression
# https://stackoverflow.com/questions/42891148/changing-colors-for-decision-tree-plot-created-using-export-graphviz
# Color scheme info: http://wingraphviz.sourceforge.net/wingraphviz/language/colorname.htm
# Currently, supported only for sklearn models
def plot_tree(estimator, estimator_type='classifier', feature_names=None, class_names=None, color_list=None,
              colormap_reg='PuBuGn', enable_node_id=True, coverage=True, seed=2):

    graph = _generate_graph(estimator, estimator_type, class_names, feature_names, enable_node_id, coverage)

    if estimator_type == 'classifier':
        # if color is not assigned, pick color uniformly random from the color list defined above if the estimator
        # type is "classification"
        colors = color_list if color_list is not None else _get_colors(len(class_names), seed)
        default_color = 'cornsilk'
    else:
        colors = colormap_reg
        default_color = None

    graph = _set_node_properites(estimator, estimator_type, graph, color_names=colors, default_color=default_color)

    # Set the color scheme for the edges
    edges = graph.get_edge_list()
    for ed in edges:
        ed.set_color('steelblue')
    return graph


_return_value = lambda estimator_type, v: 'Predicted Label: {}'.format(str(np.argmax(v))) \
    if estimator_type == 'classifier' else 'Value: {}'.format(str(v))


def _global_decisions_as_txt(est_type, label_color, criteria_color, if_else_color, values,
                             features, thresholds, l_nodes, r_nodes):
    # Reference: https://github.com/scikit-learn/scikit-learn/blob/a24c8b464d094d2c468a16ea9f8bf8d42d949f84/sklearn/tree/_tree.pyx
    TREE_LEAF = -1
    TREE_UNDEFINED = -2

    # define "if and else" string patterns for extracting the decision rules
    if_str_pattern = lambda offset, node: offset + "if {}{}".format(criteria_color, features[node]) \
        + " <= {}".format(str(thresholds[node])) + if_else_color + " {"

    other_str_pattern = lambda offset, str_type: offset + if_else_color + str_type

    def _recurse_tree(left_node, right_node, threshold, node, depth=0):
        offset = "  " * depth
        if threshold[node] != TREE_UNDEFINED:
            print(if_str_pattern(offset, node))
            if left_node[node] != TREE_LEAF:
                _recurse_tree(left_node, right_node, threshold, left_node[node], depth + 1)
                print(other_str_pattern(offset, "} else {"))
                if right_node[node] != TREE_LEAF:
                    _recurse_tree(left_node, right_node, threshold, right_node[node], depth + 1)
                print(other_str_pattern(offset, "}"))
        else:
            print(offset, label_color, _return_value(est_type, values[node]))

    _recurse_tree(l_nodes, r_nodes, thresholds, 0)


def _local_decisions_as_txt(est, est_type, label_color, criteria_color, if_else_color,
                            values, features, thresholds, input_X):
    as_str_pattern = lambda offset, node_id, \
        feature_value: offset + \
        "As {}{}{}".format(criteria_color, features[node_id], "[" + str(feature_value) + "]") + \
        " <= {}".format(str(thresholds[node_id])) + if_else_color + " then,"

    path = est.decision_path(input_X)
    node_indexes = path.indices
    leaf_id = est.apply(input_X)
    depth = 0
    for node_index in node_indexes:
        offset = "  " * depth
    if leaf_id != node_index:
        print(as_str_pattern(offset, node_index, input_X[features[node_index]]))
        depth += 1
    else:
        print(offset, label_color, _return_value(est_type, values[node_index]))


# Current implementation is specific to sklearn models.
# Reference: https://stackoverflow.com/questions/20224526/how-to-extract-the-decision-rules-from-scikit-learn-decision-tree
# TODO: Figure out ways to make it generic for other frameworks
def tree_to_text(tree, feature_names, estimator_type='classifier', scope='global', X=None):
    # defining colors
    label_value_color = "\033[1;34;49m"  # blue
    split_criteria_color = "\033[0;32;49m"  # green
    if_else_quotes_color = "\033[0;30;49m"  # if and else quotes

    left_nodes = tree.tree_.children_left
    right_nodes = tree.tree_.children_right
    criterias = tree.tree_.threshold
    feature_names = [feature_names[i] for i in tree.tree_.feature]
    values = tree.tree_.value

    if scope == "global":
        _global_decisions_as_txt(estimator_type, label_value_color, split_criteria_color,
                                 if_else_quotes_color, values, feature_names, criterias, left_nodes, right_nodes)
    else:
        _local_decisions_as_txt(tree, estimator_type, label_value_color, split_criteria_color,
                                if_else_quotes_color, values, feature_names, criterias, X)