#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from jinja2 import Environment, Template

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
    return dict_from_tuple( ['key', 'name', 'publisher', 'webpage'], data )

def make_author( data ):
    return dict_from_tuple( ['key', 'firstname', 'lastname'], data )

def make_university( data ):
    return dict_from_tuple( ['key', 'name', 'city', 'country', 'webpage', 'original_name'], data )

def make_conference_paper( data ):
    global conferences
    global authors

    d = dict_from_tuple( ['authors', 'conf', 'year', 'title', 'pages', 'doi', 'tools'], data )
    d['authors'] = [authors[k] for k in d['authors']]
    d['conf'] = conferences[d['conf']]
    return d

def make_article( data ):
    global journals
    global authors

    d = dict_from_tuple( ['authors', 'journal', 'volume', 'number', 'year', 'title', 'pages', 'doi', 'tools'], data )
    d['authors'] = [authors[k] for k in d['authors']]
    d['journal'] = journals[d['journal']]
    return d

def make_preprint( data ):
    global authors

    d = dict_from_tuple( ['authors', 'id', 'title', 'comments', 'ref', 'subj'], data )
    d['authors'] = [authors[k] for k in d['authors']]
    return d

def make_news( data ):
    global conferences
    global journals
    global confpapers
    global articles
    global authors

    if data[0] == 'tutorial':
        d = dict_from_tuple( ['type', 'name', 'url', 'introduction', 'authors', 'location'], data )
        d['authors'] = [authors[k] for k in d['authors']]
        d['conf'] = conferences[d['location'][0]]
        d['year'] = d['location'][1]
    else:
        d = dict_from_tuple( ['name', 'year'], data )

        if d['name'] in conferences:
            d['type'] = 'conf'
            d['papers'] = list( reversed( [p for p in confpapers if p['conf']['key'] == d['name'] and p['year'] == d['year']] ) )
        else:
            d['type'] = 'journal'
            d['papers'] = list( reversed( [a for a in articles if a['journal']['key'] == d['name'] and a['volume'] == d['year']] ) )

    return d

def make_invited( data ):
    global conferences
    global universities

    d = dict_from_tuple( ['year', 'month', 'type', 'type_key', 'host', 'title', 'webpage'], data )

    if d['type'] == 'uni':
        d['uni'] = universities[d['type_key']]
    elif d['type'] == 'conf':
        d['conf'] = conferences[d['type_key']]

    return d

def make_filename( c, collection ):
    conf = c['conf']['key']
    year = c['year']

    same_venue = [c2 for c2 in collection if c2['conf']['key'] == conf and c2['year'] == year]

    if len( same_venue ) == 1:
        return "%s_%s" % ( year, conf )
    else:
        return "%s_%s_%d" % ( year, conf, same_venue.index( c ) + 1 )

def make_bibtex_title( title ):
    global capitalize, replacements

    for c in capitalize:
        title = title.replace( c, "{%s}" % c )
    for r, s in replacements:
        title = title.replace( r, s )
    return title

def format_bibtex_incollection( paper, collection, keyword ):
    global capitalize

    conf  = paper['conf']
    venue = conf['venues'][paper['year']]

    title = make_bibtex_title( paper['title'] )

    print( "@inproceedings{%s," % make_filename( paper, collection ) )
    print( "  author    = {%s},"     % " and ".join( "%s, %s" % ( a['lastname'], a['firstname'] ) for a in paper['authors'] ) )
    print( "  title     = {%s},"     % title )
    print( "  booktitle = {%s},"     % conf['name'] )
    print( "  year      = %d,"       % paper['year'] )
    print( "  month     = %s,"       % venue['month'] )
    print( "  address   = {%s, %s}," % ( venue['city'], venue['country'] ) )
    if paper['pages'] != "XXXX":
        print( "  pages     = {%s}," % paper['pages'] )
    if conf['publisher'] != "":
        print( "  publisher = {%s}," % conf['publisher'] )
    print( "  keywords  = {%s}"      % keyword )
    print( "}" )

def format_haml_incollection( paper, id ):
    global best_paper_data

    conf  = paper['conf']
    venue = conf['venues'][paper['year']]

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    .pubassets
      {{external}}
      %a.paper(href="papers/{{filename}}.pdf" data-toggle="tooltip" data-placement="top" title="View PDF")
        %span.glyphicon.glyphicon-cloud-download
    %a.paper(href="papers/{{filename}}.pdf")
      %img.pubthumb(src="images/{{image}}.png")
    %h4.pubtitle#c{{id}}
      {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-warning Conference Paper {{id}}
      In {{conf}} ({{shortname}}) | {{city}}, {{country}}, {{month}} {{year}}{{pages}} | Publisher: {{publisher}}{{best}}''')

    authors = ",\n      ".join( "%s %s" % ( a['firstname'], a['lastname'] ) for a in paper['authors'] )
    authors = authors.replace( "Mathias Soeken", "%strong Mathias Soeken" )

    filename = make_filename( paper, confpapers )
    image = "thumbs/" + filename if os.path.exists( "images/thumbs/%s.png" % filename ) else "nothumb"

    external = ""
    if paper['doi'] != "":
        external = "%%a(href=\"%s\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open paper\" target=\"_blank\")\n        %%span.glyphicon.glyphicon-new-window" % paper['doi']

    besta = [b[1] for b in best_paper_data if b[0] == filename]
    if len( besta ) == 0:
        best = ""
    elif besta[0] == 'c':
        best = "\n    .pubcite(style=\"color: #990000\")\n      %%span.glyphicon.glyphicon-certificate\n      %b Best paper candidate"

    print( template.render( {'title': paper['title'],
                             'id': id,
                             'filename': filename,
                             'image': image,
                             'authors': authors,
                             'conf': conf['name'],
                             'shortname': conf['shortname'],
                             'city': venue['city'],
                             'country': venue['country'],
                             'month': monthnames[venue['month']],
                             'year': venue['year'],
                             'external': external,
                             'pages': " | Pages %s" % paper['pages'].replace( "--", "&ndash;" ) if paper['pages'] != "XXXX" else "",
                             'publisher': conf['publisher'],
                             'best': best} )[1:] )

def format_haml_incollection_work( paper, id ):
    conf  = paper['conf']
    venue = conf['venues'][paper['year']]

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    %h4.pubtitle#w{{id}}
      {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-warning Workshop Paper {{id}}
      In {{conf}} ({{shortname}}) | {{city}}, {{country}}, {{month}} {{year}}{{pages}} | Publisher: {{publisher}}''')

    authors = ",\n      ".join( "%s %s" % ( a['firstname'], a['lastname'] ) for a in paper['authors'] )
    authors = authors.replace( "Mathias Soeken", "%strong Mathias Soeken" )

    filename = make_filename( paper, workpapers )
    image = "thumbs/" + filename if os.path.exists( "images/thumbs/%s.png" % filename ) else "nothumb"

    external = ""
    if paper['doi'] != "":
        external = "%%a(href=\"%s\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open paper\" target=\"_blank\")\n        %%span.glyphicon.glyphicon-new-window" % paper['doi']

    print( template.render( {'title': paper['title'],
                             'id': id,
                             'filename': filename,
                             'image': image,
                             'authors': authors,
                             'conf': conf['name'],
                             'shortname': conf['shortname'],
                             'city': venue['city'],
                             'country': venue['country'],
                             'month': monthnames[venue['month']],
                             'year': venue['year'],
                             'external': external,
                             'pages': " | Pages %s" % paper['pages'].replace( "--", "&ndash;" ) if paper['pages'] != "XXXX" else "",
                             'publisher': conf['publisher']} )[1:] )

def format_bibtex_article( paper ):
    global capitalize

    journal = paper["journal"]

    name = make_bibtex_title( journal["name"] )
    title = make_bibtex_title( paper['title'] )

    print( "@article{%s%d," % ( journal['key'], paper['year'] ) )
    print( "  author    = {%s},"     % " and ".join( "%s, %s" % ( a['lastname'], a['firstname'] ) for a in paper['authors'] ) )
    print( "  title     = {%s},"     % title )
    print( "  journal   = {%s},"     % name )
    if paper['volume'] == -1:
        print( "  note      = {in press}," )
    else:
        print( "  year      = %d,"       % paper['year'] )
        print( "  volume    = %d,"       % paper['volume'] )
        print( "  number    = {%s},"       % paper['number'] )
        if paper['pages'] != "XXXX":
            print( "  pages     = {%s}," % paper['pages'] )
    print( "  publisher = {%s},"     % journal['publisher'] )
    print( "  keywords  = {article}" )
    print( "}" )

def format_haml_article( paper, id ):
    journal = paper['journal']

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    .pubassets
      {{external}}
      /
        %a(href="papers/{{filename}}.pdf" data-toggle="tooltip" data-placement="top" title="View PDF")
          %span.glyphicon.glyphicon-cloud-download
    %a(href="{{webpage}}" target="_blank")
      %img.pubthumb(src="images/covers/{{key}}.png" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open journal homepage\")
    %h4.pubtitle#j{{id}} {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-info Journal Article {{id}}
      In {{journal}} {{info}}{{pages}} | Publisher: {{publisher}}''')

    authors = ",\n      ".join( "%s %s" % ( a['firstname'], a['lastname'] ) for a in paper['authors'] )
    authors = authors.replace( "Mathias Soeken", "%strong Mathias Soeken" )

    number = "(%s)" % paper['number'] if paper['number'] != "" else ""

    external = ""
    if paper['doi'] != "":
        external = "%%a(href=\"%s\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open paper\" target=\"_blank\")\n        %%span.glyphicon.glyphicon-new-window" % paper['doi']

    if paper['volume'] == -1:
        info = ""
    else:
        info = "%s%s, %s" % ( paper['volume'], number, paper['year'] )

    print( template.render( {'title': paper['title'],
                             'id': id,
                             'key': journal['key'],
                             'filename': "",
                             'webpage': paper['journal']['webpage'],
                             'authors': authors,
                             'journal': paper['journal']['name'],
                             'info': info,
                             'pages': " | Pages %s" % paper['pages'].replace( "--", "&ndash;" ) if paper['pages'] != "XXXX" else "",
                             'external': external,
                             'publisher': journal['publisher']} )[1:] )

def format_bibtex_preprint( paper ):
    global capitalize

    title = make_bibtex_title( paper['title'] )

    print( "@article{arxiv_%s,"     % paper['id'] )
    print( "  author    = {%s},"    % " and ".join( "%s, %s" % ( a['lastname'], a['firstname'] ) for a in paper['authors'] ) )
    print( "  title     = {%s},"    % title )
    print( "  journal   = {arXiv}," )
    print( "  year      = {%s},"      % ( '20' + paper['id'][0:2] ) )
    print( "  volume    = {%s},"    % paper['id'] )
    print( "  keywords  = {preprint}" )
    print( "}" )

def format_haml_preprint( paper, id ):
    global months

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    .pubassets
      %a(href="http://arxiv.org/abs/{{id}}" data-toggle="tooltip" data-placement="top" title="Open webpage" target="_blank")
        %span.glyphicon.glyphicon-new-window
      %a(href="http://arxiv.org/pdf/{{id}}" data-toggle="tooltip" data-placement="top" title="View PDF" target="_blank")
        %span.glyphicon.glyphicon-cloud-download
    %a.paper(href="http://arxiv.org/pdf/{{id}}" target="_blank")
      %img.pubthumb(src="images/thumbs/arxiv_{{id}}.png")
    %h4.pubtitle#p{{nid}} {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-danger Preprint {{nid}}
      arXiv:{{id}} | {{month}} {{year}}
      {{ref}}| Comments: {{comments}} | Subjects: {{subjects}}''')

    authors = ",\n      ".join( "%s %s" % ( a['firstname'], a['lastname'] ) for a in paper['authors'] )
    authors = authors.replace( "Mathias Soeken", "%strong Mathias Soeken" )

    subjects = "; ".join( paper['subj'] )

    ref = ""
    if paper['ref'] != "":
        ref = "|\n      %%a(href=\"publications.html#%s\") Reference\n      " % paper['ref']

    print( template.render( {'title': paper['title'],
                             'authors': authors,
                             'id': paper['id'],
                             'nid': id,
                             'month': months[int( paper['id'][2:4] ) - 1],
                             'year': '20' + paper['id'][0:2],
                             'comments': paper['comments'],
                             'ref': ref,
                             'subjects': subjects } ) )

def format_haml_news( news ):
    print( "%li.list-group-item" )

    if news['type'] == "conf":
        papers = news['papers']

        if len( papers ) == 1:
            article = "  %%a(href=\"publications.html#c%i\") %s\n" % ( confpapers.index( papers[0] ) + 1, papers[0]["title"] )
        else:
            article = "  %ul\n"
            for p in papers:
                article += "    %%li\n      %%a(href=\"publications.html#c%i\") %s\n" % ( confpapers.index( p) + 1, p["title"] )
        print( "  The paper%s\n%s  %s been accepted by the %s %d conference.\n  %%a.badge(href=\"publications.html#conferences\") publication" % ( "s" if len( papers ) > 1 else "", article, "have" if len( papers ) > 1 else "has", papers[0]["conf"]["shortname"], papers[0]["year"] ) )
    if news['type'] == "journal":
        papers = news['papers']

        if len( papers ) == 1:
            article = "  %%a(href=\"publications.html#j%i\") %s\n" % ( articles.index( papers[0] ) + 1, papers[0]["title"] )
        else:
            article = "  %ul\n"
            for p in papers:
                article += "    %%li\n      %%a(href=\"publications.html#j%i\") %s\n" % ( articles.index( p) + 1, p["title"] )
        print( "  The article%s\n%s  got accepted for publication in\n  %%i %s.\n  %%a.badge(href=\"publications.html\") publication" % ( "s" if len( papers ) > 1 else "", article, papers[0]["journal"]["name"] ) )
    if news['type'] == "tutorial":
        print( "  %s\n  %%a(href=\"%s\" target=\"_blank\") %s" % (news['introduction'], news['url'], news['name']) )
        if len( news['authors'] ) > 0:
            authors = ", ".join( "%s %s" % ( a['firstname'], a['lastname'] ) for a in news['authors'] )
            print( "  with %s" % authors )
        conf = news['conf']
        venue = conf['venues'][news['year']]
        print( "  in %s, %s at the %s %d conference.\n  %%a.badge(href=\"#\") tutorial" % (venue['city'], venue['country'], conf['shortname'], news['year']) )

