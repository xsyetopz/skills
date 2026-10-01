# Search and identity

Each index has its own coverage and native query syntax; none is complete. Use native queries, not
one keyword string everywhere.

- **arXiv**: preprints. Field syntax such as `all:"tail sampling"`; ask for at least 3 seconds
  between requests ([arXiv API][arxiv]).
- **Crossref**: publisher DOI metadata with `filter=` parameters, for example `filter=updates:DOI`
  for corrections and retractions. Its polite pool takes a `mailto` only if the user supplied one
  ([Crossref REST][crossref]).
- **OpenAlex**: works and citations with filters such as `from_publication_date:2020-01-01`; an API
  key is optional ([OpenAlex][openalex]).

Commands are POSIX sh; on Windows run them in Git Bash or WSL, or in PowerShell type `curl.exe` and
drop the `\` continuations. Write a phrase already encoded, as `%22tail+sampling%22` below: Windows
PowerShell 5.1 strips double quotes inside a native command's argument, which silently turns the
phrase into separate words.

```sh
curl -sG 'https://export.arxiv.org/api/query' \
  -d 'search_query=all:%22tail+sampling%22' -d max_results=3
curl -s 'https://api.openalex.org/works?search=tail+sampling&per-page=8'
curl -sG 'https://api.crossref.org/works' \
  --data-urlencode 'filter=updates:10.1016/S0140-6736(97)11096-0'
```

For that DOI the Crossref lookup returns two notices, a correction and a retraction; a summary that
misses them cites a retracted paper.

Record provider, exact query, date, and filters for every search, including the disconfirming one
(synonyms of the first query do not count). Never match papers on title alone.

[arxiv]: https://info.arxiv.org/help/api/user-manual.html
[crossref]: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
[openalex]: https://docs.openalex.org/
