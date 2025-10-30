from lxml import etree
import re # Not strictly used yet, but good for cleaning names if needed
"""
    1-safe Petri Net.
"""
class PetriNet:
    def __init__(self):
        self.places = {} # dict of {id: place_obj}
        self.transitions = {} # dict of {id: transition_obj}
        self.initial_marking = set() # Set of place IDs with a token

    def add_place(self, p_id, initial=False):
        self.places[p_id] = {'id': p_id, 'pre': set(), 'post': set()}
        if initial:
            self.initial_marking.add(p_id)

    def add_transition(self, t_id):
        self.transitions[t_id] = {'id': t_id, 'pre': set(), 'post': set()}

    def add_arc(self, source_id, target_id):
        if source_id in self.places and target_id in self.transitions:
            # P -> T arc
            self.transitions[target_id]['pre'].add(source_id)
            self.places[source_id]['post'].add(target_id)
        elif source_id in self.transitions and target_id in self.places:
            # T -> P arc
            self.transitions[source_id]['post'].add(target_id)
            self.places[target_id]['pre'].add(source_id)
        else:
            print(f"Warning: Arc between {source_id} and {target_id} not created. One or both not found.")


    @property
    def place_ids(self):
        """
        Returns a sorted, consistent list of place IDs.
        Crucial for mapping to BDD and ILP variables.
        """
        return sorted(list(self.places.keys()))

def parse_pnml(file_path: str) -> PetriNet:
    """
    Parses a standard PNML file and returns a PetriNet object.
    Assumes 1-safe net (initial marking is 0 or 1).
    """
    print(f"Parsing {file_path}...")
    net = PetriNet()
    try:
        tree = etree.parse(file_path)
    except etree.XMLSyntaxError as e:
        print(f"Error: Could not parse XML. {e}")
        return None
    except IOError:
        print(f"Error: File not found at {file_path}")
        return None

    # PNML namespace
    ns = {'pnml': 'http://www.pnml.org/version-2009/grammar/pnml'}

    # Get places and initial marking
    for place in tree.xpath('//pnml:place', namespaces=ns):
        p_id = place.get('id')
        if not p_id: continue
        
        initial = place.find('.//pnml:initialMarking', namespaces=ns)
        has_token = False
        if initial is not None:
            text_node = initial.find('.//pnml:text', namespaces=ns)
            if text_node is not None and text_node.text == '1':
                has_token = True
        
        net.add_place(p_id, initial=has_token)

    # Get transitions
    for trans in tree.xpath('//pnml:transition', namespaces=ns):
        t_id = trans.get('id')
        if t_id:
            net.add_transition(t_id)

    # Get arcs
    for arc in tree.xpath('//pnml:arc', namespaces=ns):
        source = arc.get('source')
        target = arc.get('target')
        if source and target:
            net.add_arc(source, target)
    
    print(f"Parsing complete. Found {len(net.places)} places and {len(net.transitions)} transitions.")
    print(f"Initial marking: {net.initial_marking}")
    return net