def write_publications():
    global confpapers

    text = Template('''
\documentclass[conference]{IEEEtran}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}

    \\usepackage[backend=biber,style=ieee]{biblatex}
\\addbibresource{publications.bib}

\\title{List of Publications}
\\author{
  \IEEEauthorblockN{Mathias Soeken}
  \IEEEauthorblockA{Integrated Systems Laboratory, EPFL, Switzerland}
}

\\begin{document}
  \\maketitle

  \\nocite{*}
  \printbibliography[type=book,title={Books}]
  \printbibliography[type=incollection,title={Book chapters}]
  \printbibliography[type=article,keyword=article,title={Journal articles}]
  \printbibliography[type=inproceedings,keyword=conference,title={Conference papers}]
  \printbibliography[type=article,keyword=preprint,title={Preprints}]
  \printbibliography[type=inproceedings,keyword=workshop,title={Refereed papers without formal proceedings}]
\end{document}''')

    with open( "publications.tex", "w" ) as f:
        f.write( text.render().strip() + "\n" )

def format_haml_invited( invited ):
    template = Template('''
.pitem
  .pubmain(style="min-height:0px")
    {{ logo }}
    %h4.pubtitle {{ title }}
    .project-description
      Talk
      %i {{ talk_title }}
      {{ host }}
      ({{ month }}{{ year }})
    {{ more }}''')

    if invited['type'] == "uni":
        uni = invited['uni']
        title = uni['name']
        if uni['original_name'] != '':
            title += " (" + uni['original_name'] + ")"
        logo = '%%a(href="%s" target="_blank")\n      %%img.project-thumb(src="images/logos/%s.png" border="0")' % ( uni['webpage'], uni['key'] )
        host = 'invited by ' + invited['host']
    else:
        conf = invited['conf']
        title = conf['name'] + " " + str( invited['year'] )
        logo = ''
        host = ''

    if invited['webpage'] != '':
        more = '.project-description\n      %%a(href="%s" target="_blank") More information' % invited['webpage']
    else:
        more = ''

    talk_title = invited['title']
    month = monthnames[invited['month']] + " " if invited['month'] != '' else ''
    year = invited['year']

    print( template.render( title = title, logo = logo, talk_title = talk_title, host = host, month = month, year = year, more = more ) )


