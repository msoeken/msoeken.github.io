haml:
	./publications.py haml > _conferences.haml
	./publications.py haml_article > _journals.haml
	./publications.py haml_preprint > _preprints.haml
	./publications.py haml_news > _news.haml

%.html : %.haml
	/usr/local/opt/ruby/bin/ruby /usr/local/lib/ruby/gems/2.6.0/gems/haml-5.1.2/bin/haml $< > $@

html_files := $(wildcard *.html)

all: haml benchmarks.html blog.html blog_qac.html cirkit.html cirkit_doc.html cirkit_examples.html cirkit_new_addon.html index.html iwqc17.html iwqc18.html iwqc19.html library.html ls-dict.html publications.html quantum.html reciprocal.html research.html revclass.html revclass_viewer.html revkit.html revkit_new_command.html talks.html teaching.html tutorials.html

clean:
	rm *.html
