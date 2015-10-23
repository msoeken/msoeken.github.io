#!/usr/bin/env python
import os
import sys

from jinja2 import Environment

def dict_from_tuple( keys, data ):
    return dict( zip( keys, data ) )

def make_dict( key, data, f ):
    return dict( ( d[key], d ) for d in map( f, data ) )

def make_venue( data ):
    return dict_from_tuple( ['year', 'month', 'city', 'country'], data )

def make_conference( data ):
    d = dict_from_tuple( ['key', 'shortname', 'name', 'publisher', 'venues', 'type'], data + ('conf',) )
    d['venues'] = make_dict( 'year', d['venues'], make_venue )
    return d

def make_journal( data ):
    return dict_from_tuple( ['key', 'name', 'publisher'], data )

def make_author( data ):
    return dict_from_tuple( ['key', 'firstname', 'lastname'], data )

def make_conference_paper( data ):
    global conferences
    global authors

    d = dict_from_tuple( ['authors', 'conf', 'year', 'title', 'pages', 'doi'], data )
    d['authors'] = [authors[k] for k in d['authors']]
    d['conf'] = conferences[d['conf']]
    return d

def make_article( data ):
    global journals
    global authors

    d = dict_from_tuple( ['authors', 'journal', 'volume', 'number', 'year', 'title', 'pages', 'doi'], data )
    d['authors'] = [authors[k] for k in d['authors']]
    d['journal'] = journals[d['journal']]
    return d

def make_filename( c ):
    conf = c['conf']['key']
    year = c['year']

    same_venue = [c2 for c2 in confpapers if c2['conf']['key'] == conf and c2['year'] == year]

    if len( same_venue ) == 1:
        return "%s_%s" % ( year, conf )
    else:
        return "%s_%s_%d" % ( year, conf, same_venue.index( c ) + 1 )


def format_bibtex_incollection( paper ):
    global capitalize

    conf  = paper['conf']
    venue = conf['venues'][paper['year']]

    title = paper['title']
    for c in capitalize:
        title = title.replace( c, "{%s}" % c )

    print( "@inproceedings{%s%d," % ( conf['key'], paper['year'] ) )
    print( "  author    = {%s},"     % " and ".join( "%s, %s" % ( a['lastname'], a['firstname'] ) for a in paper['authors'] ) )
    print( "  title     = {%s},"     % title )
    print( "  booktitle = {%s},"     % conf['name'] )
    print( "  year      = %d,"       % paper['year'] )
    print( "  month     = %s,"       % venue['month'] )
    print( "  address   = {%s, %s}," % ( venue['city'], venue['country'] ) )
    print( "  publisher = {%s},"     % conf['publisher'] )
    print( "  pages     = {%s}"      % paper['pages'] )
    print( "}" )

def format_haml_incollection( paper ):
    conf  = paper['conf']
    venue = conf['venues'][paper['year']]

    env = Environment()
    template = env.from_string('''
            .item
              .pubmain
                .pubassets
                  %a(href="#")
                    %span.glyphicon.glyphicon-new-window
                  %a(href="#")
                    %span.glyphicon.glyphicon-cloud-download
                %img.pubthumb(src="images/thumbs/{{filename}}.png")
                %h4.pubtitle
                  {{title}}
                .pubauthor
                  {{authors}}
                .pubcite
                  %span.label.label-warning Conference Paper
                  In {{conf}} ({{shortname}}) | {{city}}, {{country}}, {{month}} {{year}} | Pages {{pages}} | Publisher: {{publisher}}''')

    authors = ",\n                  ".join( "%s %s" % ( a['firstname'], a['lastname'] ) for a in paper['authors'] )
    authors.replace( "Mathias Soeken", "%strong Mathias Soeken" )

    print( template.render( {'title': paper['title'],
                             'filename': make_filename( paper ),
                             'authors': authors,
                             'conf': conf['name'],
                             'shortname': conf['shortname'],
                             'city': venue['city'],
                             'country': venue['country'],
                             'month': monthnames[venue['month']],
                             'year': venue['year'],
                             'pages': paper['pages'],
                             'publisher': conf['publisher']} )[1:] )

monthnames = {'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April', 'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August', 'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December'}
capitalize = ["BDD", "Boolean", "Completeness-Driven Development", "CPU", "Formal Specification Level", "Fredkin", "Hadamard", "Industrie", "metaSMT", "NCV", "OCL", "RevKit", "RISC", "SAT", "SMT-LIB2", "SyReC", "Toffoli", "UML"]

