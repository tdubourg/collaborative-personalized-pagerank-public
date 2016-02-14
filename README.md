collaborative-personalized-pagerank
===================================

Master Thesis on Building a Collaborative-Filtering techniques-based Personalized PageRank.

Please note that this project is only aimed at running on Linux-based systems. 

Dependencies are the following:

- ElasticSearch
- Python 2.7.x
- Graph-Tool Python library
- Scrapy Python library
- `chardet`, `elasticsearch`, `pymongo`  and `bs4` Python modules
- Bash
- ZSH
- Multimarkdown (if you want to recompile the `CPPR.md` file in `report/`)


Description of folders:

- `algolia` contains an attempt to use Algolia.com service as a search engine backend, did not work.
- `elastic_search` contains the configuration of ElasticSearch together with its launching scripts.
- `frontend` contains the user study platform
- `logs-processing` contains all scripts related to processing the logs: Usage extraction, user similarity, etc.
- `logs-processing/logs-enrichment` contains the scripts related to adding the missing data to the logs.
- `ppr-java` contains the test code to use JUNG to compute PageRank, reading from a GraphML file.
- `ppr` contains all scripts related to computing PageRank and Personalized PageRank.
- `presentation` contains files integrated in the final presentation and the defense presentation (exported from GDocs format).
- `report` contains the Master Thesis (Masterarbeit) written work source code, together with its dependency files (images, latex input files).
- `scripts` contains misc scripts, mainly setup scripts. Shorthands to do procedures like installing Privoxy and Tor in a docker.
- `user_study` contains results of the user study results (JSON sessions) together with the script necessary to generate the measures/metrics results from the raw user study results.
- `versionned_data` contains versionned "data", results and binaries (spreadsheets) that needed to be versionned for safety and to be able to follow their changes.
- `web_crawler` contains the web crawler.`

The current folder, EXCEPT THE FOLDER `logs-processing/logs-enrichment`, is under the LGPLv3 license.
The folder `logs-processing/logs-enrichment` is not to be redistributed without express consent of its author.
