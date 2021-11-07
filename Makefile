haml:
	/usr/local/opt/python@3.8/bin/python3 ./publications.py haml > _conferences.haml
	/usr/local/opt/python@3.8/bin/python3 ./publications.py haml_article > _journals.haml
	/usr/local/opt/python@3.8/bin/python3 ./publications.py haml_preprint > _preprints.haml
	/usr/local/opt/python@3.8/bin/python3 ./publications.py haml_work > _workshops.haml
	/usr/local/opt/python@3.8/bin/python3 ./publications.py haml_news > _news.haml

%.html : %.haml
	/usr/local/lib/ruby/gems/3.0.0/bin/haml $< > $@

html_files := $(wildcard *.html)

all: haml benchmarks.html blog.html blog_qac.html cirkit.html cirkit_doc.html cirkit_examples.html cirkit_new_addon.html index.html iwqc17.html iwqc18.html iwqc19.html library.html ls-dict.html publications.html quantum.html reciprocal.html research.html revclass.html revclass_viewer.html revkit.html revkit_new_command.html talks.html teaching.html tutorials.html iwls20.html

clean:
	rm *.html
