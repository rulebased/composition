TEMPLATES=\
	cds \
	genericpart \
	inducible_promoter \
	promoter \
	rbs \
	terminator \
	transcription_elongation \
	transcription_termination \
	translation_chain \
	translation_elongation \
	translation_termination

all: test

test:
	@make test_turtle_syntax

test_turtle_syntax:
	@echo "*** CHECKING TURTLE SYNTAX ***"
	@for template in ${TEMPLATES}; do \
		make $$template.ttl || exit 1; \
	done

%.ttl: %.kappa
	< $< grep '^#\^' | sed 's/^#\^ //' > $@.tmp
	rapper -q -i turtle -o turtle $@.tmp $@ > $@ && rm $@.tmp

clean:
	rm -f *.tmp
	rm -f *.ttl
