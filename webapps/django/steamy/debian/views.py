from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.utils.encoding import smart_str

from debian.forms import SPARQLForm, SearchForm
from debian.services import SPARQLQueryProcessor, SPARQLQueryBuilder
from debian.errors import SPARQLQueryProcessorError


def index(request):
    searchform = SearchForm()
    sparqlform = SPARQLForm()
    dict = {'search': searchform, 'sparql': sparqlform}
    return render_to_response('debian/search.html', dict)

def sparql(request):
    if request.method == 'POST':
        sparqlform = SPARQLForm(request.POST)
        
        if sparqlform.is_valid() is False:
            searchform = SearchForm()
            dict = {'search': searchform, 'sparql': sparqlform}
            return render_to_response('debian/search.html', dict)

        query = sparqlform.cleaned_data['ns'] + sparqlform.cleaned_data['query']
        processor = SPARQLQueryProcessor()
        try:
            processor.execute_query(smart_str(query))
        except SPARQLQueryProcessorError, e:
            return render_to_response('debian/error.html', {'reason': e.reason})

        (variables, results) = processor.format_sparql_results()
        dict = {'variables': variables, 'results': results}
        return render_to_response('debian/results.html', dict)
    else:
        return HttpResponse("405 - Method not allowed", status=405)

def results(request):
    if request.method == 'POST':
        searchform = SearchForm(request.POST)

        if searchform.is_valid() is False:
            sparqlform = SPARQLForm()
            dict = {'search': searchform, 'sparql': sparqlform}
            return render_to_response('debian/search.html', dict)
        
        data = searchform.cleaned_data
        builder = SPARQLQueryBuilder(data)
        processor = SPARQLQueryProcessor()
        query = builder.create_query()

        try:
            processor.execute_sanitized_query(query)
        except SPARQLQueryProcessorError, e:
            return render_to_response('debian/error.html', {'reason': e.reason})

        if builder.source_search:
            results = processor.format_source_results()
        elif builder.binary_search:
            results = processor.format_binary_results()
        else:
            raise Exception()

        replydata = {'results': results, 'filter': data['filter']}
        replydata['query'] = query if data['showquery'] else None
        replydata['show_popcon'] = True if data['popcon'] else False

        if builder.source_search:
            return render_to_response('debian/source_results.html', replydata)
        else:
            return render_to_response('debian/binary_results.html', replydata)
    else:
        return HttpResponse("405 - Method not allowed", status=405)