monthnames = {'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April', 'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August', 'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December'}
months = ["January", "Feburary", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
capitalize = ["AIGs", "Alle", "Ausdrücken", "BDD", "Beschreibungen", "Boolean", "CMOS", "Completeness-Driven Development", "CPU", "DAG", "EPFL", "ESL", "ESOP", "Formal Specification Level", "Fredkin", "Gröbner", "Hadamard", "HDL", "IDE", "Industrie", "LEXSAT", "lips", "LUT", "LUTs", "metaSMT", "Methoden", "MIG", "MPSoC", "NCV", "NoC", "NPN", "OCL", "Pauli", "QCA", "QPUs", "RevKit", "RISC", "RRAM", "SAT", "SMT-LIB2", "STMG", "SyReC", "Toffoli", "UML", "XOR"]
replacements = [("Clifford+T", "{Clifford+$T$}"), ("ε", "{$\\varepsilon$}"), ("δ", "{$\\delta$}"), ("πDD", "{$\\pi$DD}"), ("&", "\&"), ("T-count", "{$T$-count}")]

conferences_data = [
    ( 'apms', 'APMS', 'Advances in Production Management Systems', 'IFIP', [
        ( 2014, 'sep', 'Ajaccio', 'France' )
    ] ),
    ( 'aspdac', 'ASP-DAC', 'Asia and South Pacific Design Automation Conference', 'IEEE', [
        ( 2012, 'jan', 'Sydney', 'Australia' ),
        ( 2013, 'jan', 'Yokohama', 'Japan' ),
        ( 2016, 'jan', 'Macau', 'China' ),
        ( 2017, 'jan', 'Tokyo', 'Japan' ),
        ( 2018, 'jan', 'Jeju Island', 'Korea' ),
        ( 2019, 'jan', 'Tokyo', 'Japan' )
    ] ),
    ( 'ast', 'AST', 'International Workshop on Automation of Software Test', 'ACM', [
        ( 2013, 'may', 'San Francisco, CA', 'USA' )
    ] ),
    ( 'costts', '', 'COST IC1405 Training School', '', [
        ( 2017, 'aug', 'Torun', 'Poland' )
    ] ),
    ( 'cukeup', '', 'CukeUp!', 'Skills Matter', [
        ( 2012, 'apr', 'London', 'England' ),
        ( 2013, 'apr', 'London', 'England' )
    ] ),
    ( 'dac', 'DAC', 'Design Automation Conference', 'ACM/IEEE', [
        ( 2010, 'jun', 'Anaheim, CA', 'USA' ),
        ( 2016, 'jun', 'Austin, TX', 'USA' ),
        ( 2017, 'jun', 'Austin, TX', 'USA' ),
        ( 2018, 'jun', 'San Francisco, CA', 'USA' ),
        ( 2019, 'jun', 'Las Vegas, NV', 'USA' )
    ] ),
    ( 'date', 'DATE', 'Design, Automation and Test in Europe', 'IEEE', [
        ( 2010, 'mar', 'Dresden', 'Germany' ),
        ( 2011, 'mar', 'Grenoble', 'France' ),
        ( 2012, 'mar', 'Dresden', 'Germany' ),
        ( 2013, 'mar', 'Grenoble', 'France' ),
        ( 2014, 'mar', 'Dresden', 'Germany' ),
        ( 2015, 'mar', 'Grenoble', 'France' ),
        ( 2016, 'mar', 'Dresden', 'Germany' ),
        ( 2017, 'mar', 'Lausanne', 'Switzerland' ),
        ( 2018, 'mar', 'Dresden', 'Germany' ),
        ( 2019, 'mar', 'Florence', 'Italy' ),
        ( 2020, 'mar', 'Grenoble', 'France' )
    ] ),
    ( 'ddecs', 'DDECS', 'IEEE International Symposium on Design and Diagnostics of Electronic Circuits and Systems', 'IEEE', [
        ( 2010, 'apr', 'Vienna', 'Austria' ),
        ( 2011, 'apr', 'Cottbus', 'Germany' ),
        ( 2013, 'apr', 'Karlovy Vary', 'Czech Republic' ),
        ( 2015, 'apr', 'Belgrad', 'Serbia' ),
        ( 2016, 'apr', 'Košice', 'Slovakia' )
    ] ),
    ( 'dice', 'DICE', 'Developments in Implicit Computational Complexity', '', [
        ( 2018, 'apr', 'Thessaloniki', 'Greece' )
    ] ),
    ( 'difts', 'DIFTS', 'International Workshop on Design and Implementation of Formal Tools and Systems', '', [
        ( 2014, 'oct', 'Lausanne', 'Switzerland' )
    ] ),
    ( 'dgk', 'DGK', 'Annual Conference of the German Crystallographic Society', '', [
        ( 2013, 'mar', 'Freiberg', 'Germany' )
    ] ),
    ( 'duhde', 'DUHDe', 'DATE Friday Workshop: Design Automation for Understanding Hardware Designs', '', [
        ( 2014, 'mar', 'Dresden', 'Germany' ),
        ( 2015, 'mar', 'Grenoble', 'France' ),
        ( 2016, 'mar', 'Dresden', 'Germany' )
    ] ),
    ( 'fdl', 'FDL', 'Forum on Specification and Design Languages', 'IEEE', [
        ( 2012, 'sep', 'Vienna', 'Austria' ),
        ( 2014, 'oct', 'Munich', 'Germany' )
    ] ),
    ( 'fmcad', 'FMCAD', 'Formal Methods in Computer-Aided Design', 'IEEE', [
        ( 2015, 'sep', 'Austin, TX', 'USA' ),
        ( 2016, 'oct', 'Mountain View, CA', 'USA' )
    ] ),
    ( 'fpl', 'FPL', 'International Conference on Field-Programmable Logic and Applications', 'IEEE', [
        ( 2016, 'sep', 'Lausanne', 'Switzerland' )
    ] ),
    ( 'gecco', 'GECCO', 'Genetic and Evolutionary Computation Conference', 'ACM', [
        ( 2015, 'jul', 'Madrid', 'Spain' ),
        ( 2016, 'jul', 'Denver, CO', 'USA' ),
        ( 2017, 'jul', 'Berlin', 'Germany' )
    ] ),
    ( 'gi', 'GI', 'Jahrestagung der Gesellschaft für Informatik', 'GI', [
        ( 2013, 'sep', 'Koblenz', 'Germany' )
    ] ),
    ( 'glsvlsi', 'GLSVLSI', 'Great Lakes Symposium on VLSI', 'ACM', [
        ( 2017, 'may', 'Banff, AB', 'Canada' )
    ] ),
    ( 'hldvt', 'HLDVT', 'International Workshop on High-Level Design Validation and Test', 'IEEE', [
        ( 2012, 'nov', 'Huntington Beach, CA', 'USA' )
    ] ),
    ( 'hvc', 'HVC', 'Haifa Verification Conference', 'Springer', [
        ( 2016, 'nov', 'Haifa', 'Israel' )
    ] ),
    ( 'iccad', 'ICCAD', 'International Conference on Computer-Aided Design', 'IEEE', [
        ( 2014, 'nov', 'San Jose, CA', 'USA' ),
        ( 2016, 'nov', 'Austin, TX', 'USA' ),
        ( 2017, 'nov', 'Irvine, CA', 'USA' ),
        ( 2018, 'nov', 'San Diego, CA', 'USA' ),
        ( 2019, 'nov', 'Westminster, CO', 'USA' )
    ] ),
    ( 'icecs', 'ICECS', 'International Conference on Electronics, Circuits and Systems', 'IEEE', [
        ( 2018, 'dec', 'Bordeaux', 'France' )
    ] ),
    ( 'icgt', 'ICGT', 'International Conference on Graph Transformation', 'Springer', [
        ( 2012, 'sep', 'Bremen', 'Germany' )
    ] ),
    ( 'idt', 'IDT', 'International Test and Design Symposium', 'IEEE', [
        ( 2010, 'dec', 'Abu Dhabi', 'United Arab Emirates' ),
        ( 2013, 'dec', 'Marrakesh', 'Marocco' )
    ] ),
    ( 'iscas', 'ISCAS', 'International Symposium on Circuits and Systems', 'IEEE', [
        ( 2016, 'may', 'Montreal, QC', 'Canada' ),
        ( 2017, 'may', 'Baltimore, MD', 'USA' ),
        ( 2018, 'may', 'Florence', 'Italy' ),
        ( 2019, 'may', 'Sapporo', 'Japan' ),
        ( 2020, 'oct', 'Servilla', 'Spain' )
    ] ),
    ( 'ismvl', 'ISMVL', 'International Symposium on Multiple-Valued Logic', 'IEEE', [
        ( 2011, 'may', 'Tuusula', 'Finland' ),
        ( 2012, 'may', 'Victoria, BC', 'Canada' ),
        ( 2013, 'may', 'Toyama', 'Japan' ),
        ( 2015, 'may', 'Waterloo, ON', 'Canada' ),
        ( 2016, 'may', 'Sapporo', 'Japan' ),
        ( 2017, 'may', 'Novi Sad', 'Serbia' ),
        ( 2018, 'may', 'Linz', 'Austria' ),
        ( 2019, 'may', 'Fredericton', 'Canada' ),
        ( 2020, 'nov', 'Miyazaki', 'Japan' )
    ] ),
    ( 'isvlsi', 'ISVLSI', 'IEEE Computer Society Annual Symposium on VLSI', 'IEEE', [
        ( 2008, 'apr', 'Montpellier', 'France' ),
        ( 2012, 'aug', 'Amherst, MA', 'USA' ),
        ( 2017, 'jul', 'Bochum', 'Germany' )
    ] ),
    ( 'iwls', 'IWLS', 'International Workshop on Logic Synthesis', '', [
        ( 2015, 'jun', 'Mountain View, CA', 'USA' ),
        ( 2016, 'jun', 'Austin, TX', 'USA' ),
        ( 2017, 'jun', 'Austin, TX', 'USA' ),
        ( 2018, 'jun', 'San Francisco, CA', 'USA' ),
        ( 2019, 'jun', 'Lausanne', 'Switzerland' ),
        ( 2020, 'jun', 'Salt Lake City, UT', 'USA' )
    ] ),
    ( 'iwsbp', 'IWSBP', 'International Workshop on Boolean Problems', '', [
        ( 2012, 'sep', 'Freiberg', 'Germany' ),
        ( 2014, 'sep', 'Freiberg', 'Germany' ),
        ( 2016, 'sep', 'Freiberg', 'Germany' )
    ] ),
    ( 'lascas', 'LASCAS', 'IEEE Latin Amarican Symposium on Circuits and Systems', 'IEEE', [
        ( 2016, 'feb', 'Florianopolis', 'Brazil' )
    ] ),
    ( 'mbmv', 'MBMV', 'Methoden und Beschreibungssprachen zur Modellierung und Verifikation von Schaltungen und Systemen', '', [
        ( 2010, 'mar', 'Dresden', 'Germany' ),
        ( 2011, 'mar', 'Oldenburg', 'Germany' ),
        ( 2013, 'mar', 'Rostock', 'Germany' ),
        ( 2014, 'mar', 'Böblingen', 'Germany' ),
        ( 2016, 'mar', 'Freiburg', 'Germany' )
    ] ),
    ( 'mecoes', 'MeCoES', 'International Workshop on and Code Generation for Embedded Systems', '', [
        ( 2012, 'oct', 'Tampere', 'Finland' )
    ] ),
    ( 'modevva', 'MoDeVVa', 'Model-Driven Engineering, Verification, And Validation', 'ACM', [
        ( 2011, 'oct', 'Wellington', 'New Zealand' ),
        ( 2015, 'oct', 'Ottawa, ON', 'Canada' )
    ] ),
    ( 'nanoarch', 'NANOARCH', 'International Symposium on Nanoscale Architectures', 'IEEE', [
        ( 2016, 'jul', 'Beijing', 'China' ),
        ( 2018, 'jul', 'Athens', 'Greece' )
    ] ),
    ( 'naturalise', 'NaturaLiSE', 'International Workshop on Natural Language Analysis in Software Engineering', '', [
        ( 2013, 'may', 'San Francisco, CA', 'USA' )
    ] ),
    ( 'newcas', 'NEWCAS', 'International NEWCAS Conference', 'IEEE', [
        ( 2017, 'jun', 'Strasbourg', 'France' )
    ] ),
    ( 'oopsla', 'OOPSLA', 'ACM SIGPLAN International Conference on Object-Oriented Programming, Systems, Languages, and Applications', 'ACM', [
        ( 2020, 'nov', 'Chicao, IL', 'USA' )
    ] ),
    ( 'pacrim', 'PACRIM', 'Pacific Rim Conference on Communications, Computers and Signal Processing', '', [
        ( 2019, 'aug', 'Victoria, BC', 'Canada' )
    ] ),
    ( 'pqcrypto', 'PQCrypto', 'International Conference on Post-Quantum Cryptography', 'Springer', [
        ( 2020, 'apr', 'Paris', 'France' )
    ] ),
    ( 'qce', 'QCE', 'IEEE Quantum Week', 'IEEE', [
        ( 2020, 'oct', 'Boulder, CO', 'USA' )
    ]),
    ( 'qpl', 'QPL', 'Quantum Physics and Logic', 'ENTCS', [
        ( 2019, 'jun', 'Orange, CA', 'USA' )
    ] ),
    ( 'rc', 'RC', 'Conference on Reversible Computation', 'Springer', [
        ( 2011, 'jul', 'Ghent', 'Belgium' ),
        ( 2012, 'jul', 'Copenhagen', 'Denmark' ),
        ( 2013, 'jul', 'Victoria, BC', 'Canada' ),
        ( 2014, 'jul', 'Kyoto', 'Japan' ),
        ( 2015, 'jul', 'Grenoble', 'France' ),
        ( 2016, 'jul', 'Bologna', 'Italy' ),
        ( 2018, 'sep', 'Leicester', 'England' )
    ] ),
    ( 'rcss', '', 'Reversible Computation Summer School', '', [
        ( 2017, 'jul', 'Kolkata', 'India' )
    ] ),
    ( 'rcw', 'RC', 'Workshop on Reversible Computation', 'Springer', [
        ( 2010, 'jul', 'Bremen', 'Germany' ),
        ( 2011, 'jul', 'Ghent', 'Belgium' ),
    ] ),
    ( 'rm', 'RM', 'Reed-Muller Workshop', '', [
        ( 2015, 'may', 'Waterloo, ON', 'Canada' ),
        ( 2017, 'may', 'Novi Sad', 'Serbia' ),
        ( 2019, 'may', 'Fredericton, NB', 'Canada' )
    ] ),
    ( 'sat', 'SAT', 'International Conference on Theory and Applications of Satisfiability Testing', 'Springer', [
        ( 2016, 'jul', 'Bordeaux', 'France' )
    ] ),
    ( 'sbcci', 'SBCCI', 'Symposium on Integrated Circuits and Systems Design', 'ACM', [
        ( 2014, 'sep', 'Aracaju', 'Brazil' )
    ] ),
    ( 'sec', 'SEC', 'International Workshop on the Swarm at the Edge of the Cloud', '', [
        ( 2013, 'sep', 'Montreal, QC', 'Canada' )
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
    ] ),
    ( 'woset', 'WOSET', 'Workshop on Open-Source EDA Technology', '', [
        ( 2018, 'nov', 'San Diego, CA', 'USA' )
    ] )
]

journals_data = [
    ( 'access', 'IEEE Access', 'IEEE', 'https://ieeeaccess.ieee.org' ),
    ( 'cnf', 'Combustion and Flame', 'Elsevier', 'http://www.journals.elsevier.com/combustion-and-flame/' ),
    ( 'computer', 'Computer', 'IEEE', 'https://www.computer.org/computer-magazine/' ),
    ( 'cps', 'Cyber-Physical Systems: Theory & Applications', 'IET', 'http://digital-library.theiet.org/content/journals/iet-cps;jsessionid=15e1smt7vf2ux.x-iet-live-01' ),
    ( 'integration', 'Integration', 'Elsevier', 'http://www.journals.elsevier.com/integration-the-vlsi-journal/' ),
    ( 'ipl', 'Information Processing Letters', 'Elsevier', 'http://www.journals.elsevier.com/information-processing-letters/' ),
    ( 'jetc', 'Journal on Emerging Technologies in Computing Systems', 'ACM', 'http://jetc.acm.org/' ),
    ( 'jsc', 'Journal of Symbolic Computation', 'Elsevier', 'http://www.journals.elsevier.com/journal-of-symbolic-computation/' ),
    ( 'mvl', 'Multiple-Valued Logic and Soft Computing', 'Old City Publishing', 'http://www.oldcitypublishing.com/journals/mvlsc-home/' ),
    ( 'npjqi', 'npj Quantum Information', 'Springer Nature', 'https://www.nature.com/npjqi/' ),
    ( 'nrp', 'Nature Reviews Physics', 'Springer Nature', 'https://www.nature.com/natrevphys/' ),
    ( 'pra', 'Physical Review A', 'American Physical Society', 'http://journals.aps.org/pra/' ),
    ( 'procieee', 'Proceedings of the IEEE', 'IEEE', 'http://proceedingsoftheieee.ieee.org' ),
    ( 'rsta', 'Philosophical Transactions of the Royal Society A', 'The Royal Society Publishing', 'https://royalsocietypublishing.org/journal/rsta' ),
    ( 'sosym', 'Software and System Modeling', 'Springer', 'http://www.sosym.org/' ),
    ( 'sttt', 'Journal on Software Tools for Technology Transfer', 'Springer', 'http://www.springer.com/computer/swe/journal/10009' ),
    ( 'tcad', 'IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems', 'IEEE', 'http://ieee-ceda.org/publication/tcad-publication' ),
    ( 'tc', 'IEEE Transactions on Computer', 'IEEE', 'https://www.computer.org/csdl/journal/tc' ),
    ( 'tcs', 'Theoretical Computer Science', 'Elsevier', 'http://www.journals.elsevier.com/theoretical-computer-science/' ),
    ( 'tqc', 'ACM Transactions on Quantum Computing', 'ACM', 'https://dl.acm.org/journal/tqc' ),
    ( 'tqe', 'IEEE Transactions on Quantum Engineering', 'IEEE', 'https://tqe.ieee.org' ),
    ( 'zk', 'Zeitschrift für Kristallographie - Crystalline Materials', 'De Gruyter', 'http://www.degruyter.com/view/j/zkri' )
]

authors_data = [
    ( 'aaa', 'Arman', 'Allahyari-Abhari' ),
    ( 'ac',  'Anupam', 'Chattopadhyay' ),
    ( 'ac2', 'Arun', 'Chandrasekharan' ),
    ( 'ad',  'Antun', 'Domic' ),
    ( 'adm', 'Anton', 'De Meester' ),
    ( 'adv', 'Alexis', 'De Vos' ),
    ( 'ag',  'Alan', 'Geller' ),
    ( 'am',  'Alan', 'Mishchenko' ),
    ( 'an', 'Azad', 'Naeemi' ),
    ( 'ap',  'Ana', 'Petkovska' ),
    ( 'asa', 'Amr', 'Sayed Ahmed' ),
    ( 'av',  'Adrien', 'Vaysset' ),
    ( 'bb',  'Bernd', 'Becker' ),
    ( 'bh',  'Bettina', 'Heim' ),
    ( 'bs',  'Baruch', 'Sterin' ),
    ( 'bs2', 'Benoit', 'Seguin' ),
    ( 'bs3', 'Bruno', 'Schmitt' ),
    ( 'cbh', 'Christopher B.', 'Harris' ),
    ( 'cc',  'Christopher', 'Casares' ),
    ( 'cg',  'Christian', 'Gorldt' ),
    ( 'cg2', 'Christopher', 'Granade' ),
    ( 'ch',  'Christoph', 'Hilken' ),
    ( 'co',  'Christian', 'Otterstedt' ),
    ( 'cr',  'Christopher D.', 'Rosebrock' ),
    ( 'cw',  'Clemens', 'Werther' ),
    ( 'db',  'Debjyoti', 'Bhattacharjee' ),
    ( 'df',  'Daniel', 'Florez' ),
    ( 'dg',  'Daniel', 'Große' ),
    ( 'dm',  'Dewmini Sudara', 'Marakkalage' ),
    ( 'dmm', 'D. Michael', 'Miller' ),
    ( 'ec',  'Edo', 'Collins' ),
    ( 'ec2', 'Earl', 'Campbell' ),
    ( 'eg',  'Esther', 'Guerra' ),
    ( 'ek',  'Eugen', 'Kuksa' ),
    ( 'el',  'Erkko', 'Lehtonen' ),
    ( 'es',  'Eleonora', 'Schönborn' ),
    ( 'et',  'Eleonora', 'Testa' ),
    ( 'fc',  'Francky', 'Catthoor' ),
    ( 'fh',  'Finn', 'Haedicke' ),
    ( 'fk',  'Frédéric', 'Kaplan' ),
    ( 'fm',  'Fereshte', 'Mozafari' ),
    ( 'gdm', 'Giovanni', 'De Micheli' ),
    ( 'gf',  'Görschwin', 'Fey' ),
    ( 'gg',  'Guy', 'Gogniat' ),
    ( 'gm',  'Giulia', 'Meuli' ),
    ( 'gwd', 'Gerhard W.', 'Dueck' ),
    ( 'gz',  'Grace', 'Zgheib' ),
    ( 'hml', 'Hoang M.', 'Le' ),
    ( 'hr',  'Heinz', 'Riener' ),
    ( 'igh', 'Ian G.', 'Harris' ),
    ( 'ik',  'Ina', 'Kodrasi' ),
    ( 'jd',  'Jeroen', 'Demeyer' ),
    ( 'jl',  'Jiong', 'Luo' ),
    ( 'jo',  'Janet', 'Olson' ),
    ( 'jp',  'Judith', 'Peters' ),
    ( 'jpd', 'Jean-Philippe', 'Diguet' ),
    ( 'js',  'Julia', 'Seiter' ),
    ( 'js2', 'Johanna', 'Sepulveda' ),
    ( 'kdt', 'Klaus-Dieter', 'Thoben' ),
    ( 'kms', 'Krysta M.', 'Svore' ),
    ( 'ks',  'Kaitlin', 'Smith' ),
    ( 'la',  'Luca Gaetano', 'Amarù' ),
    ( 'lm',  'Lutz', 'Mädler' ),
    ( 'lt',  'Laura', 'Tague' ),
    ( 'lw',  'Lunyao', 'Wang' ),
    ( 'ma',  'Matthew', 'Amy' ),
    ( 'mc',  'Miguel', 'Couceiro' ),
    ( 'md',  'Melanie', 'Diepenbeck' ),
    ( 'mf',  'Martin', 'Freibothe' ),
    ( 'mg',  'Martin', 'Gogolla' ),
    ( 'mk',  'Mirko', 'Kuhlmann' ),
    ( 'mkt', 'Michael Kirkedal', 'Thomsen' ),
    ( 'mm',  'Marc', 'Michael' ),
    ( 'mm2', 'Mauricio', 'Manfrini' ),
    ( 'mmr', 'Md. Mazder', 'Rahman' ),
    ( 'mn',  'Max', 'Nitze' ),
    ( 'mn2', 'Michael', 'Naehrig' ),
    ( 'mr',  'Martin', 'Roetteler' ),
    ( 'ms',  'Mathias', 'Soeken' ),
    ( 'ms2', 'Matthias', 'Sauer' ),
    ( 'mt',  'Mitchell A.', 'Thornton' ),
    ( 'mt2', 'Matthias', 'Troyer' ),
    ( 'na',  'Nabila', 'Abdessaied' ),
    ( 'nb',  'Nikolaj', 'Bjorner' ),
    ( 'np',  'Nils', 'Przigoda' ),
    ( 'nr',  'Norbert', 'Riefler' ),
    ( 'nw',  'Nathan', 'Wiebe' ),
    ( 'ok',  'Oliver', 'Keszocze' ),
    ( 'oz',  'Odysseas', 'Zografos' ),
    ( 'peg', 'Pierre-Emmanuel', 'Gaillardon' ),
    ( 'pi',  'Paolo', 'Ienne' ),
    ( 'pm',  'Pierre', 'Mercuriali' ),
    ( 'pr',  'Pascal', 'Raiola' ),
    ( 'pr2', 'Praveen', 'Raghavan' ),
    ( 'pv',  'Patrick', 'Vuillod' ),
    ( 'rkb', 'Robert K.', 'Brayton' ),
    ( 'rkj', 'Robin Kaasgaard', 'Jensen' ),
    ( 'rd',  'Rolf', 'Drechsler' ),
    ( 'rl',  'Rudy', 'Lauwereins' ),
    ( 'rp',  'Romain', 'Péchoux' ),
    ( 'rw',  'Robert', 'Wille' ),
    ( 'rxf', 'Reinhard X.', 'Fischer' ),
    ( 'sd',  'Srijit', 'Dutta' ),
    ( 'sf',  'Stefan', 'Frehse' ),
    ( 'sim', 'Shin-ichi', 'Minato' ),
    ( 'sj',  'Samuel', 'Jaques' ),
    ( 'sln', 'Samantha Lubaba', 'Noor' ),
    ( 'sm',  'Sarah', 'Marshall' ),
    ( 'sr',  'Sandip', 'Ray' ),
    ( 'ss',  'Saeideh', 'Shirinzadeh' ),
    ( 'ss2', 'Sabine', 'Süsstrunk' ),
    ( 'sw',  'Stefan', 'Wiesner' ),
    ( 'th',  'Thomas', 'Haener' ),
    ( 'tw',  'Thomas', 'Wriedt' ),
    ( 'uk',  'Ulrich', 'Kühne' ),
    ( 'wc',  'Wouter', 'Castryck' ),
    ( 'wh',  'Winston', 'Haaswijk' ),
    ( 'xt',  'Xifan', 'Tang' ),
    ( 'yx',  'Yinshui', 'Xia' ),
    ( 'zc',  'Zhufei', 'Chu' ),
    ( 'zs',  'Zahra', 'Sasanian' )
]

confpapers_data = [
    ( ['rw', 'dg', 'ms', 'rd'],                                         'isvlsi',   2008, 'Using higher levels of abstraction for solving optimization problems by Boolean satisfiability', '411--416', 'http://dx.doi.org/10.1109/ISVLSI.2008.82', [] ),
    ( ['ms', 'mk', 'rw', 'mg', 'rd'],                                   'date',     2010, 'Verifying UML/OCL models using Boolean satisfiability', '1341-1344', 'http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=5457017', [] ),
    ( ['ms', 'rw', 'gwd', 'rd'],                                        'ddecs',    2010, 'Window optimization of reversible and quantum circuits', '341--345', 'http://dx.doi.org/10.1109/DDECS.2010.5491754', [] ),
    ( ['rw', 'ms', 'rd'],                                               'dac',      2010, 'Reducing the number of lines in reversible circuits', '647--652', 'http://doi.acm.org/10.1145/1837274.1837439', [] ),
    ( ['ms', 'rw', 'rd'],                                               'idt',      2010, 'Hierarchical synthesis of reversible circuits using positive and negative davio decomposition', '143--148', 'http://dx.doi.org/10.1109/IDT.2010.5724427', [] ),
    ( ['ms', 'rw', 'rd'],                                               'date',     2011, 'Verifying dynamic aspects of UML models', '1077--1082', 'http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=5763177', [] ),
    ( ['ms', 'sf', 'rw', 'rd'],                                         'rc',       2011, 'RevKit: An open source toolkit for the design of reversible circuits', '65--76', 'http://dx.doi.org/10.1007/978-3-642-29517-1_6', [] ),
    ( ['rw', 'ms', 'dg', 'es', 'rd'],                                   'ismvl',    2011, 'Designing a RISC CPU in reversible logic', '170--175', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2011.39', [] ),
    ( ['ms', 'uk', 'mf', 'gf', 'rd'],                                   'ddecs',    2011, 'Automatic property generation for the formal verification of bus bridges', '417--422', 'http://dx.doi.org/10.1109/DDECS.2011.5783129', [] ),
    ( ['ms', 'rw', 'rd'],                                               'tap',      2011, 'Encoding OCL data types for SAT-based verification of UML/OCL models', '152--170', 'http://dx.doi.org/10.1007/978-3-642-21768-5_12', [] ),
    ( ['ms', 'rw', 'rd'],                                               'modevva',  2011, 'Towards automatic determination of problem bounds for object instantiation in static model verification', '2', 'http://dx.doi.org/10.1145/2095654.2095657', [] ),
    ( ['ms', 'rw', 'np', 'ch', 'rd'],                                   'aspdac',   2012, 'Synthesis of reversible circuits with minimal lines for large functions', '85--92', 'http://dx.doi.org/10.1109/ASPDAC.2012.6165069', [] ),
    ( ['rw', 'ms', 'rd'],                                               'date',     2012, 'Debugging of inconsistent UML/OCL models', '1078--1083', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=6176655', [] ),
    ( ['ms', 'rw', 'rd'],                                               'date',     2012, 'Eliminating invariants in UML/OCL models', '1142--1145', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=6176669', [] ),
    ( ['ms', 'rw', 'co', 'rd'],                                         'ismvl',    2012, 'A synthesis flow for sequential reversible circuits', '299--304', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2012.72', [] ),
    ( ['rw', 'ms', 'np', 'rd'],                                         'ismvl',    2012, 'Exact synthesis of Toffoli gate circuits with negative control lines', '69--74', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2012.71', [] ),
    ( ['ms', 'zs', 'rw', 'dmm', 'rd'],                                  'ismvl',    2012, 'Optimizing the mapping of reversible circuits to four-valued quantum gate circuits', '173--178', 'http://doi.ieeecomputersociety.org/10.1109/ISMVL.2012.64', [] ),
    ( ['ms', 'rw', 'rd'],                                               'tools',    2012, 'Assisted behavior driven development using natural language processing', '269--287', 'http://dx.doi.org/10.1007/978-3-642-30561-0_19', [] ),
    ( ['rw', 'ms', 'es', 'rd'],                                         'isvlsi',   2012, 'Circuit line minimization in the HDL-based synthesis of reversible logic', '213--218', 'http://dx.doi.org/10.1109/ISVLSI.2012.43', [] ),
    ( ['rd', 'ms', 'rw'],                                               'fdl',      2012, 'Formal Specification Level: Towards verification-driven design based on natural language processing', '53--58', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=6336984', [] ),
    ( ['rd', 'md', 'dg', 'uk', 'hml', 'js', 'ms', 'rw'],                'icgt',     2012, 'Completeness-Driven Development', '38--50', 'http://dx.doi.org/10.1007/978-3-642-33654-6_3', [] ),
    ( ['md', 'ms', 'dg', 'rd'],                                         'hldvt',    2012, 'Behavior driven development for circuit design and verification', '9--16', 'http://dx.doi.org/10.1109/HLDVT.2012.6418237', [] ),
    ( ['js', 'ms', 'rw', 'rd'],                                         'rc',       2012, 'Property checking of quantum circuits using quantum multiple-valued decision diagrams', '183--196', 'http://dx.doi.org/10.1007/978-3-642-36315-3_15', [] ),
    ( ['ms', 'rw', 'sim', 'rd'],                                        'rc',       2012, 'Using πDDs in the design for reversible circuits', '197--203', 'http://dx.doi.org/10.1007/978-3-642-36315-3_16', [] ),
    ( ['rw', 'ms', 'co', 'rd'],                                         'aspdac',   2013, 'Improving the mapping of reversible circuits to quantum circuits using multiple target lines', '145--150', 'http://dx.doi.org/10.1109/ASPDAC.2013.6509587', [] ),
    ( ['rw', 'mg', 'ms', 'mk', 'rd'],                                   'date',     2013, 'Towards a generic verification methodology for system models', '1193--1196', 'http://dl.acm.org/citation.cfm?id=2485575', [] ),
    ( ['js', 'rw', 'ms', 'rd'],                                         'date',     2013, 'Determining relevant model elements for the verification of UML/OCL specifications', '1189--1192', 'http://dl.acm.org/citation.cfm?id=2485574', [] ),
    ( ['na', 'ms', 'rw', 'rd'],                                         'ismvl',    2013, 'Exact template matching using Boolean satisfiability', '328--333', 'http://dx.doi.org/10.1109/ISMVL.2013.26', [] ),
    ( ['lt', 'ms', 'sim', 'rd'],                                        'ismvl',    2013, 'Debugging of reversible circuits using πDDs', '316--321', 'http://dx.doi.org/10.1109/ISMVL.2013.22', [] ),
    ( ['md', 'ms', 'dg', 'rd'],                                         'ast',      2013, 'Towards automatic scenario generation from coverage information', '82--88', 'http://dx.doi.org/10.1109/IWAST.2013.6595796', [] ),
    ( ['ms', 'rd', 'rxf'],                                              'dgk',      2013, 'Evaluation of site occupancy factors in crystal structure refinements using Boolean satisfiability techniques', '19', 'https://doi.org/10.1524/9783486858983.19', [] ),
    ( ['rd', 'ms'],                                                     'ddecs',    2013, 'Hardware-software co-visualization: Developing systems in the holodeck', '1--4', 'http://dx.doi.org/10.1109/DDECS.2013.6549775', [] ),
    ( ['na', 'rw', 'ms', 'rd'],                                         'rc',       2013, 'Reducing the depth of quantum circuits using additional lines', '221--233', 'http://dx.doi.org/10.1007/978-3-642-38986-3_18', [] ),
    ( ['ms', 'mkt'],                                                    'rc',       2013, 'White dots do matter: Rewriting reversible logic circuits', '196--208', 'http://dx.doi.org/10.1007/978-3-642-38986-3_16', [] ),
    ( ['ms', 'rd'],                                                     'idt',      2013, 'Grammar-based program generation based on model finding', '1--5', 'http://dx.doi.org/10.1109/IDT.2013.6727084', [] ),
    ( ['na', 'ms', 'rd'],                                               'rc',       2014, 'Quantum circuit optimization by Hadamard gate reduction', '149--162', 'http://dx.doi.org/10.1007/978-3-319-08494-7_12', [] ),
    ( ['dmm', 'ms', 'rd'],                                              'rc',       2014, 'Mapping NCV circuits to optimized Clifford+T circuits', '163--175', 'http://dx.doi.org/10.1007/978-3-319-08494-7_13', [] ),
    ( ['md', 'uk', 'ms', 'rd'],                                         'tap',      2014, 'Behaviour driven development for tests and verification', '61--77', 'http://dx.doi.org/10.1007/978-3-319-09099-3_5', [] ),
    ( ['rd', 'ms', 'rw'],                                               'iccad',    2014, 'Automated and quality-driven requirements engineering (invited tutorial)', '586--590', 'http://dx.doi.org/10.1109/ICCAD.2014.7001410', [] ),
    ( ['sw', 'cg', 'ms', 'kdt', 'rd'],                                  'apms',     2014, 'Requirements engineering for cyber-physical systems - challenges in the context of "Industrie 4.0"', '281--288', 'http://dx.doi.org/10.1007/978-3-662-44739-0_35', [] ),
    ( ['rd', 'hml', 'ms'],                                              'sbcci',    2014, 'Self-verification as the key technology for next generation electronic systems', '15:1--15:4', 'http://doi.acm.org/10.1145/2660540.2660983', [] ),
    ( ['ms', 'cbh', 'na', 'igh', 'rd'],                                 'fdl',      2014, 'Automating the translation of assertions using natural language processing techniques', '1--8', 'http://dx.doi.org/10.1109/FDL.2014.7119356', [] ),
    ( ['hr', 'ms', 'cw', 'gf', 'rd'],                                   'fdl',      2014, 'metaSMT: A unified interface to SMT-LIB2', '1--6', 'http://dx.doi.org/10.1109/FDL.2014.7119353', [] ),
    ( ['mmr', 'ms', 'gwd'],                                             'ismvl',    2015, 'Dynamic template matching with mixed-polarity Toffoli gates', '72--77', 'http://dx.doi.org/10.1109/ISMVL.2015.44', [] ),
    ( ['ms', 'ac'],                                                     'ismvl',    2015, 'Fredkin-enabled transformation-based reversible logic synthesis', '60--65', 'http://dx.doi.org/10.1109/ISMVL.2015.37', [] ),
    ( ['aaa', 'ms', 'rd'],                                              'ddecs',    2015, 'Sentence quality assessment based on natural language processing and artificial ingelligence', '183--188', 'http://dx.doi.org/10.1109/DDECS.2015.19', [] ),
    ( ['ss', 'ms', 'rd'],                                               'gecco',    2015, 'Multi-objective BDD optimization with evolutionary algorithms', '751--758', 'http://doi.acm.org/10.1145/2739480.2754718', [] ),
    ( ['ms', 'bs', 'rd', 'rkb'],                                        'fmcad',    2015, 'Reverse engineering with simulation graphs', '152--159', '', [] ),
    ( ['na', 'ms', 'rd'],                                               'rc',       2015, 'Technology mapping for quantum circuits using Boolean functional decomposition', '219--232', 'http://dx.doi.org/10.1007/978-3-319-20860-2_14', [] ),
    ( ['mkt', 'rkj', 'ms'],                                             'rc',       2015, 'Ricercar: A language for describing and rewriting reversible circuits with ancillae and its permutation semantics', '200--215', 'http://dx.doi.org/10.1007/978-3-319-20860-2_13', [] ),
    ( ['na', 'ms', 'gwd', 'rd'],                                        'vlsisoc',  2015, 'Reversible circuit rewriting with simulated annealing', '286--291', 'http://dx.doi.org/10.1109/VLSI-SoC.2015.7314431', [] ),
    ( ['ms', 'js', 'rd'],                                               'tap',      2015, 'Coverage of OCL operation specifications and invariants', '191--207', 'http://dx.doi.org/10.1007/978-3-319-21215-9_12', [] ),
    ( ['np', 'jp', 'ms', 'rw', 'rd'],                                   'modevva',  2015, 'Towards an automatic approach for restricting UML/OCL invariability clauses', '44--47', 'http://ceur-ws.org/Vol-1514/paper6.pdf', [] ),
    ( ['ms', 'dg', 'ac2', 'rd'],                                        'aspdac',   2016, 'BDD minimization for approximate computing', '474--479', 'http://dx.doi.org/10.1109/ASPDAC.2016.7428057', [] ),
    ( ['js2', 'df', 'ms', 'jpd', 'gg'],                                 'lascas',   2016, 'Dynamic NoC buffer allocation for MPSoC timing side channel attack protection', '91--94', 'http://dx.doi.org/10.1109/LASCAS.2016.7451017', [] ),
    ( ['asa', 'dg', 'uk', 'ms', 'rd'],                                  'date',     2016, 'Formal verification of integer multipliers by combining Gröbner basis with logic reduction', '1048--1053', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=7459464', [] ),
    ( ['ss', 'ms', 'peg', 'rd'],                                        'date',     2016, 'Fast logic synthesis for RRAM-based in-memory computing using majority-inverter graphs', '948--953', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=7459444', [] ),
    ( ['ms', 'la', 'peg', 'gdm'],                                       'date',     2016, 'Optimizing majority-inverter graphs with functional hashing', '1030--1035', 'http://ieeexplore.ieee.org/xpl/freeabs_all.jsp?arnumber=7459461', ['cirkit'] ),
    ( ['ss', 'ms', 'rd'],                                               'ddecs',    2016, 'Multi-objective BDD optimization for RRAM based circuit design', '46--15', 'http://dx.doi.org/10.1109/DDECS.2016.7482461, []'),
    ( ['ms', 'gwd', 'mmr', 'dmm'],                                      'iscas',    2016, 'An extension of transformation-based reversible and quantum circuit synthesis', '2290--2293', 'http://dx.doi.org/10.1109/ISCAS.2016.7539041', ['revkit'] ),
    ( ['ac', 'la', 'ms', 'peg', 'gdm'],                                 'ismvl',    2016, 'Notes on majority Boolean algebra', '50--55', 'https://doi.org/10.1109/ISMVL.2016.21', [] ),
    ( ['na', 'ma', 'ms', 'rd'],                                         'ismvl',    2016, 'Technology mapping of reversible circuits to Clifford+T quantum circuits', '150--155', 'https://doi.org/10.1109/ISMVL.2016.33', [] ),
    ( ['ac2', 'ms', 'dg', 'rd'],                                        'dac',      2016, 'Precise error determination of approximated components in sequential circuits with model checking', '129:1--129:6', 'http://doi.acm.org/10.1145/2897937.2898069', ['cirkit'] ),
    ( ['ms', 'ac'],                                                     'dac',      2016, 'Unlocking efficiency and scalability of reversible logic synthesis using conventional logic synthesis', '149:1--149:6', 'http://doi.acm.org/10.1145/2897937.2898107', ['revkit'] ),
    ( ['ms', 'ss', 'peg', 'la', 'rd', 'gdm'],                           'dac',      2016, 'An MIG-based compiler for programmable logic-in-memory architectures', '117:1--117:6', 'http://doi.acm.org/10.1145/2897937.2897985', ['cirkit'] ),
    ( ['ss', 'ms', 'dg', 'rd'],                                         'gecco',    2016, 'Approximate BDD optimization with prioritized ε-preferred evolutionary algorithm', '79--80', 'http://doi.acm.org/10.1145/2908961.2908987', [] ),
    ( ['ms', 'gwd', 'dmm'],                                             'rc',       2016, 'A fast symbolic transformation based algorithm for reversible logic synthesis', '307--321', 'http://dx.doi.org/10.1007/978-3-319-40578-0_22', ['revkit'] ),
    ( ['ms', 'na', 'gdm'],                                              'rc',       2016, 'Enumeration of reversible functions and its application to circuit complexity', '255--270', 'http://dx.doi.org/10.1007/978-3-319-40578-0_19', [] ),
    ( ['ms', 'am', 'ap', 'bs', 'pi', 'rkb', 'gdm'],                     'sat',      2016, 'Heuristic NPN classification for large functions using AIGs and LEXSAT', '212--227', 'http://dx.doi.org/10.1007/978-3-319-40970-2_14', ['cirkit'] ),
    ( ['et', 'ms', 'oz', 'la', 'pr2', 'rl', 'peg', 'gdm'],              'nanoarch', 2016, 'Inversion optimization in majority-inverter graphs', '15--20', 'http://dx.doi.org/10.1145/2950067.2950072', ['cirkit'] ),
    ( ['ac2', 'ms', 'dg', 'rd'],                                        'iccad',    2016, 'Approximation-aware rewriting of AIGs for error tolerant applications', '83', 'http://doi.acm.org/10.1145/2966986.2967003', ['cirkit'] ),
    ( ['ap', 'am', 'ms', 'gdm', 'rkb', 'pi'],                           'iccad',    2016, 'Fast generation of lexicographic satisfiable assignments: enabling canonicity in SAT-based applications', '4', 'http://doi.acm.org/10.1145/2966986.2967040', ['abc'] ),
    ( ['sr', 'igh', 'gf', 'ms'],                                        'iccad',    2016, 'Multilevel design understanding: from specification to logic (invited special session)', '133', 'http://doi.acm.org/10.1145/2966986.2980093', [] ),
    ( ['ap', 'ms', 'gdm', 'pi', 'am'],                                  'fpl',      2016, 'Fast hierarchical NPN classification', '1--4', 'http://dx.doi.org/10.1109/FPL.2016.7577306', ['abc'] ),
    ( ['asa', 'dg', 'ms', 'rd'],                                        'fmcad',    2016, 'Equivalence checking using Gröbner bases', '169--176', 'http://dx.doi.org/10.1109/FMCAD.2016.7886676', [] ),
    ( ['ms', 'pr', 'bs', 'bb', 'gdm', 'ms2'],                           'hvc',      2016, 'SAT-based combinational and sequential dependency computation', '1--17', 'http://dx.doi.org/10.1007/978-3-319-49052-6_1', ['cirkit'] ),
    ( ['wh', 'ms', 'la', 'peg', 'gdm'],                                 'aspdac',   2017, 'A novel basis for logic rewriting', '151--156', 'http://dx.doi.org/10.1109/ASPDAC.2017.7858312', ['cirkit'] ),
    ( ['la', 'ms', 'wh', 'et', 'pv', 'jl', 'peg', 'gdm'],               'aspdac',   2017, 'Multi-level logic benchmarks: An exactness study', '157--162', 'http://dx.doi.org/10.1109/ASPDAC.2017.7858313', [] ),
    ( ['ss', 'ms', 'peg', 'gdm', 'rd'],                                 'date',     2017, 'Endurance management for resistive logic-in-memory computing architectures', '1092-1097', 'https://doi.org/10.23919/DATE.2017.7927152', ['cirkit'] ),
    ( ['ms', 'gdm', 'am'],                                              'date',     2017, 'Busy Man\'s Synthesis: Combinational delay optimization with SAT', '830--835', 'https://doi.org/10.23919/DATE.2017.7927103', ['abc'] ),
    ( ['ms', 'mr', 'nw', 'gdm'],                                        'date',     2017, 'Design automation and design space exploration for quantum computers', '470--475', 'https://doi.org/10.23919/DATE.2017.7927035', ['revkit', 'abc'] ),
    ( ['oz', 'adm', 'et', 'ms', 'peg', 'gdm', 'la', 'pr2', 'fc', 'rl'], 'date',     2017, 'Wave pipelining for majority-based beyond-CMOS technologies (invited special session)', '1306--1311', 'https://doi.org/10.23919/DATE.2017.7927195', [] ),
    ( ['wh', 'et', 'ms', 'gdm'],                                        'ismvl',    2017, 'Classifying functions with exact synthesis', '272--277', 'https://doi.org/10.1109/ISMVL.2017.44', ['percy'] ),
    ( ['zc', 'xt', 'ms', 'ap', 'gz', 'la', 'yx', 'pi', 'gdm', 'peg'],   'glsvlsi',  2017, 'Improving circuit mapping performance through MIG-based synthesis for carry chains', '131--136', 'http://doi.acm.org/10.1145/3060403.3060432', ['cirkit'] ),
    ( ['ms', 'peg', 'gdm'],                                             'iscas',    2017, 'RM3 based logic synthesis', '1--4', 'https://doi.org/10.1109/ISCAS.2017.8050223', ['cirkit'] ),
    ( ['ms', 'mr', 'nw', 'gdm'],                                        'dac',      2017, 'Hierarchical reversible logic synthesis using LUTs', '78:1--78:6', 'http://doi.acm.org/10.1145/3061639.3062261', ['caterpillar', 'revkit'] ),
    ( ['ss', 'ms', 'dg', 'rd'],                                         'gecco',    2017, 'An adaptive prioritized ε-preferred evolutionary algorithm for approximate BDD optimization', '1232--1239', 'http://doi.acm.org/10.1145/3071178.3071281', [] ),
    ( ['et', 'oz', 'ms', 'av', 'mm2', 'rl', 'gdm'],                     'isvlsi',   2017, 'Inverter propagation and fan-out constraints for beyond-CMOS majority-based technologies', '164--169', 'https://doi.org/10.1109/ISVLSI.2017.37', ['cirkit'] ),
    ( ['la', 'ms', 'pv', 'jl', 'am', 'peg', 'jo', 'rkb', 'gdm'],        'iccad',    2017, 'Enabling exact delay synthesis',' 352--359', 'https://doi.org/10.1109/ICCAD.2017.8203799', [] ),
    ( ['zc', 'ms', 'yx', 'gdm'],                                        'aspdac',   2018, 'Functional decomposition using majority', '676--681', 'https://doi.org/10.1109/ASPDAC.2018.8297400', ['mockturtle'] ),
    ( ['gm', 'ms', 'mr', 'nw', 'gdm'],                                  'aspdac',   2018, 'A best-fit mapping algorithm to facilitate ESOP-decomposition in Clifford+T quantum network synthesis', '664--669', 'https://doi.org/10.1109/ASPDAC.2018.8297398', ['caterpillar'] ),
    ( ['la', 'ms', 'pv', 'jl', 'am', 'jo', 'rkb', 'gdm'],               'date',     2018, 'Improvements to Boolean resynthesis', '755--760', 'https://doi.org/10.23919/DATE.2018.8342108', [] ),
    ( ['ms', 'wh', 'et', 'am', 'la', 'rkb', 'gdm'],                     'date',     2018, 'Practical exact synthesis (invited executive session)', '309--314', 'https://doi.org/10.23919/DATE.2018.8342027', ['percy', 'abc'] ),
    ( ['ms', 'th', 'mr'],                                               'date',     2018, 'Programming quantum computers using design automation (invited executive session)', '137--146', 'https://doi.org/10.23919/DATE.2018.8341993', ['revkit'] ),
    ( ['wh', 'ec', 'bs2', 'ms', 'ss2', 'fk', 'gdm'],                    'iscas',    2018, 'Deep learning for logic optimization algorithms', '1--4', 'https://doi.org/10.1109/ISCAS.2018.8351885', [] ),
    ( ['wc', 'jd', 'adv', 'ok', 'ms'],                                  'ismvl',    2018, 'Translating between the roots of identity in quantum circuits', '254--259', 'https://doi.org/10.1109/ISMVL.2018.00051', [] ),
    ( ['dmm', 'ms'],                                                    'ismvl',    2018, 'A spectral algorithm for ternary function classification', '198--203', 'https://doi.org/10.1109/ISMVL.2018.00042', ['kitty'] ),
    ( ['am', 'rkb', 'ap', 'ms', 'la', 'ad'],                            'dac',      2018, 'Canonical computation without canonical representation', '52:1--52:6', 'http://doi.acm.org/10.1145/3195970.3196006', ['abc'] ),
    ( ['wh', 'am', 'ms', 'gdm'],                                        'dac',      2018, 'SAT based exact synthesis using DAG topology families', '53:1--53:6', 'http://doi.acm.org/10.1145/3195970.3196111', ['percy'] ),
    ( ['gm', 'ms', 'gdm'],                                              'rc',       2018, 'SAT-based {CNOT, T} quantum circuit synthesis', '175--188', 'https://doi.org/10.1007/978-3-319-99498-7_12', ['caterpillar'] ),
    ( ['th', 'ms', 'mr', 'kms'],                                        'rc',       2018, 'Quantum circuits for floating-point arithmetic', '162--174', 'https://doi.org/10.1007/978-3-319-99498-7_11', ['revkit'] ),
    ( ['hr', 'et', 'la', 'ms', 'gdm'],                                  'nanoarch', 2018, 'Size optimization of MIGs with an application to QCA and STMG technologies', '157--162', 'https://doi.org/10.1145/3232195.3232202', ['mockturtle'] ),
    ( ['la', 'et', 'mc', 'oz', 'gdm', 'ms'],                            'iccad',    2018, 'Majority logic synthesis (embedded tutorial)', '79', 'https://doi.org/10.1145/3240765.3267501', [] ),
    ( ['wh', 'la', 'jl', 'pv', 'ms', 'gdm'],                            'icecs',    2018, 'Integrated ESOP refactoring for industrial designs', '369-372', 'https://doi.org/10.1109/ICECS.2018.8617963', [] ),
    ( ['zc', 'ms', 'yx', 'lw'],                                         'aspdac',   2019, 'Structural rewriting in XOR-majority graphs', '663--668', 'https://doi.org/10.1145/3287624.3287671', ['mockturtle'] ),
    ( ['hr', 'wh', 'am', 'gdm', 'ms'],                                  'date',     2019, 'On-the-fly and DAG-aware: Rewriting Boolean networks with exact synthesis', '1649--1654', 'https://doi.org/10.23919/DATE.2019.8715185', ['mockturtle'] ),
    ( ['et', 'la', 'ms', 'am', 'pv', 'jl', 'cc', 'peg', 'gdm'],         'date',     2019, 'Scalable Boolean methods in a modern synthesis flow', '1643--1648', 'https://doi.org/10.23919/DATE.2019.8714776', [] ),
    ( ['gm', 'ms', 'mr', 'nb', 'gdm'],                                  'date',     2019, 'Reversible pebbling game for quantum memory management', '288--291', 'https://doi.org/10.23919/DATE.2019.8715092', ['caterpillar'] ),
    ( ['ms', 'fm', 'bs3', 'gdm'],                                       'date',     2019, 'Compiling permutations for superconducting QPUs', '1349--1354', 'https://doi.org/10.23919/DATE.2019.8715275', ['tweedledum'] ),
    ( ['zc', 'wh', 'ms', 'lw', 'yx', 'gdm'],                            'iscas',    2019, 'Exact synthesis of Boolean functions in majority-of-five forms', '1--5', 'https://doi.org/10.1109/ISCAS.2019.8702141', ['mockturtle'] ),
    ( ['db', 'ms', 'sd', 'ac', 'gdm'],                                  'ismvl',    2019, 'Reversible pebble games for reducing qubits in hierarchical quantum circuit synthesis', '102--107', 'https://doi.org/10.1109/ISMVL.2019.00026', ['revkit'] ),
    ( ['bs3', 'ms', 'am', 'gdm'],                                       'ismvl',    2019, 'Scaling-up ESOP synthesis for quantum compilation', '13--18', 'https://doi.org/10.1109/ISMVL.2019.00011', ['abc'] ),
    ( ['hr', 'et', 'wh', 'am', 'la', 'gdm', 'ms'],                      'dac',      2019, 'Scalable generic logic synthesis: one approach to rule them all', '70', 'https://doi.org/10.1145/3316781.3317905', ['mockturtle'] ),
    ( ['et', 'ms', 'la', 'gdm'],                                        'dac',      2019, 'Reducing the multiplicative complexity in logic networks for cryptography and security applications', '74', 'https://doi.org/10.1145/3316781.3317893', ['mockturtle'] ),
    ( ['gm', 'ms', 'mr', 'gdm'],                                        'qpl',      2019, 'ROS: Resource-constrained oracle synthesis for quantum computers', 'XXXX', '', ['caterpillar'] ),
    ( ['ks', 'ms', 'bs3', 'gdm', 'mt'],                                 'qpl',      2019, 'Using ZDDs in the mapping of quantum circuits', 'XXXX', '', ['tweedledum'] ),
    ( ['gm', 'ms', 'ec2', 'mr', 'gdm'],                                 'iccad',    2019, 'The role of multiplicative complexity in compiling low T-count oracle circuits', '1--8', 'https://doi.org/10.1109/ICCAD45719.2019.8942093', ['caterpillar'] ),
    ( ['ms', 'et', 'dmm'],                                              'pacrim',   2019, 'A hybrid spectral method for checking Boolean function equivalence', '1--6', 'https://doi.org/10.1109/PACRIM47961.2019.8985048', [] ),
    ( ['et', 'ms', 'hr', 'la', 'gdm'],                                  'date',     2020, 'A logic synthesis toolbox for reducing the multiplicative complexity in logic networks', '568-573', 'https://doi.org/10.23919/DATE48585.2020.9116467', ['mockturtle'] ),
    ( ['hr', 'ms', 'am'],                                               'date',     2020, 'Exact DAG-aware rewriting', '732-737', 'https://doi.org/10.23919/DATE48585.2020.9116379', ['mockturtle'] ),
    ( ['et', 'sln', 'oz', 'ms', 'fc', 'an', 'gdm'],                     'date',     2020, 'Multiplier architectures: challenges and opportunities with plasmonic-based logic (special session)', '133-138', 'https://doi.org/10.23919/DATE48585.2020.9116490', [] ),
    ( ['th', 'sj', 'mn2', 'mr', 'ms'],                                  'pqcrypto', 2020, 'Improved quantum circuits for elliptic curve discrete logarithms', '425--444', 'https://doi.org/10.1007/978-3-030-44223-1_23', [] ),
    ( ['fm', 'ms', 'hr', 'gdm'],                                        'ismvl',    2020, 'Automatic uniform quantum state preparation using decision diagrams', '170-175', 'https://doi.org/10.1109/ISMVL49045.2020.00-10', ['angel'] ),
    ( ['bs3', 'ms', 'gdm'],                                             'ismvl',    2020, 'Symbolic algorithms for token swapping', '28-33', 'https://doi.org/10.1109/ISMVL49045.2020.00-34', ['tweedledum', 'easy'] ),
    ( ['gm', 'ms', 'mr', 'gdm'],                                        'iscas',    2020, 'Enumerating optimal quantum circuits using spectral classification', '1-5', 'https://doi.org/10.1109/ISCAS45731.2020.9180792', ['caterpillar']),
    ( ['ms', 'mr'],                                                     'qce',      2020, 'Quantum circuits for functionally controlled NOT gates', '366-371', 'https://doi.org/10.1109/QCE49297.2020.00052', []),
    ( ['gm', 'ms', 'mr', 'th'],                                         'oopsla',   2020, 'Enabling Accuracy-Aware Quantum Compilers using Symbolic Resource Estimation', '130:1-130:26', 'https://doi.org/10.1145/3428198', [] )
]

workpapers_data = [
    ( ['ms', 'rw', 'mk', 'mg', 'rd'],                'mbmv',       2010, 'Verifying UML/OCL models using Boolean satisfiability', '57--66', '', [] ),
    ( ['ms', 'rw', 'rd'],                            'rcw',        2010, 'Hierachical synthesis of reversible circuits using positive and negative Davio decomposition', '55--58', '', [] ),
    ( ['ms', 'sf', 'rw', 'rd'],                      'rcw',        2010, 'RevKit: A toolkit for reversible circuit design', '69-72', '', [] ),
    ( ['ms', 'uk', 'mf', 'gf', 'rd'],                'mbmv',       2011, 'Towards automatic property generation for the formal verification of bus bridges', '183--192', '', [] ),
    ( ['rw', 'ms', 'dg', 'es', 'rd'],                'mbmv',       2011, 'Designing a RISC CPU in reversible logic', '249--258', '', [] ),
    ( ['ms', 'sf', 'rw', 'rd'],                      'rcw',        2011, 'Customized design flows for reversible circuits using RevKit', '91--96', '', [] ),
    ( ['ms', 'rw', 'np', 'ch', 'rd'],                'rcw',        2011, 'Synthesis of reversible circuits with minimal lines for large functions', '59--70', '', [] ),
    ( ['ms', 'rw', 'lt', 'dmm', 'rd'],               'iwsbp',      2012, 'Towards embedding of large functions for reversible logic', 'XXXX', '', [] ),
    ( ['ms', 'hr', 'rw', 'gf', 'rd'],                'mecoes',     2012, 'Verification of embedded systems using modeling and implementation languages', '67--72', '', [] ),
    ( ['ms', 'rw', 'ek', 'rd'],                      'mbmv',       2013, 'Generierung von OCL-Ausdrücken aus natürlichsprachlichen Beschreibungen', '99-103', '', [] ),
    ( ['ok', 'ms', 'ek', 'rd'],                      'naturalise', 2013, 'lips: An IDE for model driven engineering based on natural language processing', 'XXXX', '', [] ),
    ( ['rd', 'hml', 'ms', 'rw'],                     'sec',        2013, 'Law-based verification of complex swarm systems', 'XXXX', '', [] ),
    ( ['ms', 'mn', 'rd'],                            'mbmv',       2014, 'Formale Methoden für Alle', '213--216', '', [] ),
    ( ['js', 'mm', 'ms', 'rw', 'rd'],                'duhde',      2014, 'Towards a multi-dimensional and dynamic visualization for ESL designs', 'XXXX', '', [] ),
    ( ['ms', 'na', 'rd'],                            'iwsbp',      2014, 'A framework for reversible circuit complexity', 'XXXX', '', [] ),
    ( ['rd', 'js', 'ms'],                            'difts',      2014, 'Coverage at the formal specification level', 'XXXX', '', [] ),
    ( ['ms', 'mkt', 'gwd', 'dmm'],                   'rm',         2015, 'Self-inverse functions and palindromic circuits', 'XXXX', '', [] ),
    ( ['bs', 'ms', 'rd', 'rkb'],                     'iwls',       2015, 'Simulation graphs for reverse engineering', 'XXXX', '', ['cirkit'] ),
    ( ['ac2', 'dg', 'ms', 'rd'],                     'mbmv',       2016, 'Symbolic error metric determination for approximate computing', '75--76', '', ['cirkit'] ),
    ( ['ap', 'am', 'ms', 'gdm', 'rkb', 'pi'],        'iwls',       2016, 'Fast generation of lexicographic satisfiable assignments: enabling canonicity in SAT-based applications', 'XXXX', '', ['abc'] ),
    ( ['et', 'ms', 'la', 'peg', 'gdm'],              'iwls',       2016, 'Inversion minimization in majority-inverter graphs', 'XXXX', '', ['cirkit'] ),
    ( ['ms', 'pr', 'bs', 'ms2'],                     'iwls',       2016, 'SAT-based functional dependency computation', 'XXXX', '', ['cirkit'] ),
    ( ['wh', 'ms', 'la', 'peg', 'gdm'],              'iwls',       2016, 'LUT mapping and optimization for majority-inverter graphs', 'XXXX', '', [] ),
    ( ['ok', 'ms', 'rd'],                            'iwsbp',      2016, 'On the computational complexity of error metrics in approximate computing', 'XXXX', '', [] ),
    ( ['ms', 'ik', 'gdm'],                           'rm',         2017, 'Boolean function classification with δ-swaps', 'XXXX', '', [] ),
    ( ['bs', 'ms', 'gdm', 'rkb'],                    'iwls',       2017, 'Cut generation for reverse engineering of gate-level netlists', 'XXXX', '', ['cirkit'] ),
    ( ['gm', 'ms', 'peg', 'gdm'],                    'iwls',       2017, 'A compiler for parallel and resource-constrained programmable in-memory computing', 'XXXX', '', ['cirkit'] ),
    ( ['am', 'rkb', 'ap', 'ms'],                     'iwls',       2017, 'SAT-based optimization with don\'t-cares revisited', 'XXXX', '', ['abc'] ),
    ( ['et', 'ms', 'oz', 'fc', 'gdm'],               'iwls',       2017, 'Exact synthesis for logic synthesis applications with complex constraints', 'XXXX', '', ['cirkit'] ),
    ( ['zc', 'ms', 'yx', 'gdm'],                     'iwls',       2017, 'Functional decomposition using majority', 'XXXX', '', ['cirkit'] ),
    ( ['wh', 'ec', 'bs2', 'ms', 'ss2', 'fk', 'gdm'], 'iwls',       2017, 'Deep learning for logic optimization', 'XXXX', '', [] ),
    ( ['mc', 'el', 'pm', 'rp', 'ms'],                'dice',       2018, 'Normal form systems generated by single connectives have mutually equivalent efficiency', 'XXXX', '', [] ),
    ( ['zc', 'ms', 'yx', 'lw'],                      'iwls',       2018, 'Structural rewriting in XOR-majority graphs', 'XXXX', '', ['cirkit'] ),
    ( ['gm', 'ms', 'mr', 'dmm', 'ma', 'nw', 'gdm'],  'iwls',       2018, 'Estimating single-target gate T-count using spectral classification', 'XXXX', '', ['revkit'] ),
    ( ['ms', 'hr', 'wh', 'gdm'],                     'iwls',       2018, 'The EPFL logic synthesis libraries', 'XXXX', '', ['alice', 'kitty', 'percy', 'easy'] ),
    ( ['ms', 'hr', 'wh', 'et', 'gdm'],               'woset',      2018, 'The EPFL logic synthesis libraries', 'XXXX', '', ['alice', 'kitty', 'percy', 'easy', 'mockturtle', 'tweedledum'] ),
    ( ['ms', 'et', 'dmm'],                           'rm',         2019, 'A hybrid spectral method for checking Boolean function equivalence', 'XXXX', '', [] ),
    ( ['et', 'wh', 'ms', 'gdm'],                     'iwls',       2019, 'The complexity of self-dual monotone 7-input functions', 'XXXX', '', ['kitty', 'percy'] ),
    ( ['gm', 'ms', 'mr', 'gdm'],                     'iwls',       2019, 'ROS: Resource constrained oracle synthesis for quantum computers', 'XXXX', '', ['caterpillar'] ),
    ( ['fm', 'ms', 'gdm'],                           'iwls',       2019, 'Automatic rreparation of uniform quantum states utilizing Boolean functions', 'XXXX', '', ['tweedledum'] ),
    ( ['ms'],                                        'iwls',       2020, 'Determining the multiplicative complexity of Boolean functions using SAT', 'XXXX', '', ['mockturtle'] )
]

article_data = [
    ( ['ms', 'sf', 'rw', 'rd'],                            'mvl',          18,  "1",      2012, 'RevKit: A toolkit for reversible circuit design',                                                                                        '55--65',        'http://www.oldcitypublishing.com/MVLSC/MVLSCabstracts/MVLSC18.1abstracts/MVLSCv18n1p55-65Soeken.html', ['revkit'] ),
    ( ['rw', 'ms', 'np', 'rd'],                            'mvl',          21,  "5--6",   2013, 'Effect of negative control lines on the exact synthesis of reversible circuits',                                                         '627--640',      'http://www.oldcitypublishing.com/MVLSC/MVLSCabstracts/MVLSC21.5-6abstracts/MVLSCv21n5-6p627-640Wille.html', ['revkit'] ),
    ( ['ms', 'dmm', 'rd'],                                 'pra',          88,  "042322", 2013, 'Quantum circuits employing roots of the Pauli matrices',                                                                                 '042322',        'http://dx.doi.org/10.1103/PhysRevA.88.042322', [] ),
    ( ['rw', 'ms', 'dmm', 'rd'],                           'integration',  47,  "2",      2014, 'Trading off circuit lines and gate costs in the synthesis of reversible logic',                                                          '284--294',      'http://dx.doi.org/10.1016/j.vlsi.2013.08.002', ['revkit'] ),
    ( ['na', 'ms', 'mkt', 'rd'],                           'ipl',         114,  "6",      2014, 'Upper bounds for reversible circuits based on Young subgroups',                                                                          '282--286',      'http://dx.doi.org/10.1016/j.ipl.2014.01.003', [] ),
    ( ['eg', 'ms'],                                        'sosym',        14,  "2",      2015, 'Specification-driven model transformation testing',                                                                                      '623--644',      'http://dx.doi.org/10.1007/s10270-013-0369-x', [] ),
    ( ['ms', 'rw', 'ok', 'dmm', 'rd'],                     'jetc',         12,  "4",      2015, 'Embedding of large Boolean functions for reversible logic',                                                                              '41',            'http://dx.doi.org/10.1145/2786982', ['revkit'] ),
    ( ['ms', 'lt', 'gwd', 'rd'],                           'jsc',          73,  "",       2016, 'Ancilla-free synthesis of large reversible functions using binary decision diagrams',                                                    '1--26',         'http://dx.doi.org/10.1016/j.jsc.2015.03.002', ['revkit'] ),
    ( ['rw', 'es', 'ms', 'rd'],                            'integration',  53,  "",       2016, 'SyReC: A hardware description language for the specification and synthesis of reversible circuits',                                      '39--53',        'http://dx.doi.org/10.1016/j.vlsi.2015.10.001', [] ),
    ( ['ms', 'rd', 'rxf'],                                 'zk',          231,  "2",      2016, 'Atomic distributions in crystal structures solved by Boolean satisfiability techniques',                                                 '107--111',      'http://dx.doi.org/10.1515/zkri-2015-1887', [] ),
    ( ['na', 'ma', 'rd', 'ms'],                            'tcs',         618,  "",       2016, 'Complexity of reversible circuits and their quantum implementations',                                                                    '85--106',       'http://dx.doi.org/10.1016/j.tcs.2016.01.011', [] ),
    ( ['cr', 'ss', 'ms', 'nr', 'tw', 'rd', 'lm'],          'cnf',         168,  "",       2016, 'Time-resolved detection of diffusion limited temperature gradients inside single isolated burning droplets using rainbow refractometry', '255-269',       'http://dx.doi.org/10.1016/j.combustflame.2016.03.007', [] ),
    ( ['np', 'ms', 'rw', 'rd'],                            'cps',           1,  "1",      2016, 'Verifying the structure and behavior in UML/OCL models using satisfiability solvers',                                                    '49--59',        'http://digital-library.theiet.org/content/journals/10.1049/iet-cps.2016.0022', [] ),
    ( ['ms', 'peg', 'ss', 'rd', 'gdm'],                    'computer',     50,  "6",      2017, 'A PLiM computer for the Internet of Things',                                                                                             '35--40',        'https://doi.org/10.1109/MC.2017.173', ['cirkit'] ),
    ( ['hr', 'fh', 'sf', 'ms', 'dg', 'rd', 'gf'],          'sttt',         19,  "5",      2017, 'metaSMT: Focus on your application and not on solver integration',                                                                       '605--621',      'http://link.springer.com/article/10.1007/s10009-016-0426-1', [] ),
    ( ['ms', 'la', 'peg', 'gdm'],                          'tcad',         36,  "11",     2017, 'Exact synthesis of majority-inverter graphs and its applications',                                                                       '1842--1855',    'https://doi.org/10.1109/TCAD.2017.2664059', ['cirkit'] ),
    ( ['ss', 'ms', 'peg', 'rd'],                           'tcad',         37,  "7",      2018, 'Logic synthesis for RRAM-based in-memory computing',                                                                                     '1937-4151',     'https://doi.org/10.1109/TCAD.2017.2750064', ['cirkit'] ),
    ( ['ok', 'ms', 'rd'],                                  'ipl',         139,  "",       2018, 'The complexity of error metric',                                                                                                         '1--7',          'https://doi.org/10.1016/j.ipl.2018.06.010', [] ),
    ( ['ms', 'et', 'am', 'gdm'],                           'ipl',         139,  "",       2018, 'Pairs of majority-decomposing functions',                                                                                                '35-38',         'https://doi.org/10.1016/j.ipl.2018.07.004', [] ),
    ( ['et', 'ms', 'la', 'gdm'],                           'procieee',    107,  "1",      2019, 'Logic synthesis for established and emerging computing',                                                                                 '1558--2256',    'https://doi.org/10.1109/JPROC.2018.2869760', [] ),
    ( ['et', 'ms', 'la', 'wh', 'gdm'],                     'tc',           68,  "5",      2019, 'Mapping monotone Boolean functions into majority',                                                                                       '791--797',      'https://doi.org/10.1109/TC.2018.2881245', [] ),
    ( ['ms', 'mr', 'nw', 'gdm'],                           'tcad',         38,  "9",      2019, 'LUT-based hierarchical reversible logic synthesis',                                                                                      '1675--1688',    'https://doi.org/10.1109/TCAD.2018.2859251', ['caterpillar', 'revkit'] ),
    ( ['ms', 'gm', 'bs3', 'fm', 'hr', 'gdm'],              'rsta',        378,  "2164",   2020, 'Boolean satisfiability in quantum compilation',                                                                                          '',              'http://dx.doi.org/10.1098/rsta.2019.0161', ['tweedledum', 'caterpillar'] ),
    ( ['wh', 'ms', 'am', 'gdm'],                           'tcad',         39,  "4",      2020, 'SAT-based exact synthesis: encodings, topology families, and parallelism',                                                               '871--884',      'https://doi.org/10.1109/TCAD.2019.2897703', ['percy'] ),
    ( ['zc', 'ms', 'yx', 'lw', 'gdm'],                     'tcad',         39,  "8",      2020, 'Advanced functional decomposition using majority and its applications',                                                                  '1621-1634',     'https://doi.org/10.1109/TCAD.2019.2925392', [] ),
    ( ['dmm', 'ms'],                                       'mvl',          34,  "3-4",    2020, 'A spectral algorithm for 3-valued function equivalence classification',                                                                  '203-221',       'https://www.oldcitypublishing.com/journals/mvlsc-home/mvlsc-issue-contents/mvlsc-volume-34-number-3-4-2020/mvlsc-34-3-4-p-203-221/', [] ),
    ( ['bh', 'ms', 'sm', 'cg2', 'mr', 'ag', 'mt2', 'kms'], 'nrp',           2,  "",       2020, 'Quantum programming languages',                                                                                                          '709-722',       'https://doi.org/10.1038/s42254-020-00245-7', [] ),
    ( ['et', 'la', 'ms', 'am', 'pv', 'peg', 'gdm'],        'access',        8,  "",       2020, 'Extending Boolean methods for scalable logic synthesis',                                                                                 '226828-226844', 'https://doi.org/10.1109/ACCESS.2020.3045014', ['mockturtle']),
    ( ['dm', 'et', 'hr', 'am', 'ms', 'gdm'],               'tcad',         40,  "10",     2021, 'Three-input gates for logic synthesis',                                                                                                  '2184-2188',     'https://doi.org/10.1109/TCAD.2020.3032625', ['mockturtle'] ),
    ( ['fm', 'hr', 'ms', 'gdm'],                           'tqe',           2,  "",       2021, 'Efficient Boolean methods for preparing uniform quantum states',                                                                         '3103112',       'https://doi.org/10.1109/TQE.2021.3101663', ['angel'] ),
    ( ['gm', 'ms', 'gdm'],                                 'npjqi',         8,  "",       2022, 'Xor-And-Inverter graphs for quantum compilation',                                                                                        '7',             'https://doi.org/10.1038/s41534-021-00514-y', ['caterpillar'] ),
    ( ['th', 'ms'],                                        'tqc',           3,  "2",      2022, 'Lowering the T-depth of quantum circuits via logic network optimization',                                                                '6',             'https://doi.org/10.1145/3501334', ['mockturtle'])
]

preprint_data = [
    ( ['ms', 'dmm', 'rd'],              '1308.2493',  'On quantum circuits employing roots of the Pauli matrices',                                       '7 pages, 1 figure',                                                                                    'j3',   ['quant-ph', 'cs.ET'] ),
    ( ['ms', 'na', 'rd'],               '1407.5878',  'A framework for reversible circuit complexity',                                                   "6 pages, 4 figures, accepted for Int'l Workshop on Boolean Problems 2014",                             '',     ['cs.ET', 'quant-ph'] ),
    ( ['ms', 'rw', 'ok', 'dmm', 'rd'],  '1408.3586',  'Embedding of large Boolean functions for reversible logic',                                       '13 pages, 10 figures',                                                                                 'j7',   ['cs.ET'] ),
    ( ['ms', 'lt', 'gwd', 'rd'],        '1408.3955',  'Ancilla-free synthesis of large reversible functions using binary decision diagrams',             '25 pages, 15 figures',                                                                                 'j8',   ['cs.ET', 'quant-ph'] ),
    ( ['ms', 'mkt', 'gwd', 'dmm'],      '1502.05825', 'Self-inverse functions and palindromic circuits',                                                 '6 pages, 3 figures',                                                                                   '',     ['cs.ET', 'math.GR', 'quant-ph'] ),
    ( ['wc', 'jd', 'adv', 'ok', 'ms'],  '1503.08579', 'Translating between the roots of identity in quantum circuits',                                   '7 pages',                                                                                              '',     ['quant-ph', 'math.GR'] ),
    ( ['ms', 'mr', 'nw', 'gdm'],        '1612.00631', 'Design automation and design space exploration for quantum computers',                            '6 pages, 1 figure',                                                                                    'c81',  ['quant-ph', 'cs.ET'] ),
    ( ['ms', 'mr', 'nw', 'gdm'],        '1706.02721', 'Logic synthesis for quantum computing',                                                           '15 pages, 10 figures',                                                                                 '',     ['quant-ph', 'cs.ET'] ),
    ( ['ms', 'th', 'mr'],               '1803.01022', 'Programming quantum computers using design automation',                                           '10 pages, 10 figures',                                                                                 'c94',  ['quant-ph', 'cs.ET'] ),
    ( ['ms', 'hr', 'wh', 'gdm'],        '1805.05121', 'The EPFL logic synthesis libraries',                                                              "8 pages, accepted at Int'l Workshop on Logic & Synthesis 2018",                                        '',     ['cs.LO', 'cs.MS'] ),
    ( ['th', 'ms', 'mr', 'kms'],        '1807.02023', 'Quantum circuits for floating-point arithmetic',                                                  '13 pages, 2 tables, 6 figures. To appear in: Proc. Reversible Computation (RC 2018)',                  'c101', ['quant-ph', 'cs.ET'] ),
    ( ['ks', 'ms', 'bs3', 'gdm', 'mt'], '1901.02406', 'Using ZDDs in the mapping of quantum circuits',                                                   '13 pages, accepted at QPL 2019',                                                                       'c116', ['quant-ph', 'cs.ET'] ),
    ( ['gm', 'ms', 'mr', 'nb', 'gdm'],  '1904.02121', 'Reversible pebbling game for quantum memory management',                                          'In Proc. Design Automation and Test in Europe (DATE 2019)',                                            'c111', ['quant-ph', 'cs.ET'] ),
    ( ['gm', 'ms', 'ec2', 'mr', 'gdm'], '1908.01609', 'The role of multiplicative complexity in compiling low T-count oracle circuits',                  "13 pages, 2 tables, 6 figures, To appear in: Proc. Int'l Conf. on Computer-Aided Design (ICCAD 2019)", 'c117', ['quant-ph', 'cs.ET'] ),
    ( ['th', 'sj', 'mn2', 'mr', 'ms'],  '2001.09580', 'Improved quantum circuits for elliptic curve discrete logarithms',                                "22 pages, to appear in: Int'l Conf. on Post-Quantum Cryptography (PQCrypto 2020)",                     'c120', ['quant-ph', 'cs.ET'] ),
    ( ['gm', 'ms', 'mr', 'th'],         '2003.08408', 'Automatic accuracy management of quantum programs via (near-)symbolic resource estimation',       '15 pages',                                                                                             'c127', ['quant-ph', 'cs.ET', 'cs.PL'] ),
    ( ['gm', 'ms', 'mr', 'gdm'],        '2005.00211', 'ROS: resource-constrained oracle synthesis for quantum computers',                                'In Proceedings QPL 2019, arXiv:2004.14750',                                                            'c115', ['cs.ET', 'cs.LO', 'quant-ph'] ),
    ( ['ms'],                           '2005.01778', 'Determining the multiplicative complexity of Boolean functions using SAT',                        '8 pages, 2 tables, comments welcome',                                                                  '',     ['cs.DS', 'cs.LO', 'quant-ph'] ),
    ( ['ms', 'mr'],                     '2005.12310', 'Quantum circuits for functionally controlled NOT gates',                                          '6 pages, 7 figures',                                                                                   'c126', ['quant-ph', 'cs.ET'] ),
    ( ['th', 'ms'],                     '2006.03845', 'Lowering the T-depth of quantum circuits by reducing the multiplicative depth of logic networks', '8 pages, 3 figures',                                                                                   'j32',  ['quant-ph', 'cs.CR', 'cs.ET'] ),
    ( ['th', 'ms'],                     '2201.10200', 'The multiplicative complexity of interval checking',                                              '7 pages',                                                                                              '',     ['quant-ph', 'cs.CR', 'cs.LO'] )
]

best_paper_data = [ ( '2016_date_1', 'c' ), ( '2016_sat', 'c' ) ]

news_data = []

authors = make_dict( 'key', authors_data, make_author )
conferences = make_dict( 'key', conferences_data, make_conference )
journals = make_dict( 'key', journals_data, make_journal )

confpapers = list( map( make_conference_paper, confpapers_data ) )
workpapers = list( map( make_conference_paper, workpapers_data ) )
articles = list( map( make_article, article_data ) )
preprints = list( map( make_preprint, preprint_data ) )

news = list( map( make_news, news_data ) )

universities_data = [
    ( 'birs',    'Banff International Research Station', 'Banff, AL',        'Canada',      'http://www.birs.ca',                                   '' ),
    ( 'epfl',    'EPFL',                                 'Lausanne',         'Switzerland', 'http://epfl.ch',                                       'École Polytechnique Fédérale de Lausanne' ),
    ( 'hu',      'Hokkaido University',                  'Sapporo',          'Japan',       'https://www.oia.hokudai.ac.jp',                        '北海道大学' ),
    ( 'ibm',     'IBM Research',                         'Yorktown Heights', 'USA',         'https://www.research.ibm.com/labs/watson/index.shtml', '' ),
    ( 'rwth',    'RWTH Aachen University',               'Aachen',           'Germany',     'http://www.rwth-aachen.de',                            'RWTH Aachen' ),
    ( 'ru',      'Ritsumeikan University',               'Kyoto',            'Japan',       'http://en.ritsumei.ac.jp',                             '立命館大学' ),
    ( 'sri',     'SRI International',                    'Menlo Park, CA',   'USA',         'https://www.sri.com',                                  '' ),
    ( 'su',      'Stanford University',                  'Stanford, CA',     'USA',         'http://stanford.edu',                                  '' ),
    ( 'unb',     'University of New Brunswick',          'Fredericton, NB',  'Canada',      'http://www.unb.ca',                                    '' ),
    ( 'msr',     'Microsoft Research',                   'Redmond, WA',      'USA',         'https://www.microsoft.com/en-us/research/',            '' ),
    ( 'rigetti', 'Rigetti Computing',                    'Berkeley, CA',     'USA',         'https://www.rigetti.com/',                             '' ),
    ( 'snps',    'Synopsys',                             'Sunnyvale, CA',    'USA',         'http://www.synopsys.com/',                             '' ),
    ( 'unistra', 'University of Strasbourg',             'Strasbourg',       'France',      'https://en.unistra.fr/',                               '' )
]

universities = make_dict( 'key', universities_data, make_university )

invited_data = [
    ( 2011, 'jan', 'uni',  'hu',      'Prof. Shin-ichi Minato',                    'Formal verification of UML-based specifications',                         'http://www-erato.ist.hokudai.ac.jp/wiki/wiki.cgi?page=ERATO-seminar' ),
    ( 2012, 'apr', 'conf', 'cukeup',  '',                                          'BDD for embedded system design',                                          'https://skillsmatter.com/skillscasts/3124-bdd-for-embedded-system-design' ),
    ( 2013, 'jan', 'uni',  'hu',      'Prof. Shin-ichi Minato',                    'Synthesis of reversible circuits with minimal lines for large functions', '' ),
    ( 2013, 'apr', 'conf', 'cukeup',  '',                                          'Towards automatic scenario generation based on uncovered code',           'https://skillsmatter.com/skillscasts/4043-towards-automatic-scenario-generation-based-on-uncovered-code' ),
    ( 2014, 'apr', 'uni',  'su',      'Prof. Subhasish Mitra',                     'Formal specification level',                                              '' ),
    ( 2014, '',    'uni',  'rwth',    'Prof. Anupam Chattopadhyay',                'Implementing synthesis flows with RevKit',                                '' ),
    ( 2014, 'may', 'uni',  'ru',      'Prof. Shigeru Yamashita',                   'Formal specification level',                                              '' ),
    ( 2014, 'oct', 'uni',  'unb',     'Prof. Gerhard W. Dueck',                    'Formal specification level',                                              'http://www.cs.unb.ca/seminarseries/documents/Mathias_Soeken-10.29.14.pdf' ),
    ( 2014, 'dec', 'uni',  'sri',     'Dr. Wenchao Li',                            'Reverse engineering',                                                     '' ),
    ( 2015, 'may', 'conf', 'rm',      '',                                          'Generalized equivalence checking problems for reverse engineering',       'http://lyle.smu.edu/RM2015/program.htm' ),
    ( 2015, 'jun', 'uni',  'epfl',    'Prof. Paolo Ienne',                         'Reverse engineering with simulation graphs',                              '' ),
    ( 2016, 'apr', 'uni',  'birs',    'Dr. Martin Roetteler',                      'Ancilla-free reversible logic synthesis using symbolic methods',          'http://www.birs.ca/events/2016/5-day-workshops/16w5029/videos/watch/201604181552-Soeken.html' ),
    ( 2016, 'may', 'uni',  'hu',      'Prof. Shin-ichi Minato',                    'Ancilla-free reversible logic synthesis using symbolic methods',          'http://www-erato.ist.hokudai.ac.jp/html/php/seminar.php?day=20160517' ),
    ( 2016, 'sep', 'uni',  'msr',     'Dr. Martin Roetteler and Dr. Nathan Wiebe', 'Symbolic and hierarchical reversible logic synthesis',                    '' ),
    ( 2016, 'nov', 'uni',  'snps',    'Dr. Luca Amarù',                            'SAT-based logic synthesis',                                               '' ),
    ( 2017, 'feb', 'uni',  'msr',     'Dr. Martin Roetteler and Dr. Nathan Wiebe', 'LUT-based hierarchical reversible logic synthesis',                       '' ),
    ( 2017, 'jul', 'conf', 'rcss',    '',                                          'Reversible logic synthesis and RevKit',                                   'http://reversible-computation.org/2017/images/Program-RC2017.pdf' ),
    ( 2017, 'aug', 'conf', 'costts',  '',                                          'Hierarchical reversible logic synthesis',                                 'http://www.informatik.uni-bremen.de/ictcost/school2017.php?program' ),
    ( 2018, 'jan', 'uni',  'unistra', 'Dr. Morgan Madec',                          'Introduction to Quantum Computing and Reversible Logic',                  '' ),
    ( 2018, 'feb', 'uni',  'ibm',     'Dr. Mihir Choudhury',                       'Logic Synthesis for Quantum Computing',                                   '' ),
    ( 2018, 'feb', 'uni',  'rigetti', 'Dr. Will Zeng',                             'Logic Synthesis in Automatic Quantum Compilation',                        '' ),
    ( 2018, 'feb', 'uni',  'msr',     'Dr. Martin Roetteler',                      'Automatically Compiling Combinational Operations in Q#',                  '' )
]

invited = list( map( make_invited, invited_data ) )

def cmd_publications():
    for key, conf in conferences.items():
        if len( conf['shortname'] ) > 0:
            print( "@STRING{%s = {%s}}" % ( conf['shortname'], conf['name'] ) )
    print()

    print( "@book{book1," )
    print( "  editor    = {Rolf Drechsler and Mathias Soeken and Robert Wille}," )
    print( "  title     = {Auf dem Weg zum Quantencomputer: Entwurf reversibler Logik (Technische Informatik)}," )
    print( "  publisher = {Shaker}," )
    print( "  year      = 2012" )
    print( "}" )
    print()
    print( "@book{book2," )
    print( "  author    = {Mathias Soeken and Rolf Drechsler}," )
    print( "  title     = {Formal Specification Level}," )
    print( "  publisher = {Springer}," )
    print( "  year      = 2014" )
    print( "}" )
    print()
    print( "@book{book3," )
    print( "  editor    = {Rolf Drechsler and Mathias Soeken}," )
    print( "  title     = {Advanced Boolean Techniques: Selected Papers from the 13th International Workshop on Boolean Problems}," )
    print( "  publisher = {Springer}," )
    print( "  year      = 2019" )
    print( "}" )
    print()
    print( "@incollection{inc1," )
    print( "  author    = {Rolf Drechsler and Mathias Soeken and Robert Wille}," )
    print( "  title     = {Formal specification level}," )
    print( "  editor    = {Jan Haase}," )
    print( "  booktitle = {Models, Methods, and Tools for Complex Chip Design: Selected Contributions from FDL 2012}," )
    print( "  publisher = {Springer}," )
    print( "  year      = 2014" )
    print( "}" )
    print()
    print( "@incollection{inc2," )
    print( "  author    = {Mathias Soeken}," )
    print( "  title     = {Formale {Spezifikationsebene}}," )
    print( "  editor    = {S. H{\\\"o}lldobler and others}," )
    print( "  booktitle = {Ausgezeichnete Informatikdissertationen 2013}," )
    print( "  publisher = {GI}," )
    print( "  year      = 2014" )
    print( "}" )
    print()
    print( "@incollection{inc3," )
    print( "  author    = {Mathias Soeken and Nabila Abdessaied and Rolf Drechsler}," )
    print( "  title     = {A framework for reversible circuit complexity}," )
    print( "  editor    = {Bernd Steinbach}," )
    print( "  booktitle = {Problems and New Solutions in the Boolean Domain}," )
    print( "  publisher = {Cambridge Scholars Publishing}," )
    print( "  pages     = {327--341}," )
    print( "  year      = 2016" )
    print( "}" )
    print()

    for a in articles:
        format_bibtex_article( a )
        print()

    for c in confpapers:
        format_bibtex_incollection( c, confpapers, "conference" )
        print()

    for w in workpapers:
        format_bibtex_incollection( w, workpapers, "workshop" )

    for p in preprints:
        format_bibtex_preprint( p )

    write_publications()

def cmd_haml():
    year = ""
    for index, c in enumerate( reversed( confpapers ) ):
        if c['year'] != year:
            year = c['year']
            print( "%%h4 %s" % year )
        format_haml_incollection( c, len( confpapers ) - index )

def cmd_haml_work():
    print( "%p These workshop papers are peer-reviewed and have been presented at events, where the proceedings where distributed only among the participants.  If you are interested in one of the listed papers, please send me an eMail and I am happy to share the PDF." )
    year = ""
    for index, c in enumerate( reversed( workpapers ) ):
        if c['year'] != year:
            year = c['year']
            print( "%%h4 %s" % year )
        format_haml_incollection_work( c, len( workpapers ) - index )

def cmd_haml_article():
    year = ""
    for index, c in enumerate( reversed( articles ) ):
        if c['year'] != year:
            year = c['year']
            print( "%%h4 %s" % ( "In press" if year == 0 else year ) )
        format_haml_article( c, len( articles ) - index )

def cmd_haml_preprint():
    for index, c in enumerate( reversed( preprints ) ):
        format_haml_preprint( c, len( preprints ) - index )

def cmd_haml_news():
    for n in reversed( news ):
        format_haml_news( n )

def cmd_haml_invited():
    year = ""
    for n in reversed( invited ):
        if n['year'] != year:
            year = n['year']
            print( "%%h4 %s" % year )
        format_haml_invited( n )

def cmd_stats():
    num_countries = len( set( [p['conf']['venues'][p['year']]['country'] for p in confpapers] ) )
    print( "%d authors, %d conference papers, in %d countries" % ( len( authors ), len( confpapers ), num_countries ) )

def cmd_pdfs():
    for c in confpapers:
        filename = make_filename( c, confpapers )

        if os.path.exists( "papers/%s.pdf" % filename ):
            if not os.path.exists( "images/thumbs/%s.png" % filename ):
                print( "[i] creating thumbnail for \"%s\" (%s %d)" % ( c['title'], c['conf']['shortname'], c['year'] ) )
                os.system( "convert papers/%s.pdf /tmp/%s.png" % ( filename, filename ) )
                os.system( "convert -trim -resize x130 /tmp/%s-0.png images/thumbs/%s.png" % ( filename, filename ) )
        else:
            print( "[w] no PDF for \"%s\" (%s %d)" % ( c['title'], c['conf']['shortname'], c['year'] ) )

def cmd_geo():
    from geopy.geocoders import Nominatim
    locator = Nominatim()
    for k1, d in conferences.items():
        for k2, v in d['venues'].items():
            location = "%s, %s" % (v['city'], v['country'])
            l = locator.geocode( location )
            if l:
                print( "  {title: '%s', position: {lat: %s, lng: %s}}," % (location, l.latitude, l.longitude) )
            else:
                print( "No geocode for %s" % v )

if len( sys.argv ) == 2:
    globals()['cmd_%s' % sys.argv[1]]()