conferences_data = [
    ( 'apms', 'APMS', 'Advances in Production Management Systems', 'IFIP', [
        ( 2014, 'sep', 'Ajaccio', 'France' )
    ] ),
    ( 'aspdac', 'ASP-DAC', 'Asia and South Pacific Design Automation Conference', 'IEEE', [
        ( 2012, 'jan', 'Sydney', 'Australia' ),
        ( 2013, 'jan', 'Yokohama', 'Japan' ),
        ( 2016, 'jan', 'Macau', 'China' )
    ] ),
    ( 'ast', 'AST', 'International Workshop on Automation of Software Test', 'ACM', [
        ( 2013, 'may', 'San Francisco, CA', 'USA' )
    ] ),
    ( 'dac', 'DAC', 'Design Automation Conference', 'ACM/IEEE', [
        ( 2010, 'jun', 'Anaheim, CA', 'USA' )
    ] ),
    ( 'date', 'DATE', 'Design, Automation and Test in Europe', 'IEEE', [
        ( 2010, 'mar', 'Dresden', 'Germany' ),
        ( 2011, 'mar', 'Grenoble', 'France' ),
        ( 2012, 'mar', 'Dresden', 'Germany' ),
        ( 2013, 'mar', 'Grenoble', 'France' ),
        ( 2014, 'mar', 'Dresden', 'Germany' ),
        ( 2015, 'mar', 'Grenoble', 'Germany' ),
        ( 2016, 'mar', 'Dresden', 'Germany' )
    ] ),
    ( 'ddecs', 'DDECS', 'IEEE International Symposium on Design and Diagnostics of Electronic Circuits and Systems', 'IEEE', [
        ( 2010, 'apr', 'Vienna', 'Austria' ),
        ( 2011, 'apr', 'Cottbus', 'Germany' ),
        ( 2013, 'apr', 'Karlovy Vary', 'Czech Republic' ),
        ( 2015, 'apr', 'Belgrad', 'Serbia' )
    ] ),
    ( 'dgk', 'DGK', 'Annual Conference of the German Crystallographic Society', '', [
        ( 2013, 'mar', 'Freiberg', 'Germany' )
    ] ),
    ( 'fdl', 'FDL', 'Forum on Specification & Design Languages', 'IEEE', [
        ( 2012, 'sep', 'Vienna', 'Austria' ),
        ( 2014, 'oct', 'Munich', 'Germany' )
    ] ),
    ( 'fmcad', 'FMCAD', 'Formal Methods in Computer-Aided Design', 'IEEE', [
        ( 2015, 'sep', 'Austin, TX', 'USA' )
    ] ),
    ( 'gecco', 'GECCO', 'Genetic and Evolutionary Computation Conference', 'ACM', [
        ( 2015, 'jul', 'Madrid', 'Spain' )
    ] ),
    ( 'gi', 'GI', 'Jahrestagung der Gesellschaft für Informatik', 'GI', [
        ( 2013, 'sep', 'Koblenz', 'Germany' )
    ] ),
    ( 'hldvt', 'HLDVT', 'International Workshop on High-Level Design Validation and Test', 'IEEE', [
        ( 2012, 'nov', 'Huntington Beach, CA', 'USA' )
    ] ),
    ( 'iccad', 'ICCAD', 'International Conference on Computer-Aided Design', 'IEEE', [
        ( 2014, 'nov', 'San Jose, CA', 'USA' )
    ] ),
    ( 'icgt', 'ICGT', 'International Conference on Graph Transformation', 'Springer', [
        ( 2012, 'sep', 'Bremen', 'Germany' )
    ] ),
    ( 'idt', 'IDT', 'International Test & Design Symposium', 'IEEE', [
        ( 2010, 'dec', 'Abu Dhabi', 'United Arab Emirates' ),
        ( 2013, 'dec', 'Marrakesh', 'Marocco' )
    ] ),
    ( 'ismvl', 'ISMVL', 'International Symposium on Multiple-Valued Logic', 'IEEE', [
        ( 2011, 'may', 'Tuusula', 'Finland' ),
        ( 2012, 'may', 'Victoria, BC', 'Canada' ),
        ( 2013, 'may', 'Toyama', 'Japan' ),
        ( 2015, 'may', 'Waterloo, ON', 'Canada' )
    ] ),
    ( 'isvlsi', 'ISVLSI', 'IEEE Computer Society Annual Symposium on VLSI', 'IEEE', [
        ( 2008, 'apr', 'Montpellier', 'France' ),
        ( 2012, 'aug', 'Armherst, CA', 'USA' )
    ] ),
    ( 'modevva', 'MoDeVVa', 'Model-Driven Engineering, Verification, And Validation', 'ACM', [
        ( 2011, 'oct', 'Wellington', 'New Zealand' ),
        ( 2015, 'oct', 'Ottawa, ON', 'Canada' )
    ] ),
    ( 'rc', 'RC', 'Conference on Reversible Computation', 'Springer', [
        ( 2011, 'jul', 'Ghent', 'Belgium' ),
        ( 2012, 'jul', 'Copenhagen', 'Denmark' ),
        ( 2013, 'jul', 'Victoria, BC', 'Canada' ),
        ( 2014, 'jul', 'Kyoto', 'Japan' ),
        ( 2015, 'jul', 'Grenoble', 'France' )
    ] ),
    ( 'sbcci', 'SBCCI', 'Symposium on Integrated Circuits and Systems Design', 'ACM', [
        ( 2014, 'sep', 'Aracaju', 'Brazil' )
    ] ),
    ( 'tap', 'TAP', 'International Conference on Tests and Proofs', 'Springer', [
        ( 2011, 'jun', 'Zürich', 'Switzerland' ),
        ( 2014, 'jul', 'York', 'England' ),
        ( 2015, 'jul', "L'Aquila", 'Italy' )
    ] ),
    ( 'tools', 'TOOLS', 'International Conference on Objects, Models, Components, Patterns', 'Springer', [
        ( 2012, 'may', 'Prague', 'Czech Republic' )
    ] ),
    ( 'vlsisoc', 'VLSI-SoC', 'International Conference on Very Large Scale Integration', 'IEEE', [
        ( 2015, 'oct', 'Daejon', 'Korea' )
    ] )
]

journals_data = [
    ( 'integration', 'Integration', 'Elsevier' ),
    ( 'ipl', 'Information Processing Letters', 'Elsevier' ),
    ( 'jetc', 'Journal on Emerging Technologies in Computing Systems', 'ACM' ),
    ( 'jsc', 'Journal of Symbolic Computation', 'Elsevier' ),
    ( 'mvl', 'Multiple-Valued Logic and Soft Computing', 'Old City Publishing' ),
    ( 'pra', 'Physical Review A', 'American Physical Society' ),
    ( 'sosym', 'Software and System Modeling', 'Springer' ),
    ( 'zk', 'Zeitschrift für Kristallographie - Crystalline Materials' )
]

authors_data = [
    ( 'aaa', 'Arman', 'Allahyari-Abhari' ),
    ( 'ac',  'Anupam', 'Chattopadhyay' ),
    ( 'ac2', 'Arun', 'Chandrasekharan' ),
    ( 'bs',  'Baruch', 'Sterin' ),
    ( 'cbh', 'Christopher B.', 'Harris' ),
    ( 'cg',  'Christian', 'Gorldt' ),
    ( 'ch',  'Christoph', 'Hilken' ),
    ( 'co',  'Christian', 'Otterstedt' ),
    ( 'cw',  'Clemens', 'Werther' ),
    ( 'dg',  'Daniel', 'Große' ),
    ( 'dmm', 'D. Michael', 'Miller' ),
    ( 'eg',  'Esther', 'Guerra' ),
    ( 'es',  'Eleonora', 'Schönborn' ),
    ( 'gf',  'Görschwin', 'Fey' ),
    ( 'gwd', 'Gerhard W.', 'Dueck' ),
    ( 'hml', 'Hoang M.', 'Le' ),
    ( 'hr',  'Heinz', 'Riener' ),
    ( 'igh', 'Ian G.', 'Harris' ),
    ( 'jp',  'Judith', 'Peters' ),
    ( 'js',  'Julia', 'Seiter' ),
    ( 'kdt', 'Klaus-Dieter', 'Thoben' ),
    ( 'lt',  'Laura', 'Tague' ),
    ( 'md',  'Melanie', 'Diepenbeck' ),
    ( 'mf',  'Martin', 'Freibothe' ),
    ( 'mg',  'Martin', 'Gogolla' ),
    ( 'mk',  'Mirko', 'Kuhlmann' ),
    ( 'mkt', 'Michael Kirkedal', 'Thomsen' ),
    ( 'mmr', 'Md. Mazder', 'Rahman' ),
    ( 'ms',  'Mathias', 'Soeken' ),
    ( 'na',  'Nabila', 'Abdessaied' ),
    ( 'np',  'Nils', 'Przigoda' ),
    ( 'rkb', 'Robert K.', 'Brayton' ),
    ( 'rkj', 'Robin Kaasgaard', 'Jensen' ),
    ( 'rd',  'Rolf', 'Drechsler' ),
    ( 'rw',  'Robert', 'Wille' ),
    ( 'rxf', 'Reinhard X.', 'Fischer' ),
    ( 'sf',  'Stefan', 'Frehse' ),
    ( 'sim', 'Shin-ichi', 'Minato' ),
    ( 'ss',  'Saeideh', 'Shirinzadeh' ),
    ( 'sw',  'Stefan', 'Wiesner' ),
    ( 'uk',  'Ulrich', 'Kühne' ),
    ( 'zs',  'Zahra', 'Sasanian' )
]

confpapers_data = [
    ( ['rw', 'dg', 'ms', 'rd'],                          'isvlsi',  2008, 'Using higher levels of abstraction for solving optimization problems by Boolean satisfiability', '411--416', 'http://dx.doi.org/10.1109/ISVLSI.2008.82' ),
    ( ['ms', 'mk', 'rw', 'mg', 'rd'],                    'date',    2010, 'Verifying UML/OCL models using Boolean satisfiability', '1341-1344', 'http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=5457017' ),
    ( ['ms', 'rw', 'gwd', 'rd'],                         'ddecs',   2010, 'Window optimization of reversible and quantum circuits', '341--345', 'http://dx.doi.org/10.1109/DDECS.2010.5491754' ),
    ( ['rw', 'ms', 'rd'],                                'dac',     2010, 'Reducing the number of lines in reversible circuits', '647--652', 'http://doi.acm.org/10.1145/1837274.1837439' ),
    ( ['ms', 'rw', 'rd'],                                'idt',     2010, 'Hierarchical synthesis of reversible circuits using positive and negative davio decomposition', '143--148', 'http://dx.doi.org/10.1109/IDT.2010.5724427' ),
    ( ['ms', 'rw', 'rd'],                                'date',    2011, 'Verifying dynamic aspects of UML models', '1077--1082', 'http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=5763177' ),
    ( ['ms', 'sf', 'rw', 'rd'],                          'rc',      2011, 'RevKit: An open source toolkit for the design of reversible circuits', '65--76', 'http://dx.doi.org/10.1007/978-3-642-29517-1_6' ),
    ( ['rw', 'ms', 'dg', 'es', 'rd'],                    'ismvl',   2011, 'Designing a RISC CPU in reversible logic', '170--175', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2011.39' ),
    ( ['ms', 'uk', 'mf', 'gf', 'rd'],                    'ddecs',   2011, 'Automatic property generation for the formal verification of bus bridges', '417--422', 'http://dx.doi.org/10.1109/DDECS.2011.5783129' ),
    ( ['ms', 'rw', 'rd'],                                'tap',     2011, 'Encoding OCL data types for SAT-based verification of UML/OCL models', '152--170', 'http://dx.doi.org/10.1007/978-3-642-21768-5_12' ),
    ( ['ms', 'rw', 'rd'],                                'modevva', 2011, 'Towards automatic determination of problem bounds for object instantiation in static model verification', '2', 'http://dx.doi.org/10.1145/2095654.2095657' ),
    ( ['ms', 'rw', 'np', 'ch', 'rd'],                    'aspdac',  2012, 'Synthesis of reversible circuits with minimal lines for large functions', '85--92', 'http://dx.doi.org/10.1109/ASPDAC.2012.6165069' ),
    ( ['rw', 'ms', 'rd'],                                'date',    2012, 'Debugging of inconsistent UML/OCL models', '1078--1083', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=6176655' ),
    ( ['ms', 'rw', 'rd'],                                'date',    2012, 'Eliminating invariants in UML/OCL models', '1142--1145', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=6176669' ),
    ( ['ms', 'rw', 'co', 'rd'],                          'ismvl',   2012, 'A synthesis flow for sequential reversible circuits', '299--304', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2012.72' ),
    ( ['rw', 'ms', 'np', 'rd'],                          'ismvl',   2012, 'Exact synthesis of Toffoli gate circuits with negative control lines', '69--74', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2012.71' ),
    ( ['ms', 'zs', 'rw', 'dmm', 'rd'],                   'ismvl',   2012, 'Optimizing the mapping of reversible circuits to four-valued quantum gate circuits', '173--178', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2012.64' ),
    ( ['ms', 'rw', 'rd'],                                'tools',   2012, 'Assisted behavior driven development using natural language processing', '269--287', 'http://dx.doi.org/10.1007/978-3-642-30561-0_19' ),
    ( ['rw', 'ms', 'es', 'rd'],                          'isvlsi',  2012, 'Circuit line minimization in the HDL-based synthesis of reversible logic', '213--218', 'http://dx.doi.org/10.1109/ISVLSI.2012.43' ),
    ( ['rd', 'ms', 'rw'],                                'fdl',     2012, 'Formal Specification Level: Towards verification-driven design based on natural language processing', '53--58', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=6336984' ),
    ( ['rd', 'md', 'dg', 'uk', 'hml', 'js', 'ms', 'rw'], 'icgt',    2012, 'Completeness-Driven Development', '38--50', 'http://dx.doi.org/10.1007/978-3-642-33654-6_3' ),
    ( ['md', 'ms', 'dg', 'rd'],                          'hldvt',   2012, 'Behavior driven development for circuit design and verification', '9--16', 'http://dx.doi.org/10.1109/HLDVT.2012.6418237' ),
    ( ['js', 'ms', 'rw', 'rd'],                          'rc',      2012, 'Property checking of quantum circuits using quantum multiple-valued decision diagrams', 'http://dx.doi.org/10.1007/978-3-642-36315-3_15', '183--196' ),
    ( ['ms', 'rw', 'sim', 'rd'],                         'rc',      2012, 'Using πDDs in the design for reversible circuits', '197--203', 'http://dx.doi.org/10.1007/978-3-642-36315-3_16' ),
    ( ['rw', 'ms', 'co', 'rd'],                          'aspdac',  2013, 'Improving the mapping of reversible circuits to quantum circuits using multiple target lines', '145--150', 'http://dx.doi.org/10.1109/ASPDAC.2013.6509587' ),
    ( ['rw', 'mg', 'ms', 'mk', 'rd'],                    'date',    2013, 'Towards a generic verification methodology for system models', '1193--1196', 'http://dl.acm.org/citation.cfm?id=2485575' ),
    ( ['js', 'rw', 'ms', 'rd'],                          'date',    2013, 'Determining relevant model elements for the verification of UML/OCL specifications', '1189--1192', 'http://dl.acm.org/citation.cfm?id=2485574' ),
    ( ['na', 'ms', 'rw', 'rd'],                          'ismvl',   2013, 'Exact template matching using Boolean satisfiability', '328--333', 'http://dx.doi.org/10.1109/ISMVL.2013.26' ),
    ( ['lt', 'ms', 'sim', 'rd'],                         'ismvl',   2013, 'Debugging of reversible circuits using πDDs', '316--321', 'http://dx.doi.org/10.1109/ISMVL.2013.22' ),
    ( ['md', 'ms', 'dg', 'rd'],                          'ast',     2013, 'Towards automatic scenario generation from coverage information', '82--88', 'http://dx.doi.org/10.1109/IWAST.2013.6595796' ),
    ( ['ms', 'rd', 'rxf'],                               'dgk',     2013, 'Evaluation of site occupancy factors in crystal structure refinements using Boolean satisfiability techniques', 'XXXX', '' ),
    ( ['rd', 'ms'],                                      'ddecs',   2013, 'Hardware-software co-visualization: Developing systems in the holodeck', '1--4', 'http://dx.doi.org/10.1109/DDECS.2013.6549775' ),
    ( ['na', 'rw', 'ms', 'rd'],                          'rc',      2013, 'Reducing the depth of quantum circuits using additional lines', '221--233', 'http://dx.doi.org/10.1007/978-3-642-38986-3_18' ),
    ( ['ms', 'mkt'],                                     'rc',      2013, 'White dots do matter: Rewriting reversible logic circuits', '196--208', 'http://dx.doi.org/10.1007/978-3-642-38986-3_16' ),
    ( ['ms', 'rd'],                                      'idt',     2013, 'Grammar-based program generation based on model finding', '1--5', 'http://dx.doi.org/10.1109/IDT.2013.6727084' ),
    ( ['na', 'ms', 'rd'],                                'rc',      2014, 'Quantum circuit optimization by Hadamard gate reduction', '149--162', 'http://dx.doi.org/10.1007/978-3-319-08494-7_12' ),
    ( ['dmm', 'ms', 'rd'],                               'rc',      2014, 'Mapping NCV circuits to optimized Clifford+$T$ circuits', '163--175', 'http://dx.doi.org/10.1007/978-3-319-08494-7_13' ),
    ( ['md', 'uk', 'ms', 'rd'],                          'tap',     2014, 'Behaviour driven development for tests and verification', '61--77', 'http://dx.doi.org/10.1007/978-3-319-09099-3_5' ),
    ( ['rd', 'ms', 'rw'],                                'iccad',   2014, 'Automated and quality-driven requirements engineering', '586--590', 'http://dx.doi.org/10.1109/ICCAD.2014.7001410' ),
    ( ['sw', 'cg', 'ms', 'kdt', 'rd'],                   'apms',    2014, 'Requirements engineering for cyber-physical systems - challenges in the context of "Industrie 4.0"', '281--288', 'http://dx.doi.org/10.1007/978-3-662-44739-0_35' ),
    ( ['rd', 'hml', 'ms'],                               'sbcci',   2014, 'Self-verification as the key technology for next generation electronic systems', '15:1--15:4', 'http://doi.acm.org/10.1145/2660540.2660983' ),
    ( ['ms', 'cbh', 'na', 'igh', 'rd'],                  'fdl',     2014, 'Automating the translation of assertions using natural language processing techniques', '1--8', 'http://dx.doi.org/10.1109/FDL.2014.7119356' ),
    ( ['hr', 'ms', 'cw', 'gf', 'rd'],                    'fdl',     2014, 'metaSMT: A unified interface to SMT-LIB2', '1--6', 'http://dx.doi.org/10.1109/FDL.2014.7119353' ),
    ( ['mmr', 'ms', 'gwd'],                              'ismvl',   2015, 'Dynamic template matching with mixed-polarity Toffoli gates', '72--77', 'http://dx.doi.org/10.1109/ISMVL.2015.44' ),
    ( ['ms', 'ac'],                                      'ismvl',   2015, 'Fredkin-enabled transformation-based reversible logic synthesis', '60--65', 'http://dx.doi.org/10.1109/ISMVL.2015.37' ),
    ( ['aaa', 'ms', 'rd'],                               'ddecs',   2015, 'Sentence quality assessment based on natural language processing and artificial ingelligence', '183--188', 'http://dx.doi.org/10.1109/DDECS.2015.19' ),
    ( ['ss', 'ms', 'rd'],                                'gecco',   2015, 'Multi-objective BDD optimization with evolutionary algorithms', '751--758', 'http://doi.acm.org/10.1145/2739480.2754718' ),
    ( ['ms', 'bs', 'rd', 'rkb'],                         'fmcad',   2015, 'Simulation Graphs for Reverse Engineering', 'XXXX', '' ),
    ( ['na', 'ms', 'rd'],                                'rc',      2015, 'Technology mapping for quantum circuits using Boolean functional decomposition', '219--232', 'http://dx.doi.org/10.1007/978-3-319-20860-2_14' ),
    ( ['mkt', 'rkj', 'ms'],                              'rc',      2015, 'Ricercar: A language for describing and rewriting reversible circuits with ancillae and its permutation semantics', '200--215', 'http://dx.doi.org/10.1007/978-3-319-20860-2_13' ),
    ( ['na', 'ms', 'gwd', 'rd'],                         'vlsisoc', 2015, 'Reversible circuit rewriting with simulated annealing', 'XXXX', '' ),
    ( ['ms', 'js', 'rd'],                                'tap',     2015, 'Coverage of OCL operation specifications and invariants', '191--207', 'http://dx.doi.org/10.1007/978-3-319-21215-9_12' ),
    ( ['np', 'jp', 'ms', 'rw', 'rd'],                    'modevva', 2015, 'Towards an automatic approach for restricting UML/OCL invariability clauses', 'XXXX', '' ),
    ( ['ms', 'dg', 'ac2', 'rd'],                         'aspdac',  2016, 'BDD minimization for approximate computing', 'XXXX', '' )
]

article_data = [
    ( ['ms', 'sf', 'rw', 'rd'],        'mvl',         18,  "1",      2012, 'RevKit: A toolkit for reversible circuit design',                                                   '55--65',   'http://www.oldcitypublishing.com/MVLSC/MVLSCabstracts/MVLSC18.1abstracts/MVLSCv18n1p55-65Soeken.html' ),
    ( ['rw', 'ms', 'np', 'rd'],        'mvl',         21,  "5--6",   2013, 'Effect of negative control lines on the exact synthesis of reversible circuits',                    '627--640', 'http://www.oldcitypublishing.com/MVLSC/MVLSCabstracts/MVLSC21.5-6abstracts/MVLSCv21n5-6p627-640Wille.html' ),
    ( ['ms', 'dmm', 'rd'],             'pra',         88,  "042322", 2013, 'Quantum circuits employing roots of the Pauli matrices',                                            '042322',   'http://dx.doi.org/10.1103/PhysRevA.88.042322' ),
    ( ['rw', 'ms', 'dmm', 'rd'],       'integration', 47,  "2",      2014, 'Trading off circuit lines and gate costs in the synthesis of reversible logic',                     '284--294', 'http://dx.doi.org/10.1016/j.vlsi.2013.08.002' ),
    ( ['na', 'ms', 'mkt', 'rd'],       'ipl',         114, "6",      2014, 'Upper bounds for reversible circuits based on Young subgroups',                                     '282--286', 'http://dx.doi.org/10.1016/j.ipl.2014.01.003' ),
    ( ['eg', 'ms'],                    'sosym',       14,  "2",      2015, 'Specification-driven model transformation testing',                                                 '623--644', 'http://dx.doi.org/10.1007/s10270-013-0369-x' ),
    ( ['ms', 'lt', 'gwd', 'rd'],       'jsc',         73,  "",       2016, 'Ancilla-free synthesis of large reversible functions using binary decision diagrams',               '1--26',    'http://dx.doi.org/10.1016/j.jsc.2015.03.002' ),
    ( ['ms', 'rw', 'ok', 'dmm', 'rd'], 'jetc',        -1,  "",          0, 'Embedding of large Boolean functions for reversible logic',                                         '',         '' ),
    ( ['rw', 'es', 'ms', 'rd'],        'integration', -1,  "",          0, 'SyReC: A hardware description language for the specification and synthesis of reversible circuits', '',         '' ),
    ( ['ms', 'rd', 'rxf'],             'zk',          -1,  "",          0, 'Atomic distributions in crystal structures solved by Boolean satisfiability techniques',            '',         '' )
]

authors = make_dict( 'key', authors_data, make_author )
conferences = make_dict( 'key', conferences_data, make_conference )

confpapers = list( map( make_conference_paper, confpapers_data ) )


def cmd_bibtex():
    for c in confpapers:
        format_bibtex_incollection( c )
        print()

def cmd_haml():
    for c in confpapers:
        format_haml_incollection( c )

def cmd_stats():
    num_countries = len( set( [p['conf']['venues'][p['year']]['country'] for p in confpapers] ) )
    print( "%d authors, %d conference papers, in %d countries" % ( len( authors ), len( confpapers ), num_countries ) )

def cmd_pdfs():
    for c in confpapers:
        filename = make_filename( c )

        if os.path.exists( "papers/%s.pdf" % filename ):
            if not os.path.exists( "images/thumbs/%s.png" % filename ):
                print( "[i] creating thumbnail for \"%s\" (%s %d)" % ( c['title'], c['conf']['shortname'], year ) )
                os.system( "convert papers/%s.pdf /tmp/%s.png" % ( filename, filename ) )
                os.system( "convert -trim -resize x130 /tmp/%s-0.png images/thumbs/%s.png" % ( filename, filename ) )
        else:
            print( "[w] no PDF for \"%s\" (%s %d)" % ( c['title'], c['conf']['shortname'], year ) )

if len( sys.argv ) == 2:
    globals()['cmd_%s' % sys.argv[1]]()

